# mtcpts: net-harm comparison of manual traffic control, portable traffic signals and attended automated flagger devices at rural stop/go work zones

Code, configuration, tests and production outputs for *A Probabilistic Net-Harm Comparison of Manual Traffic Control, Portable Traffic Signals and Attended Automated Flagger Devices at Rural Stop/Go Work Zones* (Tilton and van der Walt, submitted to Transportation Research Record, 2026). The conference version (TRB Annual Meeting 2027, presentation only) used the same model without the attended device.

## What is here

- `model/src/mtcpts/`: the model. `cycle.py` (alternating one-lane control), `conflict.py` (the red-running event tree and the model-form alternatives), `pathways.py` (the harm pathways), `severity.py` (injury curves), `distributions.py` (priors and the expert-judgement mixtures), `model.py` (the per-cell Monte Carlo assembly, break-even and decision-surface outputs), `sensitivity.py` (partial rank correlation).
- `model/config/priors.toml`: every non-elicited prior with its evidence; `welfare-values.toml`: the monetary values; `sej_scenario_c_pooled.npz`: the pooled expert-judgement priors (see below).
- `model/scripts/`: `run_suite.py` (the guarded production run), `decision_outputs.py` and `decision_outputs_s2.py` (the comparisons at the recorded rates), `model_form_sensitivity.py`, `welfare.py`, `make_figures.py` (conference figures), `make_figures_v15.py` (the paper's Figures 3 to 8, from the saved draws), `make_figures_trr_v12.py` (Figure 1 and four supplement figures, from the saved outputs), `make_figures_trr.py` (three supplement figures), `make_influence_diagram.py` (the main and full influence diagrams), `export_pooled_priors.py` (how the pooled priors were made; it needs the restricted table, see below).
- `model/tests/`: the test suite (`python3 -m pytest model/tests`).
- `model/outputs/dist/capfix_20260927/`: the production run of 27 September 2026 (grid results, sensitivity, calibration curves, decision surfaces, record checks, model-form and welfare summaries), including the saved per-draw traces used by the figure scripts. The earlier run without the entry cap described below is in this repository's history.
- `docs/prespec.md` (the pre-registered design, decision rules and the addendum for the attended device), `docs/model-design.md`, `research/` (the evidence notes behind every prior and both record bands), `results/REGISTRY.md` (every number the paper quotes, with its source file).
- `docs/influence-diagram-edges.md`: the node and edge list for the main influence diagram and its full supplemental version, with links to the model code and the distinction between modelled links and the unmodelled delay-to-violation response.
- `research/trace/stats19_trace.py` and its `README.md` reproduce the Great Britain STATS19 roadworks head-on proxy for 2021 to 2025 from saved extracts: 50.6 injury collisions, 18.8 fatal or serious and 1.6 fatal per year; `research/traceability.md` documents the confirmed US count and the unresolved NZ frequency and national exposure estimates.

## Figures

The manuscript and supplement captions give the figure numbers. Image filenames keep their original identifiers.

| Script | Paper figures | Supplement figures |
|---|---|---|
| `model/scripts/make_figures_v15.py` | 3 (event tree, `fig_tree.png`), 4 (injury curves, `fig_injury_curves.png`), 5 (break-even maps, `fig3_decision_surface.png`), 6 (change against the margin, `fig_spread.png`), 7 (mutual sight, `fig9_sight.png`), 8 (speed sweep, `fig_speed_sweep.png`) | |
| `model/scripts/make_figures_trr_v12.py` | 1 (control layouts, `fig1_substitution.png`) | S4 (operator exposure, `fig6_device_exposure.png`), S5 (demand and length grid, `figS6_grid.png`), S7 (matching conventions, `fig4_calibration.png`), S8 (avoidance forms, `fig8_model_form.png`) |
| `model/scripts/make_influence_diagram.py` | 2 (grouped influence diagram, `fig_influence.png`) | S1 (full influence diagram, `fig_influence_full.png`) |
| `model/scripts/make_figures_trr.py` | | S2 (all-red rules, `fig_allred.png`), S3 (input sources, `fig_inputs.png`), S6 (pathway decomposition and sensitivity, `fig4_decomp_prcc.png`) |

`make_figures_v15.py` and `make_figures_trr_v12.py` read the saved production outputs and check plotted values against them without running the model. `make_influence_diagram.py` produces both PNG and SVG diagrams and the node and edge inventory published as `docs/influence-diagram-edges.md`.

## The expert-judgement priors

Four quantities (the queue-tail crash rate and severity, the controller-strike rate and severity) come from a structured expert-judgement panel (Tilton and van der Walt, 2026, companion study). The panel's individual responses were collected under an ethics approval that does not permit release. The paper's runs consumed a per-expert fitted table (one row per expert per quantity, equal-weight mixture, rate and severity coupled through the same expert draw); that table is not in this repository. In its place, `sej_scenario_c_pooled.npz` holds 400,000 coupled rows drawn from those mixtures, with no expert identifier and no per-expert parameter. The code detects which form is present (`distributions.load_sej`). With the pooled form the results reproduce the paper's within Monte Carlo tolerance (pinned by `model/tests/test_pooled_release.py`); with the restricted table they reproduce it bit for bit.

## Running

Python 3.11 or later with numpy, scipy and matplotlib (pytest for the tests). From the repository root:

```
python3 -m pytest model/tests            # structural identities, record checks, reproducibility
python3 model/scripts/run_suite.py       # the production suite (about 40 minutes); needs a git checkout for the pre-registration guard
python3 model/scripts/decision_outputs.py && python3 model/scripts/decision_outputs_s2.py
python3 model/scripts/model_form_sensitivity.py && python3 model/scripts/welfare.py
python3 model/scripts/make_figures_v15.py
python3 model/scripts/make_figures_trr.py
python3 model/scripts/make_figures_trr_v12.py
python3 model/scripts/make_influence_diagram.py
```

`run_suite.py` refuses to run unless `docs/prespec.md` was committed no later than `model/config/priors.toml`; in a fresh clone commit both files together before running.

## Licence

MIT (see `LICENSE`). Cite the paper when you use the model.

The per-form trace files behind `model_form_headline_reads.json` (about 18 MB each) are not included; `model/scripts/model_form_headline_reads.py` regenerates them from the same seed and draws.

On 27 September 2026 the red-running tree was corrected so that entries against red at any moment cannot exceed the vehicles able to enter; the excess is assigned to queue-lead departures and the measured violation total is unchanged. The correction was specified in `docs/prespec-addendum-2026-09-27-entry-cap.md` before the corrected run, whose outputs are in `model/outputs/dist/capfix_20260927/`.
