# Funding the runners-up beats a golden ticket

Analysis code, aggregate results, and the **iclr-golden-ticket, 2017–2024 dataset**
for comparing score-based allocation rules among rejected submissions to the
International Conference on Learning Representations (ICLR).

The analyses compare minority-support ranking, panel-mean ranking, highest-score
ranking, score-variance ranking, and a lottery benchmark. Citation outcomes are
within-edition percentiles from a fixed OpenAlex reference-graph snapshot dated
June 26, 2026. These are retrospective comparisons of selection rules, not estimates
of the causal effect of receiving funding.

## Repository contents

| Directory | Contents |
|---|---|
| `analysis/` | Ranking and matched-comparison analyses; release validation |
| `data/` | Versioned submission, linkage, citation, and frozen analysis tables |
| `results/` | Frozen aggregate estimates and sensitivity results |
| `figures/` | Scripts for the quantitative results figures |
| `licenses/` | Upstream license and attribution notices |

The dataset contains **24,476 submission records** across eight editions: 24,450
original source records and 26 recovered records. It includes 2020. The main analysis
retains its original exclusion of 2020; a separate sensitivity analysis includes it.
The 26 recovered records do not enter the statistical analyses.

External bibliographic identity is resolved for **19,864 records (81.2%)**; usable
citation records are available for **18,657 (76.2%)**. These are separate measures.
Unresolved records remain missing, and unobserved citation outcomes are not zeros.
The dataset represents accessible source records rather than a verified census of
all submissions. See the [dataset description](data/README.md) for coverage by
edition, field definitions, and reuse terms.

## Installation

Python 3.12 or newer is recommended. Install the pinned analysis dependencies in an
isolated environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

NumPy and pandas implement the analyses; PyArrow reads the distributed Parquet
tables; Matplotlib renders the figures. All commands run locally from the repository
root using the supplied data. No API credentials are required.

## Reproduce the analyses

```bash
python analysis/validate.py
python analysis/ranking.py
python analysis/ranking.py --window 3
python analysis/matching.py
python analysis/matching.py --caliper 0.25
python analysis/ranking.py --include-2020
python analysis/ranking.py --window 3 --include-2020
python analysis/validate.py --results
```

`ranking.py` uses 2,000 within-edition bootstrap resamples with seed 20260915 and
budgets of 1%, 2%, 5%, and 10% of each edition's accepted count, rounded up. Rules are
ranked among all eligible rejections before restricting outcome averages to observed
citations. The lottery is the expectation over the same rejected pool. Three explicit
missing-outcome assignments are reported separately. Minority-support coefficients
remain fixed; the adjusted highest-score regression is refitted in each resample.

`matching.py` matches on edition, reviewer count, and panel mean, one-to-one without
replacement. The default requires identical means; `--caliper 0.25` reproduces the
supplementary analysis allowing a difference of at most 0.25 raw score points.
Intervals resample the fixed pairs. This is not propensity-score matching.

Outputs are written to `output/`; the reference tables in `results/` are never
overwritten. The validation command checks the core reproduced tables against the
frozen references with a numeric tolerance of 1e-9. For the nested two-year samples,
run `python analysis/ranking.py --through 2022` or `--through 2023`.

## Reproduce the quantitative figures

```bash
python figures/make_figure2_results.py
python figures/make_figure3_mechanism.py
```

The scripts read `results/estimates.csv` and write PDFs and PNGs to `output/figures/`.
The second command also renders the supplementary adjusted-highest-score figure.
Aggregate result identifiers retain their original names: `D2` means minority
support and `D1` or `D1prime` refers to the bar-clearing indicator. These identifiers
are defined in the [data dictionary](data/dictionary.csv).

## Code quality

```bash
python -m pip install ruff==0.16.8
ruff check --select E4,E7,E9,F,I,D --ignore D203,D213 analysis figures
ruff format --check analysis figures
```

## License and attribution

Original code, documentation, aggregate results, and original dataset contributions
are distributed under the [MIT License](LICENSE). Upstream material retains its
source terms, including MIT, CC0, and CC BY 4.0. The combined dataset is not represented
as exclusively MIT-licensed. See [source attribution and licenses](licenses/SOURCES.md).

When using these materials, cite **Haining Wang, iclr-golden-ticket, 2017–2024 dataset,
version 1.0.0**, available at <https://github.com/Wang-Haining/wonka>, and retain the
upstream attribution notices. Questions and corrections may be reported through
repository issues.
