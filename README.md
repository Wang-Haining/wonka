# wonka

Code, aggregate results, and the iclr-golden-ticket, 2017–2024 dataset.

## Contents

| Directory | Contents |
|---|---|
| `analysis/` | Analysis and validation scripts |
| `data/` | Dataset and frozen analysis inputs |
| `results/` | Reference results |
| `figures/` | Figure scripts |
| `licenses/` | Source licenses and attribution |

Dataset details are in [data/README.md](data/README.md) and the
[field dictionary](data/dictionary.csv).

## Installation

Python 3.12 or newer. Run commands from the repository root.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Analyses

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

The default analyses exclude 2020. The `--include-2020` option runs the inclusion
sensitivity analysis; `--caliper 0.25` relaxes exact matching on panel mean.
For the nested two-year samples, use `--through 2022` or `--through 2023` with
`ranking.py`.

Outputs go to `output/`. Validation compares them with the reference tables in
`results/` at a numeric tolerance of 1e-9.

## Figures

```bash
python figures/make_figure2_results.py
python figures/make_figure3_mechanism.py
```

These commands read `results/estimates.csv` and write PDFs and PNGs to
`output/figures/`, including the supplementary adjusted-highest-score figure.

## License

Original contributions use the [MIT License](LICENSE). Upstream material retains
its [source licenses and attribution](licenses/SOURCES.md).

## Contact

Haining Wang

[hw56@iu.edu](mailto:hw56@iu.edu)
