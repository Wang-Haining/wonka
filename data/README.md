# iclr-golden-ticket, 2017–2024 dataset

Version 1.0.0. One submission is identified by `(year, id)`. All tables use UTF-8
metadata in Apache Parquet format. Load them with `pandas.read_parquet`.

## Files

| File | Rows | Unit |
|---|---:|---|
| `submissions.parquet` | 24,476 | Submission |
| `manifestations.parquet` | 41,160 | Submission–external-work relation |
| `match_evidence.parquet` | 58,177 | Linkage evidence record |
| `annual_citations.parquet` | 186,570 | Submission–citation-year count |
| `incoming_citation_edges.parquet` | 581,031 | Target work–citing work edge |
| `analysis_frame.parquet` | 24,450 | Frozen original-source submission |

The [field dictionary](dictionary.csv) describes every column. The checksums in
`manifest.json` identify the exact distributed files. No data acquisition code is
included. The analysis code starts from these tables.

## Coverage

Identity resolution and citation availability have the same submission denominator
but different meanings. A linked paper may still lack a usable citation record.

| Edition | Submissions | Identity resolved | Citation available |
|---|---:|---:|---:|
| 2017 | 490 | 484 (98.8%) | 481 (98.2%) |
| 2018 | 1,018 | 963 (94.6%) | 960 (94.3%) |
| 2019 | 1,579 | 1,552 (98.3%) | 1,537 (97.3%) |
| 2020 | 2,594 | 2,556 (98.5%) | 2,528 (97.5%) |
| 2021 | 3,014 | 2,964 (98.3%) | 2,939 (97.5%) |
| 2022 | 3,422 | 2,550 (74.5%) | 2,313 (67.6%) |
| 2023 | 4,955 | 3,535 (71.3%) | 3,125 (63.1%) |
| 2024 | 7,404 | 5,260 (71.0%) | 4,774 (64.5%) |

## Interpretation

- The original source contains 24,450 submissions. The release retains an additional
  26 recovered records, identified by `supplemental_reason`. The statistical analysis
  uses only the original source frame; 2020 is included only in a sensitivity analysis.
- Missing values remain missing. A recorded zero means no indexed citation in the
  specified OpenAlex window after completion of the source reference-graph scan.
  An unmatched submission is not evidence of nonpublication.
- Annual counts deduplicate citing work identifiers across verified versions. Do not
  add preprint and published-version totals. Annual counts may be reconstructed from
  `incoming_citation_edges` and `counted_openalex_ids`.
- The two-year window covers the conference year and the next calendar year; the
  three-year window includes one further year. Citation year 2026 is partial in the
  snapshot, and open windows remain unavailable. For the frozen three-year analysis,
  editions after 2022 are excluded even when the dataset has later available outcomes.
- Repeated submissions of the same paper retain distinct submission identifiers.
  `work_family_id` connects verified related submission records; it is release-specific.
- `match_evidence` is a compact structured selection of permitted linkage evidence.
  It omits internal adjudication narratives and provider response payloads. Candidate
  status must be checked before interpreting any evidence row as an accepted link.
- `analysis_frame` retains the original score constructs (`D2`, `D1prime`, `mstar`)
  and source decision strings used by the study. Other tables use categorized decisions.
  Citation counts are untransformed; percentiles are recomputed by the analysis scripts.

See [licenses and attribution](../licenses/SOURCES.md) for source-specific terms.
