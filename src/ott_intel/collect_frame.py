"""Step 1-3: build the title frame from Wikipedia categories, then fetch infobox wikitext and Wikidata claims.
Outputs raw JSON under data/raw/ (not redistributed; see data/README.md)."""
import json, re
from .http import get, ROOT

W = "https://en.wikipedia.org/w/api.php"
WD = "https://www.wikidata.org/w/api.php"
RAW = ROOT / "data" / "raw"

# category -> (platform, format hint, needs_india_filter)
CATEGORIES = {
    "Indian television series distributed by Netflix": ("Netflix", "series", False),
    "Netflix original films": ("Netflix", "film", True),
    "Amazon Prime Video original programming": ("Amazon Prime Video", "series", True),
    "Tamil-language Amazon Prime Video original programming": ("Amazon Prime Video", "series", False),
    "Amazon Prime Video original films": ("Amazon Prime Video", "film", True),
    "Disney+ Hotstar original programming": ("JioHotstar", "series", True),
    "Hindi-language Disney+ Hotstar original programming": ("JioHotstar", "series", False),
    "Tamil-language Disney+ Hotstar original programming": ("JioHotstar", "series", False),
    "Telugu-language Disney+ Hotstar original programming": ("JioHotstar", "series", False),
    "Disney+ Hotstar original films": ("JioHotstar", "film", True),
    "Voot original programming": ("JioHotstar", "series", False),
    "SonyLIV original programming": ("SonyLIV", "series", False),
    "SonyLIV original films": ("SonyLIV", "film", False),
    "ZEE5 original programming": ("ZEE5", "series", False),
    "ZEE5 original films": ("ZEE5", "film", False),
    "Aha (streaming service) original programming": ("Aha", "series", False),
    "Aha (streaming service) original films": ("Aha", "film", False),
    "ALTBalaji original programming": ("ALTT", "series", False),
    "MX Player original programming": ("MX Player", "series", False),
    "Hoichoi original programming": ("Hoichoi", "series", False),
    "TVF Play Shows": ("TVF Play", "series", False),
    "ETV Win original films": ("ETV Win", "film", False),
}
# Voot merged into JioCinema (2023) and JioCinema into JioHotstar (2025); both are grouped under JioHotstar.


def category_members(cat):
    out, cont = [], {}
    while True:
        r = get(W, {"action": "query", "generator": "categorymembers", "gcmtitle": "Category:" + cat, "gcmnamespace": 0,
                    "gcmlimit": 500, "prop": "pageprops", "ppprop": "wikibase_item", "format": "json", **cont}, min_interval=2.5)
        if not r or "query" not in r:
            break
        for p in r["query"]["pages"].values():
            out.append({"pageid": p["pageid"], "title": p["title"], "qid": p.get("pageprops", {}).get("wikibase_item")})
        if "continue" not in r:
            break
        cont = r["continue"]
    return out


def build_frame():
    frame = {}
    for cat, (platform, fmt, india_filter) in CATEGORIES.items():
        for m in category_members(cat):
            rec = frame.setdefault(m["title"], {**m, "platforms": [], "categories": [], "format_hint": fmt, "needs_india_filter": True})
            if platform not in rec["platforms"]:
                rec["platforms"].append(platform)
            rec["categories"].append(cat)
            rec["needs_india_filter"] = rec["needs_india_filter"] and india_filter
    (RAW / "frame.json").write_text(json.dumps(list(frame.values()), indent=1, ensure_ascii=False), encoding="utf-8")
    return list(frame.values())


def fetch_wikidata(qids, props="claims|sitelinks/urls|labels", batch=50):
    out = {}
    qids = [q for q in dict.fromkeys(qids) if q]
    for i in range(0, len(qids), batch):
        r = get(WD, {"action": "wbgetentities", "ids": "|".join(qids[i:i + batch]), "props": props, "languages": "en",
                     "sitefilter": "enwiki", "format": "json"}, min_interval=2.0)
        out.update(r.get("entities", {}))
    return out


def fetch_wikitext(titles, batch=40):
    out = {}
    for i in range(0, len(titles), batch):
        r = get(W, {"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main", "rvsection": 0,
                    "titles": "|".join(titles[i:i + batch]), "format": "json", "redirects": 1}, min_interval=2.5)
        for p in r["query"]["pages"].values():
            if "revisions" in p:
                out[p["title"]] = p["revisions"][0]["slots"]["main"]["*"]
    return out


def main():
    frame = build_frame()
    ent = fetch_wikidata([f["qid"] for f in frame])
    (RAW / "wikidata_titles.json").write_text(json.dumps(ent, ensure_ascii=False), encoding="utf-8")
    txt = fetch_wikitext([f["title"] for f in frame])
    (RAW / "wikitext_section0.json").write_text(json.dumps(txt, ensure_ascii=False), encoding="utf-8")
    print(len(frame), "frame titles;", len(ent), "wikidata entities;", len(txt), "infobox texts")


if __name__ == "__main__":
    main()
