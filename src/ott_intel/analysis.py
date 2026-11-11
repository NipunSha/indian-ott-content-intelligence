"""Statistical analysis for the OTT observatory. All functions take the titles DataFrame.

`views_d0_27` (English-Wikipedia pageviews in the 28 days from release) is the public-attention
proxy. It is not viewership and is biased towards English-reading audiences."""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from .http import ROOT

PROC = ROOT / "data" / "processed"
CAT = ["platform", "primary_language", "primary_genre", "format"]
NUM_A = ["is_franchise_or_sequel", "is_adaptation", "log_cast_prom", "cast_missing", "company_prior_titles"]
TRAIN_END_YEAR = 2023


def load():
    t = pd.read_csv(PROC / "titles.csv")
    t["log_views"] = np.log10(t.views_d0_27.where(t.views_d0_27 > 0))
    t["cast_missing"] = t.cast_prom_max.isna().astype(int)
    t["log_cast_prom"] = np.log10(t.cast_prom_max.fillna(0) + 1)
    t["log_pre_views"] = np.log10(t.views_pre_30d.fillna(0) + 1)
    for c in ("is_franchise_or_sequel", "is_adaptation", "scripted", "page_live_at_release"):
        t[c] = t[c].astype(int)
    return t


def sample(t):
    """Analysis sample: scripted titles whose Wikipedia page existed on release day."""
    return t[(t.scripted == 1) & (t.page_live_at_release == 1) & t.log_views.notna()].copy()


def coverage(t):
    s = t[t.scripted == 1]
    f = lambda col: s.groupby(col).agg(titles=("title_id", "size"), measurable=("page_live_at_release", "sum"), share_measurable=("page_live_at_release", "mean")).reset_index().rename(columns={col: "level"}).assign(dimension=col)
    return pd.concat([f("platform"), f("primary_language"), f("format"), f("release_year")])


def group_stats(s, col, min_n=8):
    g = s.groupby(col).views_d0_27.agg(titles="size", median_views="median", p25=lambda x: x.quantile(.25), p75=lambda x: x.quantile(.75), top_decile_share=lambda x: (x >= s.views_d0_27.quantile(.9)).mean()).reset_index()
    g = g[g.titles >= min_n].rename(columns={col: "level"}).assign(dimension=col)
    groups = [x.log_views.values for _, x in s.groupby(col) if len(x) >= min_n]
    h, p = stats.kruskal(*groups) if len(groups) > 1 else (np.nan, np.nan)
    return g.assign(kruskal_h=h, kruskal_p=p)


def lump(s, col, min_n=15, other="Other"):
    vc = s[col].value_counts()
    return s[col].where(s[col].map(vc) >= min_n, other)


def ols(s):
    d = s.copy()
    for c in ("platform", "primary_language", "primary_genre"):
        d[c] = lump(d, c)
    m = smf.ols("log_views ~ C(platform, Treatment('Netflix')) + C(primary_language, Treatment('Hindi')) + C(primary_genre, Treatment('Drama')) + C(format) + is_franchise_or_sequel + is_adaptation + log_cast_prom + cast_missing + C(release_year)", data=d).fit(cov_type="HC3")
    ci = m.conf_int()
    out = pd.DataFrame({"term": m.params.index, "coef_log10": m.params.values, "ci_low": ci[0].values, "ci_high": ci[1].values, "p_value": m.pvalues.values})
    out["multiplier"] = 10 ** out.coef_log10; out["mult_low"] = 10 ** out.ci_low; out["mult_high"] = 10 ** out.ci_high
    out["n"] = int(m.nobs); out["r2"] = m.rsquared; out["adj_r2"] = m.rsquared_adj
    return out, m


def _pipe(kind, num):
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=10), CAT), ("num", StandardScaler(), num)])
    est = LogisticRegression(max_iter=2000, C=1.0) if kind == "logit" else GradientBoostingClassifier(n_estimators=150, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=0)
    return Pipeline([("pre", pre), ("est", est)])


