"""Build reports/executive_presentation.pptx. Figures come from reports/figures; key numbers are read from tableau/data."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pandas as pd
from deck_helper import Deck

D, F = ROOT / "tableau" / "data", ROOT / "reports" / "figures"
R = json.load(open(D / "run_summary.json")); co = pd.read_csv(D / "ols_coefficients.csv").set_index("term"); perf = pd.read_csv(D / "model_performance.csv"); base = pd.read_csv(D / "model_baselines.csv").set_index("check")
val = pd.read_csv(D / "proxy_validation.csv"); opp = pd.read_csv(D / "opportunity_cells.csv").set_index(["primary_language", "primary_genre"]); gs = pd.read_csv(D / "group_stats.csv").set_index(["dimension", "level"])
def mult(term): r = co.loc[term]; return f"{r.multiplier:.2f}x (CI {r.mult_low:.2f}-{r.mult_high:.2f})"
def cell(l, g): r = opp.loc[(l, g)]; return f"{r.demand_index:.2f}x the {l} median (CI {r.index_ci_low:.2f}-{r.index_ci_high:.2f}), {r.supply_share:.0%} of supply"
gl = perf[(perf.stage == "greenlight") & (perf.model == "logit")].iloc[0]
d = Deck("Indian OTT Content Intelligence Observatory  |  Launch attention = Wikipedia pageviews, days 0-27: a proxy, not viewership")
d.title("What distinguishes Indian streaming originals that launch to strong public attention?", f"{R['n_titles']:,} originals across eleven services, 2018-2026; launch attention measured for {R['n_sample']} scripted titles. Attention is English-Wikipedia pageviews in the 28 days from release: public interest, not viewing.")
G = lambda g: chr(67) + "(primary_genre, Treatment('Drama'))[T." + g + "]"
d.bullets("A title billed first as drama starts at a disadvantage; sequels buy nothing", [
    f"Versus drama, other things equal: action {mult(G('Action'))}, horror {mult(G('Horror'))}, crime {mult(G('Crime'))}.",
    f"Lead-cast prominence: {mult('log_cast_prom')} per tenfold increase in prior-year pageviews.",
    f"Sequels, spin-offs and remakes: {mult('is_franchise_or_sequel')}, no detectable association.",
    f"Tamil versus Hindi: {mult(chr(67) + '(primary_language, Treatment(' + repr('Hindi') + '))[T.Tamil]')}, not distinguishable.",
    f"Hindi drama is over-supplied: {cell('Hindi', 'Drama')}."])
d.table("The proxy measures who went looking, not how long they watched", ["Validation check", "n", "Spearman rho", "p"], [[r.check[:78], int(r.n), "" if pd.isna(r.spearman_rho) else f"{r.spearman_rho:.2f}", f"{r.p_value:.3f}"] for r in val.itertuples()],
        note="Strong agreement with IMDb vote counts, none with IMDb rating, and none with weeks in Netflix's India Top 10. IMDb and Netflix data were used locally and are not redistributed.", col_widths=[7.6, 1.0, 1.7, 1.5])
d.picture("Attention differs sharply by language, and the proxy is part of the reason", F / "language.png", [
    f"Median launch attention: Hindi {gs.loc[('primary_language','Hindi')].median_views:,.0f}, Malayalam {gs.loc[('primary_language','Malayalam')].median_views:,.0f}, Tamil {gs.loc[('primary_language','Tamil')].median_views:,.0f}, Telugu {gs.loc[('primary_language','Telugu')].median_views:,.0f}.",
    "English Wikipedia under-counts regional-language audiences.", "Comparisons below are made within language."])
d.picture("After controls: action, horror, crime and cast prominence stand out", F / "ols.png", [
    f"Model explains {R['ols_r2']:.0%} of the variance in log launch attention (n = {R['ols_n']}).", "Platform gaps reflect audience mix and Wikipedia coverage, not commissioning quality.", "Associations, not causal effects."])
d.table("A strong launch is predictable before release, mostly from platform and genre", ["Check (test set: 2024-2026 releases)", "ROC AUC"], [
    ["Greenlight logistic model, all pre-release features", f"{gl.roc_auc:.2f} (CI {gl.auc_ci_low:.2f}-{gl.auc_ci_high:.2f})"],
    ["Platform base rates only", f"{base.loc['platform base rates only'].roc_auc:.2f}"], ["Same model without platform", f"{base.loc['greenlight logit without platform'].roc_auc:.2f}"],
    ["Within Netflix titles only (n = 30)", f"{base.loc['greenlight logit, within Netflix only'].roc_auc:.2f}"]],
    note=f"Strong launch = top quartile of 2018-2023 launches ({R['threshold_views']:,.0f} pageviews). {int(gl.n_test)} test titles, {gl.test_prevalence:.0%} strong. Top-scored fifth of titles: {gl.precision_top20pct:.0%} were strong launches. Use as a screen, not a viewing forecast.", col_widths=[8.3, 3.5])
d.picture("Hindi drama is over-supplied; Hindi action is thinly supplied", F / "opportunity.png", [
    f"Hindi drama: {cell('Hindi', 'Drama')}.", f"Hindi action: {cell('Hindi', 'Action')}.", "23 cells compared: only the Hindi drama result survives a multiple-comparison correction."])
d.bullets("Three opportunity briefs, graded by evidence", [
    "Strong: reallocate Hindi drama slots to projects with a sharper genre frame, known cast or event hook.",
    "Moderate: Hindi action, thinly supplied with above-median launch attention on two cuts of the data.",
    "Suggestive: Tamil features for national platforms; no detectable gap to Hindi, but wide intervals."],
    note="Details and risks: reports/content_opportunity_briefs.md")
d.bullets("What this cannot tell you", [
    "Viewing, completion or subscriber impact: no platform publishes comparable figures.",
    f"Anything about the {R['n_scripted'] - R['n_sample']} scripted titles whose Wikipedia page did not exist at release.",
    "Whether the fall in launch attention since 2023 is demand or declining Wikipedia use.",
    "Causes. Every result here is an association."])
print(d.save(ROOT / "reports" / "executive_presentation.pptx"))
