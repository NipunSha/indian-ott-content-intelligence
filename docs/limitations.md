# Limitations
1. **Proxy, not viewership.** Wikipedia pageviews measure curiosity among English-reading internet users. They over-represent Hindi and pan-India titles and under-represent regional-language audiences; cross-language level comparisons are flagged throughout and the opportunity analysis indexes within language.
2. **Coverage bias.** A title is in the frame only if it has an English-Wikipedia article in a platform-originals category, and in the analysis only if the article existed by release day. Low-profile titles are under-represented, so results describe the documented part of each platform's slate.
3. **Platform comparisons are not audience comparisons.** Platforms differ in how completely Wikipedia documents them.
4. **Parsed metadata.** Genre and language come from free-text infoboxes; misclassification is possible. Page renames can split pageviews across titles.
5. **Films.** "Original films" categories mostly hold direct-to-streaming releases but can include theatrical titles whose streaming rights were acquired; their release date may be theatrical.
6. **Present-day fields.** Season and episode counts are current values and are not used as predictors.
7. **Selection into the model test.** The article-at-release rule is only known after greenlight, so the \"greenlight\" model is evaluated on titles that went on to be documented; real-world performance on a full slate would be lower. Standard errors are not clustered by production house, and the production-house track-record feature grows mechanically over time.
8. **Events.** Attention can spike for reasons unrelated to demand for the title (for example a lead actor's death).
9. **No causal claims.** Regression coefficients and model importances are associations.
10. **Restricted sources.** IMDb and Netflix Top 10 files are used locally for validation only and are not in the repository.
11. **No Tableau workbook** has been built; `tableau/` holds data and a specification.
