"""Step 4: turn raw frame + infobox + Wikidata into data/processed/titles_stage.csv (one row per title)."""
import json, re
import pandas as pd
from .http import ROOT
from . import parse as P
from .collect_frame import fetch_wikidata

RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"
PLATFORM_PRIORITY = ["Netflix", "Amazon Prime Video", "JioHotstar", "SonyLIV", "ZEE5", "Aha", "ALTT", "MX Player", "Hoichoi", "TVF Play", "ETV Win"]


def main():
    frame = json.load(open(RAW / "frame.json", encoding="utf-8"))
    ent = json.load(open(RAW / "wikidata_titles.json", encoding="utf-8"))
    txt = json.load(open(RAW / "wikitext_section0.json", encoding="utf-8"))
    rows, need_labels = [], set()
    for f in frame:
        e = ent.get(f["qid"] or "", {})
        t = txt.get(f["title"], "")
        ib = P.infobox(t)
        lead = P.lead_sentence(t)
        # Titles from platform-wide categories must be Indian by Wikidata or infobox country (first country listed);
        # the lead sentence alone is not enough (foreign productions set in India would pass).
        ib_country = P.strip_markup(ib.get("country", "")).lower().strip()
        wd_country = P.wd_ids(e, "P495")
        strict = (wd_country[:1] == ["Q668"]) or ib_country.startswith("india")
        foreign = bool(ib_country) and "india" not in ib_country and "Q668" not in wd_country  # e.g. Pakistani ZEE5 originals
        india = strict or (not f["needs_india_filter"] and not foreign and (("Q668" in wd_country) or "india" in ib_country or bool(re.search(r"\bIndian\b", lead))))
        is_title = any(k in ib.get("_type", "") for k in ("television", "film", "web series", "tv "))
        rel_ib = P.parse_date(ib.get("released") or ib.get("first_aired") or ib.get("release_date") or "")
        rel_wd = P.wd_date(e)
        langs = P.languages(P.strip_markup(ib.get("language", "")), lead)
        gens = P.genres(P.strip_markup(ib.get("genre", "")), lead)
        if re.search(r"\b(reality|documentary|docu-?series|talk show|game show|stand-up|competition (?:show|series)|sketch comedy)\b", lead + " " + P.strip_markup(ib.get("genre", "")), re.I):
            gens = ["Unscripted"] + [g for g in gens if g != "Unscripted"]
        fmt = "film" if "film" in ib.get("_type", "") else ("series" if is_title else f["format_hint"])
        cast = P.listify(ib.get("starring", ""), limit=8)
        comp = P.listify(ib.get("company") or ib.get("production_companies") or ib.get("production_company") or ib.get("studio") or "", limit=4)
        direc = P.listify(ib.get("director") or ib.get("creator") or "", limit=3)
        # Sequel / spin-off / remake of an EARLIER work only: fields that can be known before release.
        # ("related", "followed_by" and Wikidata "part of series" are excluded: they are filled in after later instalments exist.)
        seq_text = " ".join(ib.get(k, "") for k in ("preceded_by", "prequel"))
        franchise = bool(P.wd_ids(e, "P155") or P.strip_markup(seq_text).strip()
                         or re.search(r"\b(2|3|II|III|Returns|Reloaded|Chapter \d)\b", f["title"]) or re.search(r"\b(sequel|spin-off|second instal|third instal|remake|reboot)\b", lead, re.I))
        wd_g, wd_l, wd_c = P.wd_ids(e, "P136"), P.wd_ids(e, "P364") + P.wd_ids(e, "P407"), P.wd_ids(e, "P272")
        need_labels.update(wd_g + wd_l + wd_c)
        rows.append({
            "wiki_title": f["title"], "pageid": f["pageid"], "qid": f["qid"], "imdb_id": P.wd_str(e, "P345"),
            "platform": next(p for p in PLATFORM_PRIORITY if p in f["platforms"]), "all_platforms": "; ".join(f["platforms"]),
            "source_categories": "; ".join(f["categories"]), "format": fmt, "infobox_type": ib.get("_type"), "is_title_page": is_title, "is_indian": india,
            "release_date_infobox": rel_ib, "release_date_wikidata": rel_wd, "languages_text": "; ".join(langs), "genres_text": "; ".join(gens),
            "genre_raw": P.strip_markup(ib.get("genre", ""))[:200], "wd_genres": wd_g, "wd_langs": wd_l, "wd_companies": wd_c,
            "num_seasons": P.first_int(ib.get("num_seasons")), "num_episodes": P.first_int(ib.get("num_episodes")), "runtime_min": P.first_int(ib.get("runtime")),
            "cast_list": cast, "production_companies_infobox": comp, "directors_creators": direc,
            "is_adaptation": bool(P.strip_markup(ib.get("based_on", "")).strip()), "is_franchise_or_sequel": franchise, "lead_sentence": lead[:300],
        })
    labels = {q: v.get("labels", {}).get("en", {}).get("value") for q, v in fetch_wikidata(sorted(need_labels), props="labels").items()}
    (RAW / "wikidata_labels.json").write_text(json.dumps(labels, ensure_ascii=False), encoding="utf-8")
    df = pd.DataFrame(rows)
    lab = lambda ids: "; ".join(dict.fromkeys(labels.get(i) for i in ids if labels.get(i)))
    df["wd_genres"] = df.wd_genres.map(lab); df["wd_langs"] = df.wd_langs.map(lab); df["wd_companies"] = df.wd_companies.map(lab)
    # fill gaps from Wikidata labels
    df["languages"] = [a or "; ".join(P.languages(b)) for a, b in zip(df.languages_text, df.wd_langs)]
    df["genres"] = [a or "; ".join(P.genres(b)) for a, b in zip(df.genres_text, df.wd_genres)]
    df["release_date"] = df.release_date_infobox.fillna(df.release_date_wikidata)
    df["release_date_source"] = ["infobox" if pd.notna(a) else ("wikidata" if pd.notna(b) else None) for a, b in zip(df.release_date_infobox, df.release_date_wikidata)]
    for c in ("cast_list", "production_companies_infobox", "directors_creators"):
        df[c] = df[c].map("; ".join)
    df["production_companies"] = [a or b for a, b in zip(df.production_companies_infobox, df.wd_companies)]
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "titles_stage.csv", index=False)
    return df


if __name__ == "__main__":
    d = main()
    k = d[d.is_indian & d.is_title_page]
    print(len(d), "candidates ->", len(k), "Indian title pages")
    print(k.platform.value_counts().to_dict()); print(k.format.value_counts().to_dict())
    print("release date present:", k.release_date.notna().mean().round(3), "| language:", (k.languages != "").mean().round(3), "| genre:", (k.genres != "").mean().round(3), "| cast:", (k.cast_list != "").mean().round(3), "| imdb:", k.imdb_id.notna().mean().round(3), "| company:", (k.production_companies != "").mean().round(3))
    print(pd.to_datetime(k.release_date).dt.year.value_counts().sort_index().to_dict())
    print(k.sample(6, random_state=1)[["wiki_title", "platform", "format", "release_date", "languages", "genres", "cast_list"]].to_string())
