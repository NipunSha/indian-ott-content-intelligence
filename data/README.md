# Data
- `raw/` is not in the repository (git-ignored). It holds API response caches and two downloaded files whose licences do not allow redistribution (IMDb ratings, Netflix Top 10). Recreate it with the collectors listed in the main README.
- `processed/titles.csv` and `processed/ott_observatory.sqlite` contain only fields derived from Wikipedia (CC BY-SA 4.0), Wikidata (CC0) and Wikimedia pageviews (CC0). Attribution: Wikipedia contributors; retrieved 2026-11-11. These derived data are shared under CC BY-SA 4.0.
- `processed/restricted/` (git-ignored) joins IMDb and Netflix fields for local validation.
