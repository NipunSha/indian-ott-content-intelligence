"""Step 6: assemble the analysis dataset (one row per title) from staged titles + pageviews
(+ locally held IMDb and Netflix files, which are never written to the publishable outputs)."""
import json, gzip, re
from datetime import date, timedelta
import numpy as np
import pandas as pd
from .http import ROOT

RAW, PROC = ROOT / "data" / "raw", ROOT / "data" / "processed"
START, CUTOFF = date(2018, 1, 1), date(2026, 11, 8)
RETRIEVED = "2026-11-11"
MAJOR_LANGS = ["Hindi", "Tamil", "Telugu", "Malayalam", "Kannada", "Bengali", "Marathi", "English"]


def primary_language(s):
    langs = [l for l in str(s).split("; ") if l and l != "nan"]
    non_en = [l for l in langs if l != "English"]
    l = (non_en or langs or ["Unknown"])[0]
    return l if l in MAJOR_LANGS else ("Other Indian" if l != "Unknown" else "Unknown")


def window_sum(d, rel, lo, hi):
    return sum(d.get((rel + timedelta(days=k)).strftime("%Y%m%d"), 0) for k in range(lo, hi + 1))


def cast_prominence(cast_list, rel, redirects, monthly):
    """Mean monthly pageviews of each top-3 billed cast member over the 12 full months before the
    release month. Returns (max, mean, n_found). Uses only pre-release months -> no leakage."""
    vals = []
    first = date(rel.year, rel.month, 1)
    months = []
    y, m = first.year, first.month
    for _ in range(12):
        m -= 1
        if m == 0: y, m = y - 1, 12
        months.append(f"{y}{m:02d}01")
    for c in [c for c in str(cast_list).split("; ")[:3] if c and c != "nan"]:
        person = redirects.get(c)
        if person and person in monthly:
            vals.append(np.mean([monthly[person].get(k, 0) for k in months]))
    return (max(vals), float(np.mean(vals)), len(vals)) if vals else (np.nan, np.nan, 0)


