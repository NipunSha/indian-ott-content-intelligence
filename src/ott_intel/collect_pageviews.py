"""Step 5: Wikimedia pageviews (CC0). Daily series around each title's release and monthly series for lead cast."""
import json
from datetime import date, timedelta
from urllib.parse import quote
import pandas as pd
from .http import get, ROOT

RAW, PROC = ROOT / "data" / "raw", ROOT / "data" / "processed"
API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{}/{}/{}/{}"
LAST_FULL_DAY = date(2026, 11, 8)   # collection cut-off (data retrieved 2026-11-11)
W = "https://en.wikipedia.org/w/api.php"


def series(article, gran, start, end):
    r = get(API.format(quote(article.replace(" ", "_"), safe=""), gran, start.strftime("%Y%m%d"), end.strftime("%Y%m%d")), min_interval=0.5)
    return {i["timestamp"][:8]: i["views"] for i in r["items"]} if r else {}


def resolve_redirects(names):
    out = {}
    for i in range(0, len(names), 50):
        r = get(W, {"action": "query", "titles": "|".join(names[i:i + 50]), "redirects": 1, "format": "json"}, min_interval=2.5)
        q = r.get("query", {})
        norm = {x["from"]: x["to"] for x in q.get("normalized", [])}
        red = {x["from"]: x["to"] for x in q.get("redirects", [])}
        missing = {p["title"] for p in q.get("pages", {}).values() if "missing" in p}
        for n in names[i:i + 50]:
            t = norm.get(n, n); t = red.get(t, t)
            out[n] = None if t in missing else t
    return out


def main():
    t = pd.read_csv(PROC / "titles_stage.csv")
    t = t[t.is_indian & t.is_title_page & t.release_date.notna()].copy()
    t["rel"] = pd.to_datetime(t.release_date).dt.date
    t = t[(t.rel >= date(2018, 1, 1)) & (t.rel <= LAST_FULL_DAY - timedelta(days=27))]
    daily = {}
    for n, (title, rel) in enumerate(zip(t.wiki_title, t.rel)):
        daily[title] = series(title, "daily", rel - timedelta(days=60), min(rel + timedelta(days=90), LAST_FULL_DAY))
        if n % 100 == 0: print("titles", n, len(t), flush=True)
    (RAW / "pageviews_titles_daily.json").write_text(json.dumps(daily), encoding="utf-8")
    cast = sorted({c for s in t.cast_list.dropna() for c in s.split("; ")[:3] if c and "[" not in c and "#" not in c})
    res = resolve_redirects(cast)
    (RAW / "cast_redirects.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    monthly = {}
    targets = sorted({v for v in res.values() if v})
    for n, person in enumerate(targets):
        monthly[person] = series(person, "monthly", date(2016, 12, 1), date(2026, 10, 31))
        if n % 200 == 0: print("cast", n, len(targets), flush=True)
    (RAW / "pageviews_cast_monthly.json").write_text(json.dumps(monthly, ensure_ascii=False), encoding="utf-8")
    print("done", len(daily), len(monthly), flush=True)


if __name__ == "__main__":
    main()
