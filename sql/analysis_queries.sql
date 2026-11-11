-- Query library. Each query is preceded by "-- name: <id>" and is executed by src/ott_intel/db.py::run_query.
-- "launch_views" = English-Wikipedia pageviews in the 28 days from release: an attention proxy, not viewership.

-- name: q01_market_overview
-- Scripted titles per platform by format, with first and last release year.
SELECT platform, COUNT(*) AS titles, SUM(format = 'series') AS series, SUM(format = 'film') AS films,
       MIN(release_year) AS first_year, MAX(release_year) AS last_year
FROM v_titles WHERE scripted = 1 GROUP BY platform ORDER BY titles DESC;

-- name: q02_release_trend
-- Releases per year and platform with year-on-year change (window function).
WITH y AS (SELECT platform, release_year, COUNT(*) AS n FROM v_titles WHERE scripted = 1 GROUP BY platform, release_year)
SELECT platform, release_year, n, n - LAG(n) OVER (PARTITION BY platform ORDER BY release_year) AS change_vs_prior_year,
       SUM(n) OVER (PARTITION BY platform ORDER BY release_year) AS cumulative_titles
FROM y ORDER BY platform, release_year;

-- name: q03_median_launch_by_language_genre
-- Median launch attention by language x genre (median via row numbering; cells with fewer than 5 titles dropped).
WITH v AS (SELECT primary_language, primary_genre, launch_views FROM v_titles WHERE scripted = 1 AND launch_views IS NOT NULL),
r AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY primary_language, primary_genre ORDER BY launch_views) AS rn,
             COUNT(*) OVER (PARTITION BY primary_language, primary_genre) AS n FROM v)
SELECT primary_language, primary_genre, n AS titles, ROUND(AVG(launch_views)) AS median_launch_views
FROM r WHERE rn IN ((n + 1) / 2, (n + 2) / 2) AND n >= 5
GROUP BY primary_language, primary_genre, n ORDER BY primary_language, median_launch_views DESC;

-- name: q04_within_language_percentile
-- Each title's percentile of launch attention inside its own language (controls for English-Wikipedia language bias).
SELECT title_id, wiki_title, platform, primary_language, primary_genre, release_year, launch_views,
       ROUND(PERCENT_RANK() OVER (PARTITION BY primary_language ORDER BY launch_views), 3) AS pct_within_language
FROM v_titles WHERE scripted = 1 AND launch_views IS NOT NULL;

-- name: q05_top_titles_per_platform
-- Three highest-attention launches per platform.
WITH r AS (SELECT *, RANK() OVER (PARTITION BY platform ORDER BY launch_views DESC) AS rk FROM v_titles WHERE scripted = 1 AND launch_views IS NOT NULL)
SELECT platform, rk, wiki_title, primary_language, primary_genre, release_year, CAST(launch_views AS INTEGER) AS launch_views FROM r WHERE rk <= 3 ORDER BY platform, rk;

-- name: q06_production_house_portfolio
-- Production houses with at least four measured titles: volume, platform spread and share of titles above the overall median.
WITH med AS (SELECT AVG(launch_views) AS m FROM (SELECT launch_views, ROW_NUMBER() OVER (ORDER BY launch_views) rn, COUNT(*) OVER () n FROM v_titles WHERE scripted = 1 AND launch_views IS NOT NULL) WHERE rn IN ((n + 1) / 2, (n + 2) / 2))
SELECT ph.company_name, COUNT(DISTINCT v.title_id) AS titles, COUNT(DISTINCT v.platform) AS platforms,
       SUM(v.launch_views IS NOT NULL) AS measured_titles,
       ROUND(AVG(CASE WHEN v.launch_views IS NOT NULL THEN v.launch_views > (SELECT m FROM med) END), 2) AS share_above_median
FROM production_houses ph JOIN title_production_houses tp USING (company_id) JOIN v_titles v USING (title_id)
WHERE v.scripted = 1 AND tp.credit_order = 1 GROUP BY ph.company_name HAVING SUM(v.launch_views IS NOT NULL) >= 4 ORDER BY titles DESC;

-- name: q07_franchise_vs_original
-- Sequel/remake and adaptation status against mean launch attention (means are hit-sensitive; see Python medians).
SELECT is_franchise_or_sequel, is_adaptation, COUNT(*) AS titles, ROUND(AVG(launch_views)) AS mean_launch_views
FROM v_titles WHERE scripted = 1 AND launch_views IS NOT NULL GROUP BY 1, 2;

-- name: q08_sustain_by_format
-- Sustained attention (days 28-89 relative to days 0-27) by format.
SELECT t.format, COUNT(*) AS titles, ROUND(AVG(o.value), 3) AS mean_sustain_ratio
FROM titles t JOIN performance_observations o ON o.title_id = t.title_id AND o.metric = 'sustain_ratio' WHERE t.scripted = 1 GROUP BY t.format;

-- name: q09_cast_reuse
-- Most frequently billed lead cast (top-3 billing) across platforms.
SELECT pe.person_name, COUNT(*) AS lead_credits, COUNT(DISTINCT t.platform_id) AS platforms
FROM people pe JOIN title_credits c USING (person_id) JOIN titles t USING (title_id)
WHERE c.role = 'cast' AND c.billing_order <= 3 AND t.scripted = 1 GROUP BY pe.person_name HAVING COUNT(*) >= 4 ORDER BY lead_credits DESC LIMIT 25;

-- name: q10_supply_demand_cells
-- Supply share versus relative demand (means; the Python analysis reports medians) for language x genre cells, releases from 2023.
WITH base AS (SELECT * FROM v_titles WHERE scripted = 1 AND launch_views IS NOT NULL AND release_year >= 2023),
lang AS (SELECT primary_language, AVG(launch_views) AS lang_mean, COUNT(*) AS lang_n FROM base GROUP BY primary_language)
SELECT b.primary_language, b.primary_genre, COUNT(*) AS titles, ROUND(1.0 * COUNT(*) / l.lang_n, 3) AS share_of_language_supply,
       ROUND(AVG(b.launch_views) / l.lang_mean, 2) AS mean_views_vs_language_mean
FROM base b JOIN lang l USING (primary_language) GROUP BY b.primary_language, b.primary_genre HAVING COUNT(*) >= 4 ORDER BY mean_views_vs_language_mean DESC;