def predict(s, seed=0, n_boot=1000):
    """Temporal hold-out: train on releases up to 2023, test on 2024 onwards. The benchmark
    ('strong launch') is the 75th percentile of launch views in the TRAINING period only."""
    tr, te = s[s.release_year <= TRAIN_END_YEAR], s[s.release_year > TRAIN_END_YEAR]
    thr = tr.views_d0_27.quantile(0.75)
    ytr, yte = (tr.views_d0_27 >= thr).astype(int), (te.views_d0_27 >= thr).astype(int)
    rng = np.random.default_rng(seed)
    rows, fitted = [], {}
    for stage, num in [("greenlight", NUM_A), ("launch_eve", NUM_A + ["log_pre_views"])]:
        for kind in ("logit", "gbm"):
            p = _pipe(kind, num).fit(tr[CAT + num], ytr)
            pr = p.predict_proba(te[CAT + num])[:, 1]
            boots = []
            for _ in range(n_boot):
                i = rng.integers(0, len(te), len(te))
                if yte.values[i].min() != yte.values[i].max(): boots.append(roc_auc_score(yte.values[i], pr[i]))
            k = max(1, int(round(len(te) * 0.2)))
            top = np.argsort(-pr)[:k]
            rows.append({"stage": stage, "model": kind, "n_train": len(tr), "n_test": len(te), "threshold_views": thr, "train_prevalence": ytr.mean(), "test_prevalence": yte.mean(),
                         "roc_auc": roc_auc_score(yte, pr), "auc_ci_low": np.quantile(boots, .025), "auc_ci_high": np.quantile(boots, .975),
                         "pr_auc": average_precision_score(yte, pr), "brier": brier_score_loss(yte, pr), "brier_baseline": brier_score_loss(yte, np.full(len(yte), ytr.mean())),
                         "precision_top20pct": yte.values[top].mean()})
            fitted[(stage, kind)] = (p, num, pr)
    return pd.DataFrame(rows), fitted, (tr, te, ytr, yte, thr)


def importance(fitted, split, stage, kind, seed=0):
    p, num, _ = fitted[(stage, kind)]
    tr, te, ytr, yte, thr = split
    r = permutation_importance(p, te[CAT + num], yte, scoring="roc_auc", n_repeats=30, random_state=seed)
    return pd.DataFrame({"stage": stage, "model": kind, "feature": CAT + num, "auc_drop_mean": r.importances_mean, "auc_drop_sd": r.importances_std}).sort_values("auc_drop_mean", ascending=False)


def opportunity_cells(s, since=2023, min_n=5, n_boot=2000, seed=0):
    """Language x genre cells since `since`: supply share inside the language versus demand index
    (cell median launch views / language median). Bootstrap CI on the index."""
    d = s[s.release_year >= since]
    rng = np.random.default_rng(seed)
    rows = []
    for lang, L in d.groupby("primary_language"):
        if len(L) < 15: continue
        for genre, C in L.groupby("primary_genre"):
            if len(C) < min_n: continue
            rest = L[L.primary_genre != genre].views_d0_27.values
            cell = C.views_d0_27.values
            idx = np.median(cell) / np.median(L.views_d0_27)
            b = []
            for _ in range(n_boot):
                cb, rb = rng.choice(cell, len(cell)), (rng.choice(rest, len(rest)) if len(rest) else rest)
                b.append(np.median(cb) / np.median(np.concatenate([cb, rb])))
            u, p = stats.mannwhitneyu(cell, rest, alternative="two-sided") if len(rest) >= 5 else (np.nan, np.nan)
            rows.append({"primary_language": lang, "primary_genre": genre, "titles": len(C), "language_titles": len(L), "supply_share": len(C) / len(L),
                         "median_views": np.median(cell), "language_median_views": np.median(L.views_d0_27), "demand_index": idx,
                         "index_ci_low": np.quantile(b, .025), "index_ci_high": np.quantile(b, .975), "mannwhitney_p": p, "platforms_active": C.platform.nunique()})
    out = pd.DataFrame(rows)
    out["flag"] = np.where((out.demand_index >= 1.25) & (out.index_ci_low > 1) & (out.supply_share <= 0.15), "under-supplied relative to attention",
                  np.where((out.demand_index <= 0.8) & (out.index_ci_high < 1) & (out.supply_share >= 0.15), "over-supplied relative to attention", ""))
    return out.sort_values("demand_index", ascending=False)


def yearly(s):
    y = s.groupby(["release_year", "primary_genre"]).agg(titles=("title_id", "size"), median_views=("views_d0_27", "median")).reset_index()
    y["share_of_year"] = y.titles / y.groupby("release_year").titles.transform("sum")
    return y


def proxy_validation(s):
    """Does the proxy move with independent demand signals? Uses local-only restricted sources;
    only the correlation statistics are published."""
    r = pd.read_csv(PROC / "restricted" / "titles_restricted_sources.csv")
    d = s.merge(r[["title_id", "numVotes", "averageRating", "netflix_in_weeks_top10"]], on="title_id", how="left")
    rows = []
    v = d[d.numVotes.notna()]
    rho, p = stats.spearmanr(v.views_d0_27, v.numVotes)
    rows.append({"check": "launch views vs IMDb vote count (all platforms)", "n": len(v), "spearman_rho": rho, "p_value": p})
    rho, p = stats.spearmanr(v.views_d0_27, v.averageRating)
    rows.append({"check": "launch views vs IMDb average rating (attention is not quality)", "n": len(v), "spearman_rho": rho, "p_value": p})
    n = d[(d.platform == "Netflix") & d.netflix_in_weeks_top10.notna() & (d.release_date >= "2021-07-04")]
    if len(n) >= 10:
        rho, p = stats.spearmanr(n.views_d0_27, n.netflix_in_weeks_top10)
        rows.append({"check": "launch views vs weeks in Netflix India Top 10 (Netflix titles released from Jul 2021)", "n": len(n), "spearman_rho": rho, "p_value": p})
        ch = n.assign(charted=n.netflix_in_weeks_top10 > 0)
        if ch.charted.nunique() == 2:
            u, p = stats.mannwhitneyu(ch[ch.charted].views_d0_27, ch[~ch.charted].views_d0_27)
            rows.append({"check": f"median launch views: charted {ch[ch.charted].views_d0_27.median():.0f} vs not charted {ch[~ch.charted].views_d0_27.median():.0f} (Mann-Whitney)", "n": len(ch), "spearman_rho": np.nan, "p_value": p})
    return pd.DataFrame(rows)


