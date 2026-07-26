# Legal Judgments KG — Design Notes

589 Indian Supreme Court judgments (2016). The published dataset already ships
extracted entities, so this graph is built from those (no OCR/extraction here).

## Node labels
| Label | Count | Key fields |
|-------|-------|-----------|
| Case  | 589   | id, title, year, month |
| Judge | 34    | name |
| Party | 1,102 | name |
| Act   | 446   | name |
| Topic | 2,291 | text, category (11 categories) |

Nodes are deduplicated by **exact string match** on their key (`Case.id`,
`Judge.name`, `Party.name`, `Act.name`, `Topic.text`). Names are **not**
normalized — the source data is unnormalized, so a judge under two spellings
appears as two nodes (which is what makes entity resolution interesting).

## Edge types
| Edge | From → To | Count | Properties |
|------|-----------|-------|------------|
| DECIDED  | Judge → Case | 1,264 | — |
| PARTY_IN | Party → Case | 1,309 | role (appellant/respondent/…) |
| CITES    | Case → Act   | 2,749 | **section** (the cited section) |
| ABOUT    | Case → Topic | 3,041 | — |

**Why section is on the edge:** one act (e.g. Indian Penal Code) is cited under
many sections. Modelling `Act` as the node and keeping `section` on the `CITES`
edge lets us answer both "which act is cited most" and "which section of which
act is cited most" without a separate `LegalSection` node.

## Optional: semantic search
`etl.loader --embed` embeds each Case's `summary` (from `summaries.csv`) with
`sentence-transformers` (1024-dim) and stores it as `Case.embedding` for cosine
k-NN search — the in-engine equivalent of the reference demo's pgvector layer.

## Data source
- **Dataset:** `Shreyasrao/Indian-law-supreme-court-judgements-2016` (rev `e928c72019d6`), HuggingFace.
- **Origin:** Indian Supreme Court Judgments registry on AWS Open Data, managed by Dattam Labs.
- **License:** CC-BY-4.0.
- **Coverage:** 2016 (plus one 2017 spill-over bundle in the source PDFs).

## Not modelled (dataset has no such data)
- **Court** — all judgments are from the one Supreme Court, so no Court node.
- **Precedent citations** (Case → Case) — the dataset cites *statutes/sections*, not other judgments.
