"""Compare bar-clearing rejections using greedy matching and fixed-pair bootstrap.

Run from the repository root with Python 3.12::

    python analysis/matching.py
    python analysis/matching.py --caliper 0.25

Input: data/analysis_frame.parquet. Outputs: output/D1_exact_through_2024/
and output/D1_through_2024/, respectively. Both analyses exclude 2020.
The default matches exactly on edition, reviewer count, and panel mean.
The sensitivity analysis allows panel means to differ by at most 0.25 points.
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    """Match within edition and reviewer count, then estimate citation differences."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--caliper", type=float, choices=[0, 0.25], default=0)
    args = parser.parse_args()
    caliper = args.caliper
    name = "D1_exact_through_2024" if caliper == 0 else "D1_through_2024"
    output_dir = ROOT / "output" / name
    output_dir.mkdir(parents=True, exist_ok=True)
    full = pd.read_parquet(ROOT / "data/analysis_frame.parquet")
    d = full[full.year.ne(2020)].copy()
    d["mean"] = d.scores.map(lambda s: np.mean(s) if len(s) else np.nan)
    r = d[d.decision.eq("Reject") & d.n_rev.ge(2)].copy()
    assert r.D1prime.notna().all()
    pairs = []
    overlap = []
    for y, g in r.groupby("year"):
        top = (
            g.assign(D2_order=g.D2.round(12))
            .sort_values(["D2_order", "id"], ascending=[False, True])
            .head(int(np.ceil(0.1 * len(g))))
        )
        overlap.append(
            dict(
                year=int(y),
                rejects=len(g),
                D1=int(g.D1prime.sum()),
                D2_top=len(top),
                intersection=int(top.D1prime.sum()),
                fraction_top_D2_in_D1=top.D1prime.mean(),
            )
        )
    for (y, k), g in r.groupby(["year", "n_rev"]):
        t = g[g.D1prime.eq(True)].sort_values("id")
        c = g[g.D1prime.eq(False)].sort_values("id")
        if t.empty or c.empty:
            continue
        dist = np.abs(t["mean"].to_numpy()[:, None] - c["mean"].to_numpy()[None, :])
        avail = np.ones(len(c), dtype=bool)
        for i in np.argsort((dist <= (caliper + 1e-12)).sum(axis=1), kind="stable"):
            cand = np.where(avail & (dist[i] <= (caliper + 1e-12)))[0]
            if not len(cand):
                continue
            j = cand[np.argmin(dist[i, cand])]
            avail[j] = False
            pairs.append(
                dict(
                    year=int(y),
                    n_rev=int(k),
                    treated=t.iloc[i].id,
                    control=c.iloc[j].id,
                    treated_mean=t.iloc[i]["mean"],
                    control_mean=c.iloc[j]["mean"],
                    score_distance=dist[i, j],
                )
            )
    f = pd.DataFrame(pairs)
    assert (
        not f.duplicated(["year", "treated"]).any()
        and not f.duplicated(["year", "control"]).any()
    )
    assert f.score_distance.max() <= (caliper + 1e-12)
    pd.DataFrame(overlap).to_csv(output_dir / "D1_D2_overlap.csv", index=False)
    rows = []
    diag = []
    for label, frame in [
        ("two_year_all", d),
        ("three_year_original", full[full.year.le(2022) & full.year.ne(2020)]),
    ]:
        outcome = {}
        zero = {}
        pool = {}
        countcol = (
            "citation_count_2y" if label == "two_year_all" else "citation_count_3y"
        )
        for y, g in frame.groupby("year"):
            vals = g[countcol].to_numpy(dtype=float)
            ok = np.isfinite(vals)
            sv = np.sort(vals[ok])
            pct = (
                50
                * (
                    np.searchsorted(sv, vals[ok], "left")
                    + np.searchsorted(sv, vals[ok], "right")
                )
                / len(sv)
            )
            outcome.update(
                {(int(y), i): float(v) for i, v in zip(g.loc[ok, "id"], pct)}
            )
            zero[y] = 50 * np.sum(sv == 0) / len(sv)
            rr = g[g.decision.eq("Reject") & g.n_rev.ge(2) & g[countcol].notna()]
            pool[y] = np.mean([outcome[(int(y), i)] for i in rr.id])
        use = f[f.year.isin(frame.year.unique())].copy()
        a = np.array(
            [outcome.get((x.year, x.treated), np.nan) for x in use.itertuples()]
        )
        b = np.array(
            [outcome.get((x.year, x.control), np.nan) for x in use.itertuples()]
        )
        both = np.isfinite(a) & np.isfinite(b)
        for year, z in use.groupby("year"):
            ids = use.index.get_indexer(z.index)
            gg = r[r.year.eq(year)]
            diag.append(
                dict(
                    window=label,
                    year=int(year),
                    champions=int(gg.D1prime.sum()),
                    matched=len(z),
                    both_resolved=int(both[ids].sum()),
                    treated_resolved=int(np.isfinite(a[ids]).sum()),
                    control_resolved=int(np.isfinite(b[ids]).sum()),
                    mean_score_difference=float(
                        (z.treated_mean - z.control_mean).mean()
                    ),
                    max_score_distance=float(z.score_distance.max()),
                )
            )
        for scenario in [
            "observed_pairs",
            "missing_percentile_0",
            "missing_pool_mean",
            "missing_zero_citation_percentile",
        ]:
            if scenario == "observed_pairs":
                diff = a[both] - b[both]
            else:
                value = (
                    np.zeros(len(use))
                    if scenario == "missing_percentile_0"
                    else np.array(
                        [
                            pool[y] if scenario == "missing_pool_mean" else zero[y]
                            for y in use.year
                        ]
                    )
                )
                diff = np.where(np.isfinite(a), a, value) - np.where(
                    np.isfinite(b), b, value
                )
            assert len(diff) > 0 and np.isfinite(diff).all()
            rng = np.random.default_rng(20260915)
            boot = np.array(
                [
                    rng.choice(diff, size=len(diff), replace=True).mean()
                    for _ in range(2000)
                ]
            )
            lo, hi = np.quantile(boot, [0.025, 0.975])
            rows.append(
                dict(
                    window=label,
                    scenario=scenario,
                    pairs=len(use),
                    analyzed_pairs=len(diff),
                    difference=diff.mean(),
                    ci_low=lo,
                    ci_high=hi,
                )
            )
    pd.DataFrame(rows).to_csv(output_dir / "D1_matched_results.csv", index=False)
    pd.DataFrame(diag).to_csv(output_dir / "D1_match_diagnostics.csv", index=False)
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    print(
        "PASS: outcome-blind greedy 1:1 matching without replacement; exact year and reviewer count; conditional fixed-pair bootstrap; caliper",
        caliper,
        "pairs",
        len(f),
        "max distance",
        f.score_distance.max(),
    )


if __name__ == "__main__":
    main()
