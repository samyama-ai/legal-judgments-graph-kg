# Legal Judgments KG — Design Notes

## Node labels
| Label | Key fields |
|-------|-----------|
| Judgment | id, title, date, outcome |
| Court | id, name, jurisdiction, level |
| Judge | id, name |
| Statute | id, title, section |
| Party | id, name, role |
| Citation | id (if modeled as node) |

## Edge types
| Edge | From → To | Meaning |
|------|-----------|---------|
| DECIDED_BY | Judgment → Judge | authoring/deciding judge |
| HEARD_IN | Judgment → Court | court that heard the case |
| INVOKES_STATUTE | Judgment → Statute | statute relied upon |
| INVOLVES_PARTY | Judgment → Party | plaintiff/defendant/etc. |
| CITES | Judgment → Judgment | precedent citation graph |

## Data sources
List each source, license, and what it contributes. Fill in `{{SOURCES}}`.
