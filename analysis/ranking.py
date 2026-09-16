"""Reproduce within-edition ranking yields and paired bootstrap intervals.

Run from the repository root with Python 3.12::

    python analysis/ranking.py
    python analysis/ranking.py --window 3
    python analysis/ranking.py --include-2020
    python analysis/ranking.py --window 3 --include-2020
    python analysis/ranking.py --through 2022
    python analysis/ranking.py --through 2023

Input: data/analysis_frame.parquet. Outputs: output/<analysis-frame>/.
The default excludes 2020; --include-2020 runs the inclusion sensitivity analysis.
The --through option selects nested two-year samples. Minority-support scores
remain fixed; the adjusted highest-score regression is refitted in each draw.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    """Read the frozen frame and run the requested citation-window analysis."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", type=int, choices=[2, 3], default=2)
    parser.add_argument("--through", type=int, choices=[2022, 2023, 2024], default=2024)
    parser.add_argument("--include-2020", action="store_true")
    args = parser.parse_args()
    cutoff = min(args.through, 2022) if args.window == 3 else args.through
    suffix = "_including_2020" if args.include_2020 else ""
    name = f"two_year_through_{cutoff}" if args.window == 2 else "three_year"
    output_dir = ROOT / "output" / (name + suffix)
    output_dir.mkdir(parents=True, exist_ok=True)
    d = pd.read_parquet(ROOT / "data/analysis_frame.parquet")
    years = [y for y in range(2017, cutoff + 1) if args.include_2020 or y != 2020]
    d = d[d.year.isin(years)].copy()
    assert set(d.year) == set(years), f"Unexpected editions: {sorted(d.year.unique())}"
    assert not d.duplicated(["year", "id"]).any(), "Duplicate submission identifiers"
    M = d.copy()
    M["eligible"] = M.decision.eq("Reject") & M.n_rev.ge(2)
    for name, fn in [("mean", np.mean), ("variance", np.var), ("max", max)]:
        M[name] = M.scores.map(lambda x: fn(x) if len(x) else np.nan)
    count_column = f"citation_count_{args.window}y"
    fractions = np.array([0.01, 0.02, 0.05, 0.1])
    names = ["D2", "mean", "variance", "max", "max_resid", "lottery"]
    scenarios = [
        "observed_only",
        "missing_percentile_0",
        "missing_pool_mean",
        "missing_zero_citation_percentile",
    ]
    a = M[M.decision.str.startswith("Accept")].groupby("year").size()
    budgets = {int(y): np.ceil(fractions * n).astype(int) for y, n in a.items()}
    B = np.sum(list(budgets.values()), axis=0)
    groups = [
        dict(
            year=int(y),
            ids=g.id.to_numpy(),
            eligible=g.eligible.to_numpy(),
            citation=g[count_column].to_numpy(dtype=float),
            n_rev=g.n_rev.to_numpy(dtype=float),
            values=g[["D2", "mean", "variance", "max"]].to_numpy(dtype=float),
        )
        for y, g in M.groupby("year")
    ]

    def evaluate(rng=None, details=False):
        """Calculate all rules on one within-edition sample, preserving shared draws."""
        out = np.zeros((4, 6, 4))
        coverage = np.zeros((4, 6))
        bounds = np.zeros((4, 6, 2))
        coefrows = []
        for g in groups:
            n = len(g["ids"])
            idx = np.arange(n) if rng is None else rng.integers(n, size=n)
            c = g["citation"][idx]
            known = np.isfinite(c)
            N = known.sum()
            assert N > 0
            pct = np.full(n, np.nan)
            s = np.sort(c[known])
            pct[known] = (
                50
                * (
                    np.searchsorted(s, c[known], "left")
                    + np.searchsorted(s, c[known], "right")
                )
                / N
            )
            r = np.where(g["eligible"][idx])[0]
            v = g["values"][idx]
            ids = g["ids"][idx]
            bs = budgets[g["year"]]
            X = np.column_stack([np.ones(len(r)), v[r, 1], g["n_rev"][idx][r]])
            beta = np.linalg.lstsq(X, v[r, 3], rcond=None)[0]
            resid = v[r, 3] - X @ beta
            assert np.max(np.abs(X.T @ resid)) < 1e-6 and np.isfinite(v[r]).all()
            scores = np.column_stack([v[r], resid])
            pool = np.mean(pct[r][known[r]])
            zero = 50 * np.sum(c[known] == 0) / N
            vals = np.column_stack(
                [
                    np.where(known, pct, 0),
                    np.where(known, pct, 0),
                    np.where(known, pct, pool),
                    np.where(known, pct, zero),
                ]
            )
            lower = np.where(known, np.nan_to_num(pct) * N / n, 0)
            upper = np.where(known, lower + 100 * (n - N) / n, 100)
            for j in range(6):
                if j == 5:
                    out[:, j] += bs[:, None] * vals[r].sum(axis=0) / len(r)
                    coverage[:, j] += bs * known[r].mean()
                    continue
                order = r[np.lexsort((ids[r], -scores[:, j].round(12)))]
                out[:, j] += np.cumsum(vals[order], axis=0)[bs - 1]
                coverage[:, j] += np.cumsum(known[order])[bs - 1]
                if details:
                    for i, b in enumerate(bs):
                        weights = np.full(len(r), -b / len(r))
                        weights[np.isin(r, order[:b])] += 1
                        bounds[i, j, 0] += (
                            np.sum(weights * np.where(weights >= 0, lower[r], upper[r]))
                            / B[i]
                        )
                        bounds[i, j, 1] += (
                            np.sum(weights * np.where(weights >= 0, upper[r], lower[r]))
                            / B[i]
                        )
            if details:
                coefrows.append(
                    dict(
                        year=g["year"],
                        rejects=len(r),
                        intercept=beta[0],
                        mean_coefficient=beta[1],
                        reviewer_count_coefficient=beta[2],
                        zero_citation_percentile=zero,
                        pool_mean_percentile=pool,
                    )
                )
        assert (coverage > 0).all()
        out[:, :, 0] /= coverage
        out[:, :, 1:] /= B[:, None, None]
        return out, coverage, bounds, coefrows

    point, coverage, bounds, coef = evaluate(details=True)
    rng = np.random.default_rng(20260915)
    boot = []
    for i in range(2000):
        boot.append(evaluate(rng)[0])
        if (i + 1) % 500 == 0:
            print("Bootstrap", i + 1, flush=True)
    boot = np.array(boot)
    rows = []
    for i, f in enumerate(fractions):
        for j, rule in enumerate(names):
            for k, scenario in enumerate(scenarios):
                lo, hi = np.quantile(boot[:, i, j, k], [0.025, 0.975])
                delta = boot[:, i, j, k] - boot[:, i, 5, k]
                dl, du = np.quantile(delta, [0.025, 0.975])
                rows.append(
                    dict(
                        budget_pct=int(100 * f),
                        slots=int(B[i]),
                        rule=rule,
                        scenario=scenario,
                        resolved_selected=coverage[i, j],
                        coverage=coverage[i, j] / B[i],
                        mean_percentile=point[i, j, k],
                        ci_low=lo,
                        ci_high=hi,
                        difference_lottery=point[i, j, k] - point[i, 5, k],
                        difference_ci_low=dl,
                        difference_ci_high=du,
                    )
                )
    result = pd.DataFrame(rows)
    result.to_csv(output_dir / "yield_scenarios.csv", index=False)
    pd.DataFrame(coef).to_csv(
        output_dir / "residualization_coefficients.csv", index=False
    )
    np.save(output_dir / "bootstrap.npy", boot)
    pd.DataFrame(
        [
            dict(
                budget_pct=int(100 * f),
                rule=rule,
                lower=bounds[i, j, 0],
                upper=bounds[i, j, 1],
            )
            for i, f in enumerate(fractions)
            for j, rule in enumerate(names)
        ]
    ).to_csv(output_dir / "missingness_bounds.csv", index=False)
    print(result[(result.budget_pct == 10)].round(3).to_string(index=False))
    print(
        "PASS: ranking analysis; frame",
        len(d),
        "rejects",
        int(M.eligible.sum()),
        "years",
        years,
        "budgets",
        B.tolist(),
        "replicates",
        2000,
    )

    contrasts = []
    for i, budget in enumerate([1, 2, 5, 10]):
        for left, right in [
            ("mean", "D2"),
            ("variance", "D2"),
            ("variance", "mean"),
            ("max_resid", "D2"),
        ]:
            a, b = names.index(left), names.index(right)
            for k, scenario in enumerate(scenarios):
                lo, hi = np.quantile(
                    boot[:, i, a, k] - boot[:, i, b, k], [0.025, 0.975]
                )
                contrasts.append(
                    dict(
                        budget_pct=budget,
                        rule=left,
                        comparator=right,
                        scenario=scenario,
                        difference=point[i, a, k] - point[i, b, k],
                        ci_low=lo,
                        ci_high=hi,
                    )
                )
    pd.DataFrame(contrasts).to_csv(output_dir / "paired_comparisons.csv", index=False)
    print(
        f"Saved {len(rows)} yield rows and {len(contrasts)} paired contrasts to {output_dir.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
