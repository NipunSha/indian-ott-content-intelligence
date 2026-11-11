# Decisions log
| Date | Decision | Reason |
|---|---|---|
| 2026-11-11 | Frame from Wikipedia platform-original categories rather than Wikidata platform links | Wikidata had 20-66 Indian titles per platform; categories gave 1,083 |
| 2026-11-11 | Wikipedia pageviews as demand proxy instead of Google Trends | Official API, CC0, daily history for every title |
| 2026-11-11 | Exclude titles whose article did not exist at release | Launch window would be undercounted |
| 2026-11-11 | Series dated at first premiere; seasons not separate rows | Consistent unit; avoids duplicate titles |
| 2026-11-11 | Voot and Disney+ Hotstar grouped as JioHotstar | Successor service after the 2023 and 2025 mergers |
| 2026-11-11 | IMDb: ratings file only, via Wikidata IMDb ids | Disk limit; avoids 750 MB of basics/akas dumps |
| 2026-11-11 | IMDb and Netflix data kept local | Licence does not permit redistribution |
| 2026-11-11 | No YouTube trailer metrics | Present-day view counts are not historical; API key not available at build time |
| 2026-11-11 | No clustering | Segments of interest already explicit; categorical features |
| 2026-11-11 | Requests identify the author via WIKIMEDIA_CONTACT env variable | Wikimedia limits anonymous clients to 10 requests/minute |
| 2026-11-11 | After independent review: primary genre and language now follow text order; sequel flag restricted to pre-release information; unscripted and no-genre titles excluded; non-Indian titles in platform categories excluded; evidence grades lowered; SQL comments corrected | Reviewer findings 1-9; headline results changed (crime-specific premium replaced by a drama deficit) |
