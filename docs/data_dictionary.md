# Data dictionary
## data/processed/titles.csv (one row per title; CC BY-SA 4.0 derived data)
| Column | Type | Definition | Source |
|---|---|---|---|
| title_id | text | Surrogate key (T0001...) in release-date order | derived |
| wiki_title | text | English-Wikipedia article title | Wikipedia |
| qid / imdb_id | text | Wikidata item; IMDb identifier (Wikidata P345) | Wikidata |
| platform | text | Assigned service (priority order when on several lists) | Wikipedia categories |
| all_platforms / source_categories | text | Every platform list / category the title appears in | Wikipedia |
| format | film / series | From infobox type | Wikipedia |
| release_date, release_date_source | date, text | First release (series: first premiere); infobox or Wikidata | Wikipedia / Wikidata |
| release_year, release_month | int | From release_date | derived |
| primary_language, languages | text | First non-English Indian language listed; all listed | Wikipedia |
| primary_genre, genres | text | Mapped genre groups in the order the text lists them (first listed is primary) | Wikipedia |
| scripted | bool | False for documentary, unscripted (reality, talk, game, stand-up), animation and titles with no recoverable genre | derived |
| is_franchise_or_sequel | bool | Sequel, spin-off or remake of an earlier work: infobox preceded-by, Wikidata \"follows\", a numeral in the title, or sequel/remake wording in the lead. Later instalments do not flag the original | Wikipedia / Wikidata |
| is_adaptation | bool | Infobox "based on" present | Wikipedia |
| num_seasons, num_episodes, runtime_min | int | Present-day infobox values; not used as predictors | Wikipedia |
| cast_list, directors_creators | text | Billing order from infobox, up to 8 / 3 names | Wikipedia |
| production_companies, lead_company | text | Infobox companies; first listed | Wikipedia |
| company_prior_titles | int | Earlier titles in this dataset from the same lead company | derived |
| cast_prom_max, cast_prom_mean | float | Max / mean over top-3 billed cast of mean monthly pageviews in the 12 full months before the release month | Pageviews API |
| cast_n_matched | int | Top-3 cast with a Wikipedia article | derived |
| page_live_at_release | bool | Article had pageviews on or before release day and at least one in days 0-27 | Pageviews API |
| first_pageview_date | text (yyyymmdd) | First day with pageviews inside the collected window (from 60 days before release) | Pageviews API |
| views_pre_30d | int | Pageviews, days -30 to -1 | Pageviews API |
| views_d0_6, views_d0_27 | int | Pageviews, days 0-6 and 0-27 (launch attention) | Pageviews API |
| views_d28_89 | int | Pageviews, days 28-89; blank if not yet observable | Pageviews API |
| sustain_ratio | float | views_d28_89 / views_d0_27 | derived |
| retrieved | date | Collection date | — |

Missing values: view fields are blank when `page_live_at_release` is false (418 of 920 scripted titles). Cast prominence is blank when no top-3 cast member has an article.

## data/processed/ott_observatory.sqlite
Normalised tables: `platforms`, `titles`, `release_events`, `languages`, `title_languages`, `genres`, `title_genres`, `production_houses`, `title_production_houses`, `people`, `title_credits`, `metric_definitions`, `performance_observations`, `data_sources`; view `v_titles`. Schema: `sql/schema.sql`.

## tableau/data
`titles_tableau.csv` (analysis sample, one row per title, adds `strong_launch` and `pct_within_language`), `coverage.csv`, `group_stats.csv`, `ols_coefficients.csv`, `model_performance.csv`, `model_baselines.csv`, `model_importance.csv`, `opportunity_cells.csv`, `opportunity_cells_since_2023.csv`, `genre_by_year.csv`, `language_format.csv`, `crime_thriller_premium.csv`, `proxy_validation.csv`, `sql_q01..q10_*.csv` (output of each query in `sql/analysis_queries.sql`), `run_summary.json`.
