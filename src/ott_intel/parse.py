"""Parse Wikipedia infobox wikitext and Wikidata claims into flat title attributes."""
import re
from datetime import date

MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"], 1)}
INDIAN_LANGS = ["Hindi", "Tamil", "Telugu", "Malayalam", "Kannada", "Bengali", "Marathi", "Punjabi", "Gujarati", "Odia", "Assamese", "Bhojpuri", "Urdu", "English"]
GENRE_MAP = [  # ordered: first match wins for primary genre
    ("crime", "Crime"), ("thriller", "Thriller"), ("mystery", "Thriller"), ("horror", "Horror"), ("romantic comedy", "Romance"), ("romance", "Romance"), ("romantic", "Romance"),
    ("comedy", "Comedy"), ("sitcom", "Comedy"), ("action", "Action"), ("political", "Drama"), ("legal", "Drama"), ("medical", "Drama"), ("sports", "Drama"),
    ("biograph", "Biographical"), ("histor", "Historical"), ("period", "Historical"), ("fantasy", "Fantasy/Sci-fi"), ("science fiction", "Fantasy/Sci-fi"), ("sci-fi", "Fantasy/Sci-fi"), ("supernatural", "Horror"),
    ("family", "Drama"), ("anthology", "Drama"), ("drama", "Drama"), ("documentar", "Documentary"), ("docu", "Documentary"), ("reality", "Unscripted"), ("talk show", "Unscripted"),
    ("game show", "Unscripted"), ("stand-up", "Unscripted"), ("animat", "Animation"), ("erotic", "Drama"), ("adventure", "Action"), ("war", "Action"), ("spy", "Thriller"), ("heist", "Crime"),
]
UNSCRIPTED = {"Documentary", "Unscripted"}


def infobox(text):
    """Return {field: raw value} for the first infobox in section-0 wikitext."""
    m = re.search(r"\{\{\s*Infobox", text or "", re.I)
    if not m:
        return {}
    i, depth, start = m.start(), 0, m.start()
    while i < len(text):
        if text.startswith("{{", i): depth += 1; i += 2; continue
        if text.startswith("}}", i):
            depth -= 1; i += 2
            if depth == 0: break
            continue
        i += 1
    body = text[start:i]
    # split on top-level pipes
    parts, buf, d1, d2 = [], "", 0, 0
    j = 0
    while j < len(body):
        two = body[j:j + 2]
        if two == "{{": d1 += 1; buf += two; j += 2; continue
        if two == "}}": d1 -= 1; buf += two; j += 2; continue
        if two == "[[": d2 += 1; buf += two; j += 2; continue
        if two == "]]": d2 -= 1; buf += two; j += 2; continue
        if body[j] == "|" and d1 == 1 and d2 == 0: parts.append(buf); buf = ""; j += 1; continue
        buf += body[j]; j += 1
    parts.append(buf)
    out = {"_type": re.sub(r"\s+", " ", parts[0].replace("{{", "").strip().lower())}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip().lower()] = v.strip().rstrip("}").strip() if v.strip().endswith("}}") and v.count("{{") < v.count("}}") else v.strip()
    return out


def strip_markup(v):
    v = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>", "", v or "", flags=re.S)
    v = re.sub(r"<!--.*?-->", "", v, flags=re.S)
    v = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", v)
    v = re.sub(r"\{\{(?:nowrap|small|nobr)\|([^{}]*)\}\}", r"\1", v, flags=re.I)
    v = re.sub(r"<br\s*/?>", "; ", v, flags=re.I)
    v = re.sub(r"<[^>]+>", "", v)
    return v


def listify(v, limit=None):
    """Ordered list of names from a starring / company style field."""
    v = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>", "", v or "", flags=re.S)
    v = re.sub(r"<!--.*?-->", "", v, flags=re.S)
    links = re.findall(r"\[\[([^\]|#]+)(?:\|[^\]]*)?\]\]", v)
    if links:
        items = [l.strip() for l in links if not l.lower().startswith(("file:", "image:", "category:"))]
    else:
        t = re.sub(r"\{\{\s*(?:plainlist|ubl|unbulleted list|hlist|flatlist|plain list)\s*\|?", "", v, flags=re.I).replace("}}", "")
        items = [x.strip(" *'") for x in re.split(r"<br\s*/?>|\n|\*|\||;", t) if x.strip(" *'")]
    items = [x for x in dict.fromkeys(items) if x and len(x) < 60]
    return items[:limit] if limit else items


def parse_date(v):
    """First date found in a release field -> ISO string (day precision only), else None."""
    if not v: return None
    m = re.search(r"\{\{\s*(?:start date|film date|start date and age|release date)[^}]*\}\}", v, re.I)
    if m:
        nums = [int(x) for x in re.findall(r"\|\s*(\d{1,4})\s*(?=\||\})", m.group(0))]
        if len(nums) >= 3 and nums[0] > 1900:
            try: return date(nums[0], nums[1], nums[2]).isoformat()
            except ValueError: pass
    t = strip_markup(v)
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", t)
    if m and m.group(2).lower() in MONTHS:
        try: return date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))).isoformat()
        except ValueError: pass
    m = re.search(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", t)
    if m and m.group(1).lower() in MONTHS:
        try: return date(int(m.group(3)), MONTHS[m.group(1).lower()], int(m.group(2))).isoformat()
        except ValueError: pass
    return None


def first_int(v):
    m = re.search(r"\d+", strip_markup(v or "").replace(",", ""))
    return int(m.group(0)) if m else None


def lead_sentence(text):
    t = re.sub(r"\{\{[^{}]*\}\}", "", text or "")
    for _ in range(4): t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = strip_markup(t)
    m = re.search(r"'''.{1,120}?'''[^\n]{0,400}", t)
    return m.group(0) if m else ""


def _ordered_matches(text, pairs):
    """Labels whose keyword occurs in `text`, ordered by where they first appear (ties: list order)."""
    low = (text or "").lower()
    hits = []
    for rank, (k, label) in enumerate(pairs):
        m = re.search(r"\b" + re.escape(k.lower()), low)
        if m: hits.append((m.start(), rank, label))
    return list(dict.fromkeys(label for _, _, label in sorted(hits)))


def languages(*texts):
    """Languages in the order the text lists them; the first text with any match is used."""
    for t in texts:
        found = _ordered_matches(t, [(l, l) for l in INDIAN_LANGS])
        if found: return found
    return []


def genres(*texts):
    """Genre groups in the order the text lists them (primary genre = first listed)."""
    for t in texts:
        out = _ordered_matches(t, GENRE_MAP)
        if out: return out
    return []


def wd_ids(ent, prop):
    return [c["mainsnak"]["datavalue"]["value"]["id"] for c in ent.get("claims", {}).get(prop, []) if c["mainsnak"].get("datavalue") and isinstance(c["mainsnak"]["datavalue"]["value"], dict) and "id" in c["mainsnak"]["datavalue"]["value"]]


def wd_date(ent, props=("P577", "P580")):
    best = None
    for p in props:
        for c in ent.get("claims", {}).get(p, []):
            dv = c["mainsnak"].get("datavalue")
            if dv and dv["value"].get("precision", 0) >= 11:
                d = dv["value"]["time"][1:11]
                if best is None or d < best: best = d
    return best


def wd_str(ent, prop):
    for c in ent.get("claims", {}).get(prop, []):
        dv = c["mainsnak"].get("datavalue")
        if dv and isinstance(dv["value"], str): return dv["value"]
    return None
