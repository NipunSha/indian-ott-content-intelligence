-- Indian OTT Content Intelligence Observatory: normalised SQLite schema
PRAGMA foreign_keys = ON;

CREATE TABLE data_sources (
  source_id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT, licence TEXT, retrieved DATE, notes TEXT);

CREATE TABLE platforms (
  platform_id INTEGER PRIMARY KEY, platform_name TEXT UNIQUE NOT NULL, platform_note TEXT);

CREATE TABLE titles (
  title_id TEXT PRIMARY KEY, wiki_title TEXT UNIQUE NOT NULL, wikidata_qid TEXT, imdb_id TEXT,
  platform_id INTEGER NOT NULL REFERENCES platforms(platform_id),
  format TEXT CHECK (format IN ('series','film')), scripted INTEGER NOT NULL,
  is_franchise_or_sequel INTEGER NOT NULL, is_adaptation INTEGER NOT NULL,
  num_seasons INTEGER, num_episodes INTEGER, runtime_min INTEGER);

CREATE TABLE release_events (
  release_id INTEGER PRIMARY KEY, title_id TEXT NOT NULL REFERENCES titles(title_id),
  event_type TEXT NOT NULL DEFAULT 'first_release', release_date DATE NOT NULL, date_source TEXT);

CREATE TABLE languages (language_id INTEGER PRIMARY KEY, language_name TEXT UNIQUE NOT NULL);
CREATE TABLE title_languages (
  title_id TEXT REFERENCES titles(title_id), language_id INTEGER REFERENCES languages(language_id),
  is_primary INTEGER NOT NULL, PRIMARY KEY (title_id, language_id));

CREATE TABLE genres (genre_id INTEGER PRIMARY KEY, genre_name TEXT UNIQUE NOT NULL);
CREATE TABLE title_genres (
  title_id TEXT REFERENCES titles(title_id), genre_id INTEGER REFERENCES genres(genre_id),
  is_primary INTEGER NOT NULL, PRIMARY KEY (title_id, genre_id));

CREATE TABLE production_houses (company_id INTEGER PRIMARY KEY, company_name TEXT UNIQUE NOT NULL);
CREATE TABLE title_production_houses (
  title_id TEXT REFERENCES titles(title_id), company_id INTEGER REFERENCES production_houses(company_id),
  credit_order INTEGER NOT NULL, PRIMARY KEY (title_id, company_id));

CREATE TABLE people (person_id INTEGER PRIMARY KEY, person_name TEXT UNIQUE NOT NULL);
CREATE TABLE title_credits (
  title_id TEXT REFERENCES titles(title_id), person_id INTEGER REFERENCES people(person_id),
  role TEXT CHECK (role IN ('cast','director_or_creator')), billing_order INTEGER NOT NULL,
  PRIMARY KEY (title_id, person_id, role));

-- One row per title x metric. Metrics are NOT comparable with each other; see metric_definitions.
CREATE TABLE metric_definitions (
  metric TEXT PRIMARY KEY, definition TEXT NOT NULL, unit TEXT, source_id TEXT REFERENCES data_sources(source_id),
  is_viewership INTEGER NOT NULL DEFAULT 0);
CREATE TABLE performance_observations (
  title_id TEXT REFERENCES titles(title_id), metric TEXT REFERENCES metric_definitions(metric),
  value REAL, PRIMARY KEY (title_id, metric));

CREATE VIEW v_titles AS
SELECT t.title_id, t.wiki_title, p.platform_name AS platform, t.format, t.scripted, t.is_franchise_or_sequel, t.is_adaptation,
       r.release_date, CAST(strftime('%Y', r.release_date) AS INTEGER) AS release_year,
       (SELECT l.language_name FROM title_languages tl JOIN languages l USING (language_id) WHERE tl.title_id = t.title_id AND tl.is_primary = 1) AS primary_language,
       (SELECT g.genre_name FROM title_genres tg JOIN genres g USING (genre_id) WHERE tg.title_id = t.title_id AND tg.is_primary = 1) AS primary_genre,
       (SELECT value FROM performance_observations o WHERE o.title_id = t.title_id AND o.metric = 'wiki_views_d0_27') AS launch_views
FROM titles t JOIN platforms p USING (platform_id) JOIN release_events r ON r.title_id = t.title_id AND r.event_type = 'first_release';