def baselines(s):
    """How much of the greenlight model is just platform identity?"""
    tr, te = s[s.release_year <= TRAIN_END_YEAR], s[s.release_year > TRAIN_END_YEAR]
    thr = tr.views_d0_27.quantile(0.75)
    ytr, yte = (tr.views_d0_27 >= thr).astype(int), (te.views_d0_27 >= thr).astype(int)
    rows = [{"check": "platform base rates only", "n_test": len(te), "positives": int(yte.sum()),
             "roc_auc": roc_auc_score(yte, te.platform.map(ytr.groupby(tr.platform).mean()).fillna(ytr.mean()))}]
    cat = [c for c in CAT if c != "platform"]
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=10), cat), ("num", StandardScaler(), NUM_A)])
    p = Pipeline([("pre", pre), ("est", LogisticRegression(max_iter=2000))]).fit(tr[cat + NUM_A], ytr)
    rows.append({"check": "greenlight logit without platform", "n_test": len(te), "positives": int(yte.sum()), "roc_auc": roc_auc_score(yte, p.predict_proba(te[cat + NUM_A])[:, 1])})
    full = _pipe("logit", NUM_A).fit(tr[CAT + NUM_A], ytr)
    pr = full.predict_proba(te[CAT + NUM_A])[:, 1]
    rows.append({"check": "greenlight logit, all features", "n_test": len(te), "positives": int(yte.sum()), "roc_auc": roc_auc_score(yte, pr)})
    for pl in te.platform.unique():
        m = (te.platform == pl).values
        if m.sum() >= 20 and yte[m].nunique() == 2:
            rows.append({"check": f"greenlight logit, within {pl} only", "n_test": int(m.sum()), "positives": int(yte[m].sum()), "roc_auc": roc_auc_score(yte[m], pr[m])})
    return pd.DataFrame(rows)


def language_format(s, min_n=8):
    g = s.groupby(["primary_language", "format"]).agg(titles=("title_id", "size"), median_views=("views_d0_27", "median"), median_sustain=("sustain_ratio", "median")).reset_index()
    return g[g.titles >= min_n]


def crime_thriller_premium(s, min_n=8):
    rows = []
    for lang, g in s.groupby("primary_language"):
        ct = g.primary_genre.isin(["Crime", "Thriller"])
        if ct.sum() >= min_n and (~ct).sum() >= min_n:
            u, p = stats.mannwhitneyu(g[ct].views_d0_27, g[~ct].views_d0_27)
            rows.append({"primary_language": lang, "crime_thriller_titles": int(ct.sum()), "crime_thriller_median": g[ct].views_d0_27.median(),
                         "other_titles": int((~ct).sum()), "other_median": g[~ct].views_d0_27.median(), "ratio": g[ct].views_d0_27.median() / g[~ct].views_d0_27.median(), "mannwhitney_p": p})
    return pd.DataFrame(rows)


def headline_numbers(s):
    pre_share = (s.views_pre_30d / (s.views_pre_30d + s.views_d0_27)).median()
    rho, p = stats.spearmanr(s.log_pre_views, s.log_views)
    fr = s.groupby("is_franchise_or_sequel").views_d0_27.agg(["size", "median"])
    return {"median_launch_views": float(s.views_d0_27.median()), "p90_launch_views": float(s.views_d0_27.quantile(.9)), "top10pct_share_of_views": float(s.nlargest(int(len(s) * .1), "views_d0_27").views_d0_27.sum() / s.views_d0_27.sum()),
            "median_pre_release_share": float(pre_share), "spearman_pre_vs_launch": float(rho), "median_sustain_ratio": float(s.sustain_ratio.median()),
            "franchise_n": int(fr.loc[1, "size"]), "franchise_median": float(fr.loc[1, "median"]), "non_franchise_median": float(fr.loc[0, "median"]),
            "log10_views_sd": float(s.log_views.std())}
