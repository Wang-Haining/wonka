"""Validate the distributed dataset and optionally reconcile reproduced results.

Run from the repository root with Python 3.12::

    python analysis/validate.py
    python analysis/validate.py --results

The first command checks the supplied data and checksums. Before running the
second, run ranking.py for both citation windows with and without --include-2020,
and matching.py with its default and --caliper 0.25 settings. Result validation
compares output/ against results/ with numeric tolerance 1e-9. Checks print a
summary and raise an error on failure; neither command modifies reference files.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def validate_data():
    """Check file integrity, submission keys, citation counts, and release boundaries."""
    data = ROOT / "data"
    manifest = json.loads((data / "manifest.json").read_text())
    for name, expected in manifest["sha256"].items():
        actual = hashlib.sha256((data / name).read_bytes()).hexdigest()
        assert actual == expected, f"Checksum mismatch: {name}"
    submissions = pd.read_parquet(data / "submissions.parquet")
    frame = pd.read_parquet(data / "analysis_frame.parquet")
    annual = pd.read_parquet(data / "annual_citations.parquet")
    edges = pd.read_parquet(data / "incoming_citation_edges.parquet")
    assert len(submissions) == 24476, f"Expected 24476 records, got {len(submissions)}"
    assert len(frame) == 24450, f"Expected 24450 analysis records, got {len(frame)}"
    for name, table in [("submissions", submissions), ("analysis_frame", frame)]:
        assert not table.duplicated(["year", "id"]).any(), f"Duplicate keys in {name}"
        assert set(table.year) == set(range(2017, 2025)), f"Unexpected years in {name}"
    assert not annual.duplicated(["year", "id", "citation_year"]).any()
    assert not edges.duplicated().any(), "Duplicate reference edges"
    assert annual.citations.ge(0).all(), "Negative annual counts"
    assert np.equal(annual.citations, np.floor(annual.citations)).all()
    known_scores = submissions.scores.notna()
    assert (
        submissions.loc[known_scores, "scores"].map(len)
        == submissions.loc[known_scores, "n_scores"]
    ).all(), "Score counts disagree with arrays"
    withheld = submissions.source_metadata_status.eq("withheld-source-license")
    assert withheld.sum() == 22, f"Expected 22 withheld rows, got {withheld.sum()}"
    assert (
        submissions.loc[
            withheld, ["title", "authors", "raw_authors", "decision", "scores"]
        ]
        .isna()
        .all()
        .all()
    ), "Withheld source fields must remain null"
    assert submissions.external_identity_resolved.sum() == 19864
    assert submissions.citation_ready.sum() == 18657
    # Reconstruct counts from the union of citing IDs, never by adding version totals.
    mapping = submissions.loc[
        submissions.citation_ready, ["year", "id", "counted_openalex_ids"]
    ].explode("counted_openalex_ids")
    linked = mapping.merge(
        edges, left_on="counted_openalex_ids", right_on="target_work_id", how="inner"
    )
    counts = linked.groupby(["year", "id", "citation_year"]).citing_work_id.nunique()
    keys = pd.MultiIndex.from_frame(annual[["year", "id", "citation_year"]])
    expected = counts.reindex(keys, fill_value=0).to_numpy()
    # An absent edge in the complete distributed graph is a structural zero.
    assert np.array_equal(expected, annual.citations), "Reference-edge counts disagree"
    totals = annual.set_index(["year", "id"])
    for window, ready in [(2, "citation_ready"), (3, "citation_ready_3y")]:
        eligible = submissions.loc[submissions[ready]].set_index(["year", "id"])
        use = totals[
            (totals.citation_year >= totals.index.get_level_values("year"))
            & (totals.citation_year < totals.index.get_level_values("year") + window)
        ]
        summed = use.groupby(level=["year", "id"]).citations.sum()
        assert np.array_equal(
            summed.reindex(eligible.index), eligible[f"citation_count_{window}y"]
        ), f"Incorrect {window}-year window totals"
    primary = frame[frame.year.ne(2020)]
    rejected = primary[primary.decision.eq("Reject") & primary.n_rev.ge(2)]
    assert len(primary) == 21857 and len(rejected) == 10625
    assert rejected.citation_count_2y.notna().sum() == 7411
    print(
        "PASS: 24476 dataset rows; 24450 original-source analysis rows; "
        "186570 annual counts reconciled to 581031 reference edges."
    )


def validate_results():
    """Compare reproduced core estimates and intervals with frozen aggregate tables."""
    checked = 0
    for folder in [
        "two_year_through_2024",
        "three_year",
        "D1_exact_through_2024",
        "D1_through_2024",
    ]:
        for reference in sorted((ROOT / "results" / folder).glob("*.csv")):
            actual = ROOT / "output" / folder / reference.name
            assert actual.exists(), f"Run the analysis first: missing {actual}"
            pd.testing.assert_frame_equal(
                pd.read_csv(actual),
                pd.read_csv(reference),
                check_exact=False,
                atol=1e-9,
                rtol=1e-9,
            )
            checked += 1
    paired_keys = ["budget_pct", "rule", "comparator", "scenario"]
    paired_reference = (
        pd.read_csv(ROOT / "results/paired_comparisons_all_budgets.csv")
        .set_index(paired_keys)
        .sort_index()
    )
    paired_actual = (
        pd.read_csv(ROOT / "output/two_year_through_2024/paired_comparisons.csv")
        .set_index(paired_keys)
        .sort_index()
    )
    assert len(paired_reference) == 80, "Expected 80 paired comparisons"
    pd.testing.assert_frame_equal(
        paired_actual, paired_reference, check_exact=False, atol=1e-9, rtol=1e-9
    )
    print("PASS: all 80 paired comparisons match the reference results.")
    reference = pd.read_csv(ROOT / "results/include2020/comparisons.csv")
    for window, folder in [
        ("two_year", "two_year_through_2024_including_2020"),
        ("three_year", "three_year_including_2020"),
    ]:
        actual = pd.read_csv(ROOT / "output" / folder / "yield_scenarios.csv")
        expected = reference[
            reference.window.eq(window)
            & reference.frame.eq("with_2020")
            & reference.contrast.str.endswith(" minus lottery")
        ].copy()
        expected["rule"] = expected.contrast.str.removesuffix(" minus lottery")
        joined = actual.merge(
            expected,
            left_on=["budget_pct", "rule", "scenario"],
            right_on=["budget", "rule", "scenario"],
            validate="one_to_one",
        )
        assert len(joined) == 80, f"Expected 80 contrasts, got {len(joined)}"
        for a, b in [
            ("difference_lottery", "estimate"),
            ("difference_ci_low", "ci_low_y"),
            ("difference_ci_high", "ci_high_y"),
        ]:
            np.testing.assert_allclose(joined[a], joined[b], atol=1e-9, rtol=1e-9)
    print(f"PASS: {checked} core result tables and 160 inclusion contrasts reconciled.")


def main():
    """Run dataset validation and the requested result-reproduction checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", action="store_true")
    args = parser.parse_args()
    validate_data()
    if args.results:
        validate_results()


if __name__ == "__main__":
    main()
