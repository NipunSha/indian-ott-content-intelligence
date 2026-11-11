"""Load data/processed/titles.csv into a normalised SQLite database and run the query library."""
import re, sqlite3
import pandas as pd
from .http import ROOT

DB = ROOT / "data" / "processed" / "ott_observatory.sqlite"
SOURCES = [
    ("WIKIPEDIA", "English Wikipedia (categories, infoboxes)", "https://en.wikipedia.org", "CC BY-SA 4.0", "Title frame and descriptive metadata"),
    ("WIKIDATA", "Wikidata", "https://www.wikidata.org", "CC0", "Identifiers, country of origin, fallback metadata"),
    ("PAGEVIEWS", "Wikimedia Pageviews API", "https://wikimedia.org/api/rest_v1/", "CC0", "Daily and monthly user pageviews (agent=user)"),
]
METRICS = [
    ("wiki_views_pre_30d", "English-Wikipedia pageviews, days -30 to -1 before release", "pageviews", "PAGEVIEWS"),
    ("wiki_views_d0_6", "English-Wikipedia pageviews, release day to day 6", "pageviews", "PAGEVIEWS"),
    ("wiki_views_d0_27", "English-Wikipedia pageviews, release day to day 27 (launch attention proxy)", "pageviews", "PAGEVIEWS"),
    ("wiki_views_d28_89", "English-Wikipedia pageviews, days 28 to 89", "pageviews", "PAGEVIEWS"),
    ("sustain_ratio", "views d28-89 divided by views d0-27", "ratio", "PAGEVIEWS"),
    ("cast_prom_max", "Highest mean monthly pageviews among top-3 billed cast, 12 months before release month", "pageviews/month", "PAGEVIEWS"),
]


def _dim(con, table, col, values):
    vals = sorted({v for v in values if v})
    con.executemany(f"INSERT INTO {table} ({col}) VALUES (?)", [(v,) for v in vals])
    return {r[1]: r[0] for r in con.execute(f"SELECT * FROM {table}").fetchall()}


def split(s):
    return [x for x in str(s).split("; ") if x and x != "nan"]


def build(csv=ROOT / "data" / "processed" / "titles.csv", db=DB, retrieved="2026-11-11"):
    t = pd.read_csv(csv)
    if db.exists(): db.unlink()
    con = sqlite3.connect(db)
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    con.executemany("INSERT INTO data_sources VALUES (?,?,?,?,?,?)", [(a, b, c, d, retrieved, e) for a, b, c, d, e in SOURCES])
    con.executemany("INSERT INTO metric_definitions VALUES (?,?,?,?,0)", METRICS)
    plat = _dim(con, "platforms", "platform_name", t.platform)
    lang = _dim(con, "languages", "language_name", [l for s in t.languages for l in split(s)] + list(t.primary_language))
    gen = _dim(con, "genres", "genre_name", [g for s in t.genres for g in split(s)] + list(t.primary_genre))
    comp = _dim(con, "production_houses", "company_name", [c for s in t.production_companies for c in split(s)])
    ppl = _dim(con, "people", "person_name", [p for s in list(t.cast_list) + list(t.directors_creators) for p in split(s)])
    nn = lambda v: None if pd.isna(v) else int(v)
    for r in t.itertuples():
        con.execute("INSERT INTO titles VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (r.title_id, r.wiki_title, r.qid if isinstance(r.qid, str) else None, r.imdb_id if isinstance(r.imdb_id, str) else None,
                    plat[r.platform], r.format, int(r.scripted), int(r.is_franchise_or_sequel), int(r.is_adaptation), nn(r.num_seasons), nn(r.num_episodes), nn(r.runtime_min)))
        con.execute("INSERT INTO release_events (title_id, release_date, date_source) VALUES (?,?,?)", (r.title_id, r.release_date, r.release_date_source))
        langs = list(dict.fromkeys([r.primary_language] + split(r.languages)))
        con.executemany("INSERT OR IGNORE INTO title_languages VALUES (?,?,?)", [(r.title_id, lang[l], int(l == r.primary_language)) for l in langs])
        gens = list(dict.fromkeys([r.primary_genre] + split(r.genres)))
        con.executemany("INSERT OR IGNORE INTO title_genres VALUES (?,?,?)", [(r.title_id, gen[g], int(g == r.primary_genre)) for g in gens])
        con.executemany("INSERT OR IGNORE INTO title_production_houses VALUES (?,?,?)", [(r.title_id, comp[c], i) for i, c in enumerate(split(r.production_companies), 1)])
        con.executemany("INSERT OR IGNORE INTO title_credits VALUES (?,?,?,?)", [(r.title_id, ppl[p], "cast", i) for i, p in enumerate(split(r.cast_list), 1)])
        con.executemany("INSERT OR IGNORE INTO title_credits VALUES (?,?,?,?)", [(r.title_id, ppl[p], "director_or_creator", i) for i, p in enumerate(split(r.directors_creators), 1)])
        for metric, colname in [("wiki_views_pre_30d", "views_pre_30d"), ("wiki_views_d0_6", "views_d0_6"), ("wiki_views_d0_27", "views_d0_27"), ("wiki_views_d28_89", "views_d28_89"), ("sustain_ratio", "sustain_ratio"), ("cast_prom_max", "cast_prom_max")]:
            v = getattr(r, colname)
            if pd.notna(v): con.execute("INSERT INTO performance_observations VALUES (?,?,?)", (r.title_id, metric, float(v)))
    con.commit()
    return con


def queries(path=ROOT / "sql" / "analysis_queries.sql"):
    out, name, buf = {}, None, []
    for line in path.read_text().splitlines():
        m = re.match(r"-- name: (\w+)", line)
        if m:
            if name: out[name] = "\n".join(buf)
            name, buf = m.group(1), []
        elif name: buf.append(line)
    if name: out[name] = "\n".join(buf)
    return out


def run_query(name, con=None):
    con = con or sqlite3.connect(DB)
    return pd.read_sql_query(queries()[name], con)
