# Tableau dashboard specification: Indian OTT Content Intelligence
**Status: specification only. No Tableau workbook has been built or tested.** Data: CSVs in `tableau/data/` written by `scripts/run_analysis.py`. Primary source: `titles_tableau.csv` (one row per analysed title).

Every page carries the caption: *"Launch attention = English-Wikipedia pageviews in the 28 days from release. A proxy for public interest, not viewership."*

Global filters: Platform, Primary language, Format, Release year (range). Palette: navy #1F3A5F (default), teal #2A9D8F (highlight), clay #C8553D (flag), grey #B0B7C3 (context).

| # | Page | Question | Sheets | Data |
|---|---|---|---|---|
| 1 | Market overview | How many documented originals does each platform release, and how complete is measurement? | Titles by platform (bar); measurable share (bar); releases per year (line) | coverage, sql_q01_market_overview, sql_q02_release_trend |
| 2 | Genre and language | Where is launch attention highest once language is held fixed? | Heat map language x genre of within-language percentile (median); box plot of launch views by genre (log axis) | titles_tableau, sql_q03_median_launch_by_language_genre |
| 3 | Platform comparison | How do platforms differ in slate mix and typical launch attention? | 100% stacked bar of genre mix; median launch views with IQR | titles_tableau, group_stats |
| 4 | Release trends | Which genres are gaining share of releases, and is attention following? | Area chart of genre share by year; line of median launch views by year | genre_by_year |
| 5 | Production houses | Which producers deliver above-median launches repeatedly? | Scatter: titles vs share above median, size = platforms | sql_q06_production_house_portfolio |
| 6 | Demand indicators | What is associated with attention after controls, and how predictable is a strong launch? | Coefficient plot with CIs; model scorecard table | ols_coefficients, model_performance, model_importance |
| 7 | Opportunity explorer | Which language x genre cells are under-supplied relative to attention? | Scatter supply share vs demand index with CI whiskers; detail table on click | opportunity_cells |

## Wireframe (not a screenshot)
```
+----------------------------------------------------------------------+
| Indian OTT Content Intelligence   [Platform v][Language v][Year ---] |
+-------------------------------+--------------------------------------+
| Language x genre heat map     | Launch views by genre (box, log)     |
| (within-language percentile)  |                                      |
+-------------------------------+--------------------------------------+
| Supply share vs demand index (opportunity scatter, CI whiskers)      |
+----------------------------------------------------------------------+
| Proxy note | n titles in view | data retrieved 2026-11-11             |
+----------------------------------------------------------------------+
```

## Assembly steps
1. Connect to `titles_tableau.csv`; add the other CSVs as separate sources (different grains; do not join).
2. Create the calculated fields in `calculated_fields.md`.
3. Use a log axis for any raw pageview measure; show medians, not means.
4. Add a "n titles" label to every aggregate and hide cells with fewer than 5 titles.
