# Source attribution and licenses

The MIT License in the repository root covers original project contributions. It
does not replace third-party licenses or impose restrictions on public-domain data.
The release contains metadata and numeric review scores, not paper PDFs, abstracts,
review text, reviewer identities, or API response archives.

| Source | Material retained | License or reuse basis |
|---|---|---|
| Rita González Márquez and Dmitry Kobak, [Berens Lab ICLR dataset](https://github.com/berenslab/iclr-dataset) | Submission metadata, decisions, numeric scores | MIT; retain [the original notice](BERENS-MIT.txt) |
| [OpenReview](https://openreview.net/legal/terms) | Public metadata and numeric review fields | Metadata: CC0; comments and configuration records: CC BY 4.0. Preserve source URLs and attribution for review-derived fields |
| Mark Neumann, [SNOR v1](https://doi.org/10.5281/zenodo.15866613) | Source linkage identifiers and explicitly attributed source fields | CC BY 4.0 |
| [OpenAlex](https://help.openalex.org/access/overview/) | Work identifiers, bibliographic metadata, reference edges, derived annual counts | CC0 |
| [Crossref](https://www.crossref.org/documentation/retrieve-metadata/) | Bibliographic metadata and identifiers | Factual metadata; Crossref-generated data are CC0. Abstracts are excluded |
| [DataCite](https://support.datacite.org/docs/datacite-data-file-use-policy) | DOI metadata and identity evidence | CC0 |
| [arXiv](https://info.arxiv.org/help/api/tou.html) | Identifiers and descriptive metadata | CC0 metadata; arXiv is acknowledged as a source |

CC BY 4.0 terms are available at
<https://creativecommons.org/licenses/by/4.0/>; CC0 terms are available at
<https://creativecommons.org/publicdomain/zero/1.0/>. Submission scores are parsed,
decisions are categorized, records are linked, and citation counts are derived from
reference edges. These transformations are this project's work and do not imply
endorsement by the source providers or ICLR.

Semantic Scholar identifiers retained from SNOR remain attributed to SNOR. Restricted
Semantic Scholar API response data are excluded. For 22 recovered submissions whose
core metadata lack a verified redistribution license, titles, authors, decisions, and
scores remain withheld. Four additional recovered records retain documented source
conflicts. A missing source license is not treated as permission to relicense a field.

The dataset uses the Berens `iclr25v2` source frame and the OpenAlex reference-graph
snapshot of June 26, 2026. Source-specific field markers are preserved in
`data/submissions.parquet`. Source terms were checked on September 16, 2026.
