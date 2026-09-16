"""Render the score-variance and supplementary adjusted-highest-score figures.

Run from the repository root with Python 3.12::

    python figures/make_figure3_mechanism.py

Input: results/estimates.csv. Outputs in output/figures/: figure3_mechanism.pdf
and .png, plus figureS1_adjusted_maximum.pdf and .png. The main figure shows
paired score-variance comparisons and edition-specific yields. The supplementary
figure compares highest-score ranking before and after linear adjustment.
"""

import pathlib

import matplotlib.pyplot as plt
import numpy as np
from figure_style import (
    ELSEVIER_DOUBLE,
    RULE_COLOUR,
    add_panel_labels,
    load_estimates,
    save_figure,
    setup,
)

E = load_estimates()
BUDGETS = [1, 2, 5, 10]
FOCAL = RULE_COLOUR["Golden ticket"]
VAR = RULE_COLOUR["Score variance"]
MEAN = RULE_COLOUR["Panel mean"]
COLD = RULE_COLOUR["Highest score"]
COLD2 = RULE_COLOUR["Highest score, residualized"]


def g(i):
    """Return the estimate and interval for a registered result identifier."""
    r = E[i]
    return r["est"], r["lo"], r["hi"]


def panel_a(ax):
    """Compare the highest score before and after linear adjustment."""
    x = np.arange(len(BUDGETS))
    ax.axhline(0, color="0.35", lw=0.6, zorder=1)
    for key, col, lab in [
        ("max", COLD, "as ranked"),
        ("max_resid", COLD2, "after adjustment"),
    ]:
        est = [
            g(f"yield_two_year_through_2024_{key}_observed_only_b{b}")[0]
            for b in BUDGETS
        ]
        lo = [
            g(f"yield_two_year_through_2024_{key}_observed_only_b{b}")[1]
            for b in BUDGETS
        ]
        hi = [
            g(f"yield_two_year_through_2024_{key}_observed_only_b{b}")[2]
            for b in BUDGETS
        ]
        ax.plot(
            x,
            est,
            marker=("s" if key == "max" else "v"),
            ms=3.2,
            lw=1.0,
            color=col,
            label=lab,
            zorder=3,
        )
        ax.fill_between(x, lo, hi, color=col, alpha=0.14, lw=0, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{b}%" for b in BUDGETS])
    ax.set_xlabel("Budget")
    ax.set_ylabel("Percentile points vs. lottery")
    ax.set_title("Highest score, before and after", fontsize=6.2, pad=3)
    ax.legend(frameon=False, fontsize=6.2, loc="lower right", handlelength=1.4)


FRAMES = [
    ("two_year_full", "Two-year, 2017-2024"),
    ("two_year_through_2023", "Two-year, through 2023"),
    ("two_year_early", "Two-year, through 2022"),
    ("three_year_early", "Three-year, through 2022"),
]
COMPS = [
    ("lottery", "lottery", VAR),
    ("mean", "panel mean", MEAN),
    ("D2", "minority support", FOCAL),
]


def panel_b(ax):
    """Draw paired score-variance contrasts within each analysis frame."""
    ax.axvline(0, color="0.35", lw=0.6, zorder=1)
    ypos, ylab = [], []
    row = 0.0
    for fr, flab in FRAMES:
        ax.text(
            0.02,
            -row + 0.85,
            flab,
            transform=ax.get_yaxis_transform(),
            fontsize=6.2,
            color="0.4",
            ha="left",
            va="center",
        )
        for comp, clab, col in COMPS:
            est, lo, hi = g(f"paired_{fr}_variance_vs_{comp}_observed_only_b10")
            y = -row
            ax.plot(
                [lo, hi], [y, y], lw=1.2, color=col, solid_capstyle="butt", zorder=2
            )
            ax.plot([est], [y], marker="o", ms=3.2, color=col, zorder=3)
            ypos.append(y)
            ylab.append(f"vs. {clab}")
            row += 1
        row += 1.15
    ax.set_yticks(ypos)
    ax.set_yticklabels(ylab, fontsize=6.2)
    ax.set_ylim(-row + 0.4, 1.5)
    ax.set_xlabel("Difference in percentile points")
    ax.set_title("Score variance, paired contrasts, budget 10%", fontsize=6.2, pad=3)


def panel_c(ax):
    """Draw edition-specific score-variance gains against the lottery."""
    years = [2017, 2018, 2019, 2021, 2022, 2023, 2024]
    x = np.arange(len(years))
    ax.axhline(0, color="0.35", lw=0.6, zorder=1)
    for xi, yr in zip(x, years):
        est, lo, hi = g(f"edition_2_{yr}_variance_observed_only")
        ax.plot([xi, xi], [lo, hi], lw=1.1, color=VAR, solid_capstyle="butt", zorder=2)
        ax.plot([xi], [est], marker="^", ms=3.2, color=VAR, zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels([str(y) for y in years], fontsize=6.2)
    ax.set_xlabel("Conference edition")
    ax.set_ylabel("Percentile points vs. lottery")
    ax.set_title("Score variance by edition, budget 10%", fontsize=6.2, pad=3)


def main():
    """Render the disagreement figure and supplementary adjustment figure."""
    setup(n=4)
    fig, axes = plt.subplots(1, 2, figsize=(ELSEVIER_DOUBLE, ELSEVIER_DOUBLE / 2.6))
    panel_b(axes[0])
    panel_c(axes[1])
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    add_panel_labels(axes)
    save_figure(
        fig,
        pathlib.Path(__file__).resolve().parents[1]
        / "output/figures/figure3_mechanism",
        formats=("pdf", "png"),
    )
    fig, ax = plt.subplots(figsize=(ELSEVIER_DOUBLE / 2, ELSEVIER_DOUBLE / 2.5))
    panel_a(ax)
    save_figure(
        fig,
        pathlib.Path(__file__).resolve().parents[1]
        / "output/figures/figureS1_adjusted_maximum",
        formats=("pdf", "png"),
    )


if __name__ == "__main__":
    main()
