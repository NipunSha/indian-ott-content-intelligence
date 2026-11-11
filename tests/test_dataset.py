"""Integrity checks on the built dataset and database (skipped if data has not been built)."""
import sqlite3
from datetime import date
import numpy as np
import pandas as pd
import pytest
from ott_intel.http import ROOT
from ott_intel import build_dataset as B

CSV = ROOT / "data" / "processed" / "titles.csv"
DBF = ROOT / "data" / "processed" / "ott_observatory.sqlite"
pytestmark = pytest.mark.skipif(not CSV.exists(), reason="dataset not built")


@pytest.fixture(scope="module")
def t():
    return pd.read_csv(CSV)


def test_keys_unique_and_dates_in_window(t):
    assert t.title_id.is_unique and t.wiki_title.is_unique
    d = pd.to_datetime(t.release_date)
    assert d.min() >= pd.Timestamp("2018-01-01") and d.max() <= pd.Timestamp("2026-10-12")


def test_views_only_when_page_live_and_windows_nest(t):
    assert t.loc[~t.page_live_at_release, "views_d0_27"].isna().all()
    live = t[t.page_live_at_release]
    assert (live.views_d0_6 <= live.views_d0_27).all()
    assert (live.views_d0_27 >= 0).all()


def test_no_restricted_columns_in_public_file(t):
    assert not {"numVotes", "averageRating", "netflix_in_weeks_top10"} & set(t.columns)


def test_cast_prominence_uses_only_pre_release_months():
    monthly = {"A": {"20200101": 100, "20200201": 100, "20200301": 9_999_999, "20190301": 100}}
    mx, mean, n = B.cast_prominence("X", date(2020, 3, 20), {"X": "A"}, monthly)
    assert n == 1 and mx < 1000  # the release month (March 2020) must not be included


def test_window_sum():
    d = {"20200101": 5, "20200102": 7, "20200110": 100}
    assert B.window_sum(d, date(2020, 1, 1), 0, 1) == 12 and B.window_sum(d, date(2020, 1, 2), -1, -1) == 5


def test_primary_language_prefers_indian_language():
    assert B.primary_language("English; Hindi") == "Hindi" and B.primary_language("English") == "English" and B.primary_language("Odia") == "Other Indian"


def test_database_matches_csv_and_queries_run(t):
    from ott_intel import db
    con = sqlite3.connect(DBF)
    assert con.execute("SELECT COUNT(*) FROM titles").fetchone()[0] == len(t)
    assert con.execute("SELECT COUNT(*) FROM title_languages WHERE is_primary = 1").fetchone()[0] == len(t)
    n_views = con.execute("SELECT COUNT(*) FROM performance_observations WHERE metric = 'wiki_views_d0_27'").fetchone()[0]
    assert n_views == t.views_d0_27.notna().sum()
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []
    for name in db.queries():
        assert len(db.run_query(name, con).columns) > 0, name
    v = pd.read_sql_query("SELECT * FROM v_titles", con)
    assert len(v) == len(t)


def test_model_uses_no_post_release_features():
    from ott_intel import analysis as A
    banned = {"views_d0_6", "views_d0_27", "views_d28_89", "sustain_ratio", "num_seasons", "num_episodes"}
    assert not banned & set(A.CAT + A.NUM_A + ["log_pre_views"])


def test_threshold_comes_from_training_period_only():
    from ott_intel import analysis as A
    s = A.sample(A.load())
    perf, fitted, (tr, te, ytr, yte, thr) = A.predict(s, n_boot=20)
    assert thr == pytest.approx(tr.views_d0_27.quantile(0.75))
    assert tr.release_year.max() <= 2023 < te.release_year.min()
    assert ytr.mean() == pytest.approx(0.25, abs=0.02)


def test_company_track_record_has_no_look_ahead(t):
    d = t[t.lead_company.notna() & (t.lead_company != "")].copy()
    d["rel"] = pd.to_datetime(d.release_date)
    for r in d.sample(40, random_state=0).itertuples():
        earlier = ((d.lead_company == r.lead_company) & (d.rel < r.rel)).sum()
        same_day = ((d.lead_company == r.lead_company) & (d.rel == r.rel)).sum() - 1
        assert earlier <= r.company_prior_titles <= earlier + same_day


def test_unscripted_and_unknown_genres_are_not_scripted(t):
    assert not t[t.primary_genre.isin(["Unscripted", "Documentary", "Animation", "Unknown"])].scripted.any()
