# Methodology
## Sample frame
Titles are the members of 22 English-Wikipedia categories of platform originals (list in `src/ott_intel/collect_frame.py`), e.g. "ZEE5 original programming", "Indian television series distributed by Netflix", "Amazon Prime Video original films". Broad categories are filtered to Indian titles (Wikidata country of origin, infobox country, or "Indian" in the lead sentence). Pages without a film/television infobox are dropped. Voot and Disney+ Hotstar titles are grouped under JioHotstar, their successor service.

A title on several platform lists is assigned once, by a fixed priority order; all memberships are kept in `all_platforms`. A series is one row dated at its first premiere; later seasons are not separate rows. Distinct sequel pages are separate titles and flagged `is_franchise_or_sequel`.

## Variables
Infobox fields are parsed from section-0 wikitext with Wikidata as fallback. Language is the first non-English Indian language listed. Genre keywords are mapped to 13 groups; the primary genre is the first one the infobox lists (or, where the infobox has none, the first in the lead sentence). \"Drama\" as a primary genre therefore often means a title nobody described more specifically. Unscripted, documentary and animation titles, and titles with no recoverable genre, are kept in the database but excluded from analysis. The sequel flag uses only information available before release (preceded-by fields, title numerals, sequel/remake wording), so an original that later received follow-ups is not flagged.

## Demand proxy
`views_d0_27`: sum of daily user (non-bot) pageviews of the title's English-Wikipedia article from release day to day 27. `views_pre_30d` covers days -30 to -1; `views_d28_89` covers days 28-89; `sustain_ratio` is their quotient with `views_d0_27`. A title enters the analysis only if its article already had pageviews on or before release day (`page_live_at_release`); otherwise launch attention would be undercounted.

Validation against independent signals (IMDb vote counts; weeks in Netflix's India Top 10 for Netflix titles) is in `tableau/data/proxy_validation.csv`. Those sources are not redistributable, so only correlation statistics are published.

## Pre-release features
Platform, language, genre, format, franchise/sequel flag, adaptation flag, production house's count of earlier titles in the dataset, and lead-cast prominence: the highest mean monthly Wikipedia pageviews among the three top-billed cast over the 12 full months before the release month. Episode and season counts are excluded from models because the infobox shows today's values.

## Statistics
- Group comparisons: medians, interquartile ranges, Kruskal-Wallis tests.
- OLS on log10 launch views with platform, language, genre, format, flags, cast prominence and release-year fixed effects; HC3 standard errors; rare levels lumped into "Other". Coefficients are associations.
- Prediction: "strong launch" = at or above the 75th percentile of launch views among 2018-2023 releases. Models are trained on 2018-2023 and tested on 2024-2026. Two information sets: *greenlight* (features above) and *launch eve* (adds pre-release pageviews). Logistic regression is compared with gradient boosting; ROC AUC (bootstrap CI), PR AUC, Brier score against a base-rate forecast, and precision in the top 20% of scores.
- Opportunity cells: for releases since 2020 (a since-2023 cut is exported as a recency check), each language x genre cell's median launch views divided by the language median (demand index, bootstrap 95% CI) against its share of that language's releases. Indexing within language removes level differences between languages, not any genre-specific bias in who uses English Wikipedia. Twenty-three cells are compared without a multiplicity correction; the report says which results would survive one.
- Clustering was not used: the features are mostly categorical and the segments that matter (language x genre) are already explicit.
