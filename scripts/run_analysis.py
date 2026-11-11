"""Rebuild the dataset, database, analysis outputs, Tableau CSVs and report figures from data/raw.
Usage: python scripts/run_analysis.py   (run the collectors first; see README)"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ott_intel import build_dataset, db, analysis as A

OUT, FIG = ROOT / "tableau" / "data", ROOT / "reports" / "figures"
NAVY, TEAL, CLAY, GREY = "#1F3A5F", "#2A9D8F", "#C8553D", "#B0B7C3"


def main():
    build_dataset.main()
    con = db.build()
    t = A.load(); s = A.sample(t)
    res = {"n_titles": len(t), "n_scripted": int((t.scripted == 1).sum()), "n_sample": len(s)}
    A.coverage(t).to_csv(OUT / "coverage.csv", index=False)
    gs = pd.concat([A.group_stats(s, c) for c in ("platform", "primary_language", "primary_genre", "format", "release_year")]); gs.to_csv(OUT / "group_stats.csv", index=False)
    coef, m = A.ols(s); coef.to_csv(OUT / "ols_coefficients.csv", index=False)
    perf, fitted, split = A.predict(s); perf.to_csv(OUT / "model_performance.csv", index=False)
    imp = pd.concat([A.importance(fitted, split, st, "logit") for st in ("greenlight", "launch_eve")]); imp.to_csv(OUT / "model_importance.csv", index=False)
    opp = A.opportunity_cells(s, since=2020, min_n=6); opp.to_csv(OUT / "opportunity_cells.csv", index=False)
    A.opportunity_cells(s, since=2023, min_n=5).to_csv(OUT / "opportunity_cells_since_2023.csv", index=False)
    base = A.baselines(s); base.to_csv(OUT / "model_baselines.csv", index=False)
    lf = A.language_format(s); lf.to_csv(OUT / "language_format.csv", index=False)
    ctp = A.crime_thriller_premium(s); ctp.to_csv(OUT / "crime_thriller_premium.csv", index=False)
    res.update(A.headline_numbers(s))
    A.yearly(s).to_csv(OUT / "genre_by_year.csv", index=False)
    val = A.proxy_validation(s); val.to_csv(OUT / "proxy_validation.csv", index=False)
    for name in db.queries():
        db.run_query(name, con).to_csv(OUT / f"sql_{name}.csv", index=False)
    # title-level Tableau file: CC-licensed fields only
    tr, te, ytr, yte, thr = split
    pub = s[["title_id", "wiki_title", "platform", "format", "release_date", "release_year", "primary_language", "primary_genre", "is_franchise_or_sequel", "is_adaptation",
             "lead_company", "cast_prom_max", "views_pre_30d", "views_d0_6", "views_d0_27", "views_d28_89", "sustain_ratio"]].copy()
    pub["strong_launch"] = (pub.views_d0_27 >= thr).astype(int)
    pub["pct_within_language"] = pub.groupby("primary_language").views_d0_27.rank(pct=True)
    pub.to_csv(OUT / "titles_tableau.csv", index=False)

    # figures (static matplotlib, not Tableau)
    fig, ax = plt.subplots(figsize=(7.5, 4))
    g = gs[gs.dimension == "primary_language"].sort_values("median_views")
    ax.barh(g.level, g.median_views, color=NAVY); ax.errorbar(g.median_views, g.level, xerr=[g.median_views - g.p25, g.p75 - g.median_views], fmt="none", ecolor=GREY)
    ax.set_xscale("log"); ax.set_xlabel("Median launch pageviews, days 0-27 (log scale; bars = interquartile range)"); ax.set_title("Launch attention by primary language"); fig.tight_layout(); fig.savefig(FIG / "language.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 4))
    g = gs[gs.dimension == "primary_genre"].sort_values("median_views")
    ax.barh(g.level, g.median_views, color=TEAL); ax.set_xlabel("Median launch pageviews, days 0-27"); ax.set_title("Launch attention by primary genre"); fig.tight_layout(); fig.savefig(FIG / "genre.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    o = opp[opp.titles >= 5]
    ax.scatter(o.supply_share, o.demand_index, s=o.titles * 6, color=[CLAY if f.startswith("under") else (GREY if not f else NAVY) for f in o.flag], alpha=0.8)
    for r in o.itertuples():
        if r.flag or r.demand_index > 1.6: ax.annotate(f"{r.primary_language} {r.primary_genre}", (r.supply_share, r.demand_index), fontsize=7, xytext=(4, 2), textcoords="offset points")
    ax.axhline(1, color="k", lw=0.8); ax.set_xlabel("Share of the language's releases since 2020"); ax.set_ylabel("Demand index (cell median / language median)"); ax.set_title("Supply versus attention by language x genre"); fig.tight_layout(); fig.savefig(FIG / "opportunity.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    c = coef[coef.term.str.contains("platform|franchise|adaptation|cast_prom|format")].copy()
    c["label"] = c.term.str.replace(r"C\((\w+).*?\)\[T\.(.*?)\]", r"\2", regex=True)
    c = c.sort_values("multiplier")
    ax.errorbar(c.multiplier, c.label, xerr=[c.multiplier - c.mult_low, c.mult_high - c.multiplier], fmt="o", color=NAVY, ecolor=GREY); ax.axvline(1, color="k", lw=0.8); ax.set_xscale("log")
    ax.set_xlabel("Multiplier on launch pageviews vs reference (95% CI, HC3)"); ax.set_title("Associations with launch attention, controls included"); ax.tick_params(labelsize=7); fig.tight_layout(); fig.savefig(FIG / "ols.png", dpi=160); plt.close(fig)

    res.update({"threshold_views": float(thr), "ols_r2": float(coef.r2.iloc[0]), "ols_n": int(coef.n.iloc[0])})
    (OUT / "run_summary.json").write_text(json.dumps(res, indent=1))
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
    print(res); print(A.coverage(t).round(2).to_string(index=False))
    print(gs.drop(columns=["kruskal_h"]).round(3).to_string(index=False))
    print(coef[["term", "multiplier", "mult_low", "mult_high", "p_value"]].round(3).to_string(index=False))
    print(perf.round(3).to_string(index=False)); print(imp.round(3).to_string(index=False))
    print(base.round(3).to_string(index=False)); print(lf.round(3).to_string(index=False)); print(ctp.round(3).to_string(index=False)); print({k: round(v, 3) for k, v in res.items()})
    print(s.nlargest(8, "views_d0_27")[["wiki_title", "platform", "primary_language", "primary_genre", "release_year", "views_d0_27"]].to_string(index=False))


if __name__ == "__main__":
    main()
