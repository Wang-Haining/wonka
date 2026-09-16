"""Figure 2: what each allocation rule buys.

a  yield against budget, two-year window, five rules
b  three-year window at a 10% budget
c  three assumptions about submissions with no citation record
"""

import pathlib

import matplotlib.pyplot as plt
import numpy as np
from figure_style import (
    ELSEVIER_DOUBLE,
    MARGIN,
    RULE_COLOUR,
    add_panel_labels,
    load_estimates,
    save_figure,
    setup,
)

E = load_estimates()
KEYS = ["mean", "max", "variance", "D2"]
LABEL = {
    "D2": "Minority support",
    "mean": "Panel mean",
    "max": "Highest score",
    "max_resid": "Highest score,\nresidualized",
    "variance": "Score variance",
}
COL = {
    "D2": RULE_COLOUR["Golden ticket"],
    "mean": RULE_COLOUR["Panel mean"],
    "max": RULE_COLOUR["Highest score"],
    "max_resid": RULE_COLOUR["Highest score, residualized"],
    "variance": RULE_COLOUR["Score variance"],
}
MARK = {"D2": "D", "mean": "o", "max": "s", "variance": "^"}
BUDGETS = [1, 2, 5, 10]
USABLE_FROM = 5


def g(i):
    """Return the estimate and interval for a registered result identifier."""
    r = E[i]
    return r["est"], r["lo"], r["hi"]


def panel_a(ax):
    """Draw citation gains across the four allocation budgets."""
    x = np.arange(len(BUDGETS))

    for boundary in [-MARGIN, MARGIN]:
        ax.axhline(boundary, color="0.55", lw=0.7, ls=":", zorder=1)
    ax.axhline(0, color="0.35", lw=0.6, zorder=1)
    for k in KEYS:
        y = [
            g(f"yield_two_year_through_2024_{k}_observed_only_b{b}")[0] for b in BUDGETS
        ]
        ax.plot(
            x,
            y,
            marker=MARK[k],
            ms=3.2,
            lw=1.3,
            color=COL[k],
            zorder=3,
            label=LABEL[k].replace("\n", " "),
        )
        if k == "D2":
            lo = [
                g(f"yield_two_year_through_2024_{k}_observed_only_b{b}")[1]
                for b in BUDGETS
            ]
            hi = [
                g(f"yield_two_year_through_2024_{k}_observed_only_b{b}")[2]
                for b in BUDGETS
            ]
            ax.fill_between(x, lo, hi, color=COL[k], alpha=0.14, lw=0, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{b}%" for b in BUDGETS])
    ax.set_xlim(-0.35, len(BUDGETS) - 0.65)
    ax.set_xlabel("Budget, share of the year's accepted set")
    ax.set_ylabel("Percentile points vs. lottery")


def forest(ax, ids, labels, title):
    """Draw rule-specific estimates and intervals on a common axis."""
    y = np.arange(len(ids))[::-1]

    for boundary in [-MARGIN, MARGIN]:
        ax.axvline(boundary, color="0.55", lw=0.7, ls=":", zorder=1)
    ax.axvline(0, color="0.35", lw=0.6, zorder=1)
    for yi, (i, k) in zip(y, ids):
        est, lo, hi = g(i)
        ax.plot(
            [lo, hi], [yi, yi], lw=1.2, color=COL[k], zorder=2, solid_capstyle="butt"
        )
        ax.plot([est], [yi], marker=MARK[k], ms=3.4, color=COL[k], zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=6.2)
    ax.set_ylim(-0.6, len(ids) - 0.4)
    ax.set_xlabel("Percentile points vs. lottery")
    ax.set_title(title, fontsize=6.2, pad=3)


def panel_b(ax):
    """Draw the three-year results at the largest allocation budget."""
    forest(
        ax,
        [(f"yield_three_year_{k}_observed_only_b10", k) for k in KEYS],
        [LABEL[k] for k in KEYS],
        "Three-year window, budget 10%",
    )


def panel_c(ax):
    """Draw gains under the three missing-outcome assignments."""
    scen = [
        ("missing_percentile_0", "lowest percentile"),
        ("missing_pool_mean", "pool mean"),
        ("missing_zero_citation_percentile", "zero citations"),
    ]
    for boundary in [-MARGIN, MARGIN]:
        ax.axvline(boundary, color="0.55", lw=0.7, ls=":", zorder=1)
    ax.axvline(0, color="0.35", lw=0.6, zorder=1)
    centres = np.array([9, 4.5, 0])
    for j, k in enumerate(KEYS):
        rows = np.array(
            [
                g(f"yield_two_year_through_2024_{k}_{scenario}_b10")
                for scenario, _ in scen
            ]
        )
        assert np.isfinite(rows).all(), f"missing interval for {k}"
        vals, lo, hi = rows.T
        ypos = centres + 1.2 - j * 0.8
        ax.hlines(ypos, lo, hi, color=COL[k], lw=1.1, zorder=3)
        ax.plot(
            vals, ypos, linestyle="none", marker=MARK[k], color=COL[k], ms=3.4, zorder=4
        )
    ax.set_yticks(
        centres, ["Lowest\npercentile", "Pool\nmean", "Zero-citation\npercentile"]
    )
    ax.tick_params(axis="y", length=0, labelsize=6.2)
    ax.set_ylim(-2, 11)
    ax.set_xlim(-5.5, 13)
    ax.set_xticks([-5, 0, 5, 10])
    ax.set_xlabel("Percentile points vs. lottery")
    ax.set_title(
        "Unresolved submissions assigned\nTwo-year window, budget 10%",
        fontsize=6.2,
        pad=5,
    )


def main():
    """Render the main allocation-results figure from the frozen estimates."""
    setup(n=5)
    fig, axes = plt.subplots(1, 3, figsize=(ELSEVIER_DOUBLE, ELSEVIER_DOUBLE / 2.9))
    panel_a(axes[0])
    panel_b(axes[1])
    panel_c(axes[2])
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.04),
        ncol=4,
        frameon=False,
        fontsize=6.2,
        handlelength=1.5,
        columnspacing=1.2,
    )
    add_panel_labels(axes)
    save_figure(
        fig,
        pathlib.Path(__file__).resolve().parents[1] / "output/figures/figure2_results",
        formats=("pdf", "png"),
    )


if __name__ == "__main__":
    main()
