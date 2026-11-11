# Indian OTT Content Intelligence Observatory: executive report

*Data retrieved 11 November 2026. "Launch attention" means English-Wikipedia pageviews of a title's article in the 28 days from release. It is a proxy for public interest. It is not viewership, it favours titles with English-reading audiences, and it can only be measured for titles that already had a Wikipedia article on release day.*

## What was built
A relational database of 998 Indian streaming originals released between January 2018 and October 2026 across eleven services, of which 920 are classified as scripted. Launch attention can be measured for 502 of them. Measurement coverage is uneven (Netflix 84%, Prime Video 68%, ZEE5 57%, JioHotstar 56%, SonyLIV 48%, Aha 18%, Hoichoi 10%), so everything below describes the better-documented, more anticipated part of each slate.

## Does the proxy mean anything?
Partly. Launch attention tracks IMDb vote counts closely (Spearman 0.71, n = 466) and is unrelated to IMDb rating (0.08), which is what an attention measure should do. It does **not** reliably track how long a Netflix title stays in Netflix's own India Top 10 (0.12, n = 54, p = 0.38; charted titles have a higher median, 370,000 against 203,000, p = 0.07). Read it as a measure of how many people went looking for a title at launch, not of how long they watched. Single events can distort it: one of the highest values belongs to a film released weeks after its lead actor's death.

## Findings

**1. Attention is concentrated.** The median measured title drew 89,000 pageviews in its first 28 days; the top tenth drew 527,000 or more and accounts for 42% of all launch pageviews.

**2. Titles billed first as "drama" draw the least attention.** Genre is the first one listed in a title's infobox or lead sentence. With platform, language, format, cast and year held constant, action titles draw 2.4 times the launch attention of dramas (95% CI 1.5–3.8), horror 2.2 times (1.3–3.5), crime 2.0 times (1.2–3.4) and romance 1.6 times (1.0–2.6). Thriller (1.3) and comedy (1.2) are not distinguishable from drama. The useful reading is not that one genre wins but that a title described first as a drama, with no sharper label, starts at a disadvantage.

**3. Films open bigger; series last longer.** Direct-to-streaming films have a median of 180,000 against 41,000 for series, in every language measured. After controls the gap narrows to 0.74 times for series and is no longer statistically clear (CI 0.50–1.11): films sit disproportionately on the platforms and in the genres that draw attention. Series hold attention longer: for Hindi, days 28–89 add 52% of the launch total for series against 34% for films.

**4. Tamil is not distinguishable from Hindi once platform and genre are accounted for.** The Tamil coefficient is 0.93 times Hindi (CI 0.63–1.38), so the data are consistent with anything from a third lower to a third higher. Telugu (0.36) and Bengali (0.20) are far lower, and an English-language encyclopaedia is part of the reason; those gaps should not be read as audience size.

**5. Star power is measurable; sequels show nothing.** A tenfold increase in the lead cast's prior-year pageviews goes with 1.35 times the launch attention (CI 1.10–1.64). Sequels, spin-offs and remakes have a higher raw median (148,000 against 87,000, 54 titles) but no association after controls (0.77, CI 0.38–1.54).

**6. Platform is the biggest single divider.** Relative to Netflix, comparable titles on JioHotstar draw 0.44 times the attention, SonyLIV 0.32 and ZEE5 0.23; Prime Video is not distinguishable from Netflix (0.87, CI 0.56–1.35). This reflects each service's audience mix and how well Wikipedia covers it, not the quality of its commissioning.

**7. Launch attention has fallen since 2023.** The median was 147,000, 184,000 and 161,000 for 2020, 2021 and 2023 releases (103,000 in 2022) and 58,000, 44,000 and 28,000 for 2024, 2025 and 2026. These data cannot say whether that is thinner demand per title or a general decline in Wikipedia use.

## Can a strong launch be predicted before release?
A "strong launch" is defined as reaching the 75th percentile of 2018–2023 launches (315,600 pageviews). Models were trained on 2018–2023 and tested on 156 releases from 2024–2026, of which 25 were strong.

| Information set | Model | ROC AUC (95% CI) | Strong launches among top-scored 20% | Base rate in test |
|---|---|---|---|---|
| Greenlight (platform, language, genre, format, cast, flags) | Logistic | 0.84 (0.77–0.91) | 42% | 16% |
| Greenlight | Gradient boosting | 0.87 (0.78–0.94) | 55% | 16% |
| Launch eve (adds pre-release pageviews) | Logistic | 0.84 (0.74–0.93) | 58% | 16% |
| Launch eve | Gradient boosting | 0.88 (0.79–0.95) | 52% | 16% |

The headline number flatters the model. Platform base rates alone give an AUC of 0.75 and the model without platform reaches 0.81. Inside Netflix, where 19 of the 25 strong launches sit, the AUC is 0.63 on 30 titles: the model separates services and genres far better than it separates titles within a service. Intervals are wide, the two model families overlap, and the test set only contains titles that went on to have a Wikipedia page by release. It is a screen for which titles are likely to need marketing support, not a forecast.

## Supply versus attention
Within each language, each genre's median launch attention was compared with the language median for releases since 2020, across 23 language–genre combinations with at least six titles. With that many comparisons, one or two would cross a 5% threshold by chance, so only the strongest result should be treated as established.

- **Hindi drama is over-supplied relative to attention:** 53 of 247 measured Hindi releases (21%) at 0.30 times the Hindi median (CI 0.16–0.69, p < 0.001). The since-2023 cut agrees (0.21, CI 0.12–0.89).
- **Hindi action meets the pre-set "under-supplied" bar:** 21 titles (9% of supply) at 1.51 times the Hindi median (CI 1.05–3.79, p = 0.016). It would not survive a correction for 23 comparisons on its own, but it agrees with the cross-language regression (action 2.4 times drama).
- **Tentative:** Tamil comedy at 0.22 times the Tamil median on nine titles (CI 0.06–0.97); Malayalam crime at 2.7 times on eight (CI 0.43–7.36).

## What a content team could do with this
- Treat a Hindi drama without a sharper genre frame as the slot needing the most justification.
- Look at Hindi action as a thinly supplied genre with above-median launch attention.
- Plan films to open a window and series to hold it; do not assume a film format by itself raises attention.
- Do not pay a premium for a sequel on the expectation of launch attention alone.
- Use the greenlight model to rank titles for marketing support across a slate, not to forecast viewing.

Limitations are listed in `docs/limitations.md`.
