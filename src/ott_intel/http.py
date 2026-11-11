"""Polite HTTP client: identifies itself, throttles, caches raw responses on disk, backs off on 429."""
import hashlib, json, os, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "raw" / "http_cache"
# Wikimedia allows ~10 requests/minute without contact details and ~200/minute with a compliant
# User-Agent. Set WIKIMEDIA_CONTACT (a URL or email) in the environment to identify yourself.
CONTACT = os.environ.get("WIKIMEDIA_CONTACT", "").strip()
UA = f"IndianOTTContentIntelligence/0.1 ({CONTACT}) python-requests" if CONTACT else "IndianOTTContentIntelligence/0.1 (portfolio research project; python-requests)"
WIKIMEDIA_MIN_INTERVAL = 0.5 if CONTACT else 6.5
_last = {}


def get(url, params=None, min_interval=1.5, as_json=True, retries=6):
    key = hashlib.sha1((url + json.dumps(params or {}, sort_keys=True)).encode()).hexdigest()
    f = CACHE / f"{key}.{'json' if as_json else 'txt'}"
    if f.exists():
        t = f.read_text(encoding="utf-8")
        return json.loads(t) if as_json else t
    host = url.split("/")[2]
    if any(h in host for h in ("wikimedia.org", "wikipedia.org", "wikidata.org")):
        host, min_interval = "wikimedia", max(min_interval if CONTACT else 0, WIKIMEDIA_MIN_INTERVAL)
    for i in range(retries):
        wait = min_interval - (time.time() - _last.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        r = requests.get(url, params=params, headers={"User-Agent": UA, "Accept-Encoding": "gzip"}, timeout=60)
        _last[host] = time.time()
        if r.status_code == 200:
            CACHE.mkdir(parents=True, exist_ok=True)
            f.write_text(r.text, encoding="utf-8")
            return r.json() if as_json else r.text
        if r.status_code == 404:
            return None
        time.sleep(min(float(r.headers.get("retry-after", 5 * (i + 1))), 120))
    raise RuntimeError(f"Failed after {retries} tries: {url} ({r.status_code})")
