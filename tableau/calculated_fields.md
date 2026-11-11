# Calculated fields
| Name | Source | Formula | Purpose |
|---|---|---|---|
| Launch views (log10) | titles_tableau | `LOG([views_d0_27])` | Axis for skewed data |
| Median launch views | titles_tableau | `MEDIAN([views_d0_27])` | Default aggregate |
| N titles | titles_tableau | `COUNTD([title_id])` | Label and small-cell filter |
| Show cell | titles_tableau | `[N titles] >= 5` | Hide thin cells |
| Strong launch rate | titles_tableau | `AVG([strong_launch])` | Share at or above the 2018-2023 75th percentile |
| Within-language percentile (median) | titles_tableau | `MEDIAN([pct_within_language])` | Language-neutral comparison |
| Pre-release share | titles_tableau | `SUM([views_pre_30d]) / (SUM([views_pre_30d]) + SUM([views_d0_27]))` | Anticipation vs launch |
| CI whisker low / high | opportunity_cells | `[index_ci_low]`, `[index_ci_high]` | Reference lines |
| Opportunity colour | opportunity_cells | `IF [flag] = '' THEN 'No clear signal' ELSE [flag] END` | Colour |
| Multiplier label | ols_coefficients | `STR(ROUND([multiplier],2)) + 'x'` | Coefficient plot label |
