"""Shared plotting dimensions, rule colors, and frozen style settings."""

import json
from pathlib import Path

import matplotlib.pyplot as plt

MM = 1 / 25.4
ELSEVIER_SINGLE = 90 * MM  # mm -> inches
ELSEVIER_DOUBLE = 190 * MM

FOCAL = "#E64B35"  # NPG coral
COLD_1 = "#0077BB"  # Paul Tol bright blue; contrast 4.82:1
COLD_2 = "#3C5488"  # NPG navy
CHARCOAL = "#333333"
GREY = "#A0A0A0"

RULES = [
    "Golden ticket",
    "Panel mean",
    "Highest score",
    "Highest score, residualized",
    "Score variance",
    "Lottery",
]
RULE_COLOUR = {
    "Golden ticket": FOCAL,
    "Panel mean": CHARCOAL,
    "Highest score": COLD_1,
    "Highest score, residualized": COLD_2,
    "Score variance": "#00A087",  # NPG teal: the symmetric alternative
    "Lottery": GREY,
}
RULE_MARKER = {
    "Panel mean": "o",
    "Highest score": "s",
    "Score variance": "^",
    "Golden ticket": "D",
    "Highest score, residualized": "v",
}
MARGIN = 5.0  # exploratory equivalence margin, percentile points


def setup(n=4, mark="fill"):
    """Apply the fixed plotting settings used for the analysis figures."""
    settings = json.loads((Path(__file__).parent / "style.json").read_text())
    plt.rcParams.update(settings)


def load_estimates():
    """Every plotted value comes from results/estimates.csv, the frozen aggregate estimate registry."""
    import csv

    rows = {}
    path = Path(__file__).resolve().parents[1] / "results" / "estimates.csv"
    with open(path) as f:
        for r in csv.DictReader(f):
            if not r["id"] or r["id"].startswith("#"):
                continue
            rows[r["id"]] = {
                "est": float(r["estimate"]),
                "lo": float(r["ci_low"]) if r["ci_low"] else None,
                "hi": float(r["ci_high"]) if r["ci_high"] else None,
                "rule": r["rule"],
                "frame": r["frame"],
            }
    return rows


def add_panel_labels(axes, x=-0.12, y=1.05, fontsize=8, labels=None):
    """Place lowercase panel labels at a fixed axes-relative position."""
    for i, ax in enumerate(axes):
        ax.text(
            x,
            y,
            labels[i] if labels else chr(97 + i),
            transform=ax.transAxes,
            fontsize=fontsize,
            fontweight="bold",
            va="top",
            ha="right",
            family="sans-serif",
        )


def save_figure(fig, filename, formats=("pdf", "png")):
    """Export editable PDF and raster PNG versions of a figure."""
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    fig.align_labels()
    for fmt in formats:
        path = Path(f"{filename}.{fmt}")
        fig.savefig(path, format=fmt, dpi=300)
        print(f"Saved {path.name}")