def main():
    t = pd.read_csv(PROC / "titles_stage.csv")
    t = t[t.is_indian & t.is_title_page & t.release_date.notna()].copy()
    t["rel"] = pd.to_datetime(t.release_date).dt.date
    t = t[(t.rel >= START) & (t.rel <= CUTOFF - timedelta(days=27))].reset_index(drop=True)
    daily = json.load(open(RAW / "pageviews_titles_daily.json"))
    redirects = json.load(open(RAW / "cast_redirects.json"))
    monthly = json.load(open(RAW / "pageviews_cast_monthly.json"))

    recs = []
    for r in t.itertuples():
        d = daily.get(r.wiki_title, {})
        first_obs = min(d) if d else None
        rel_key = r.rel.strftime("%Y%m%d")
        live = bool(d) and first_obs <= rel_key and window_sum(d, r.rel, 0, 27) > 0
        full90 = r.rel + timedelta(days=89) <= CUTOFF
        cmax, cmean, cn = cast_prominence(r.cast_list, r.rel, redirects, monthly)
        recs.append({
            "page_live_at_release": live, "first_pageview_date": first_obs,
            "views_pre_30d": window_sum(d, r.rel, -30, -1) if live else np.nan,
            "views_d0_6": window_sum(d, r.rel, 0, 6) if live else np.nan,
            "views_d0_27": window_sum(d, r.rel, 0, 27) if live else np.nan,
            "views_d28_89": window_sum(d, r.rel, 28, 89) if (live and full90) else np.nan,
            "cast_prom_max": cmax, "cast_prom_mean": cmean, "cast_n_matched": cn,
        })
    t = pd.concat([t, pd.DataFrame(recs)], axis=1)
    t["sustain_ratio"] = t.views_d28_89 / t.views_d0_27
    t["primary_language"] = t.languages.map(primary_language)
    t["primary_genre"] = t.genres.fillna("").map(lambda s: s.split("; ")[0] if s else "Unknown")
    # Titles with no recoverable genre are not assumed to be scripted.
    t["scripted"] = ~t.primary_genre.isin(["Documentary", "Unscripted", "Animation", "Unknown"])
    t["release_year"] = pd.to_datetime(t.release_date).dt.year
    t["release_month"] = pd.to_datetime(t.release_date).dt.month
    t["title_id"] = ["T%04d" % i for i in range(1, len(t) + 1)]
    t["lead_company"] = t.production_companies.fillna("").map(lambda s: s.split("; ")[0] if s else "")
    # production-house track record: number of earlier titles in this dataset from the same lead company
    t = t.sort_values(["rel", "wiki_title"], kind="stable").reset_index(drop=True)
    t["company_prior_titles"] = t.groupby("lead_company").cumcount().where(t.lead_company != "", 0)

    # ---- restricted, local-only sources -------------------------------------------------
    restricted = t[["title_id", "wiki_title", "imdb_id", "platform"]].copy()
    with gzip.open(RAW / "imdb_title_ratings.tsv.gz", "rt") as f:
        imdb = pd.read_csv(f, sep="\t")
    restricted = restricted.merge(imdb, left_on="imdb_id", right_on="tconst", how="left").drop(columns="tconst")
    nf = pd.read_csv(RAW / "netflix_all_weeks_countries.tsv", sep="\t")
    nf = nf[nf.country_iso2 == "IN"]
    norm = lambda s: re.sub(r"[^a-z0-9]", "", re.sub(r"\(.*?\)", "", str(s)).lower())
    weeks = nf.assign(k=nf.show_title.map(norm)).groupby("k").agg(netflix_in_weeks_top10=("week", "nunique"), netflix_in_best_rank=("weekly_rank", "min"), netflix_in_first_week=("week", "min"))
    restricted["k"] = restricted.wiki_title.map(norm)
    restricted = restricted.merge(weeks, on="k", how="left").drop(columns="k")
    is_nf = restricted.platform == "Netflix"
    for c in ("netflix_in_weeks_top10", "netflix_in_best_rank", "netflix_in_first_week"):
        restricted.loc[~is_nf, c] = np.nan
    restricted.loc[is_nf & restricted.netflix_in_weeks_top10.isna(), "netflix_in_weeks_top10"] = 0
    (PROC / "restricted").mkdir(exist_ok=True)
    restricted.to_csv(PROC / "restricted" / "titles_restricted_sources.csv", index=False)

    keep = ["title_id", "wiki_title", "qid", "imdb_id", "platform", "all_platforms", "format", "release_date", "release_date_source", "release_year", "release_month",
            "primary_language", "languages", "primary_genre", "genres", "scripted", "is_franchise_or_sequel", "is_adaptation", "num_seasons", "num_episodes", "runtime_min",
            "cast_list", "directors_creators", "production_companies", "lead_company", "company_prior_titles", "cast_prom_max", "cast_prom_mean", "cast_n_matched",
            "page_live_at_release", "first_pageview_date", "views_pre_30d", "views_d0_6", "views_d0_27", "views_d28_89", "sustain_ratio", "source_categories"]
    out = t[keep].copy()
    out["first_pageview_date"] = out.first_pageview_date.astype("string")
    out["retrieved"] = RETRIEVED
    out.to_csv(PROC / "titles.csv", index=False)
    return out, restricted


if __name__ == "__main__":
    o, r = main()
    s = o[o.scripted]
    print(len(o), "titles;", len(s), "scripted;", int(s.page_live_at_release.sum()), "with page live at release")
    print(s.groupby("platform").agg(n=("title_id", "size"), live=("page_live_at_release", "mean"), med=("views_d0_27", "median")).round(2).to_string())
    print(s.groupby("primary_language").agg(n=("title_id", "size"), live=("page_live_at_release", "mean"), med=("views_d0_27", "median")).round(2).to_string())
    print(s.views_d0_27.describe().round(0).to_dict()); print("cast matched:", (s.cast_n_matched > 0).mean().round(3))
    print("imdb votes matched:", r.numVotes.notna().mean().round(3), "| netflix titles with >=1 week:", int((r.netflix_in_weeks_top10 > 0).sum()), "of", int((r.platform == "Netflix").sum()))
