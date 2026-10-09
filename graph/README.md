# Connection Mapper

Who is linked to whom, through what, when, and on whose evidence. One SQLite file, a document extractor, query commands, and an interactive map.

## Quick start
```bash
python3 extract.py ../BIS_Founders_Report.md --import   # document -> review/BIS_Founders_Report.json -> graph.db
python3 query.py path "Montagu Norman" "Owen Young"      # how are two people connected?
python3 render.py                                        # -> graph.html, open in a browser
```

## Data model
- **Nodes:** person, org, project, account, place, event, document. Aliases handle short forms ("BIS", "Norman").
- **Edges:** employed_at, led, board_of, founded, member_of, worked_on, attended, met_with, corresponded_with, family_of, succeeded, advised, funded, owned, affiliated_with, replied_to, mentioned, cited_in. Each carries role, start, end, source, verbatim quote, confidence, and who added it.
- Rule: **no quote or URL, no edge.** The map is only as good as the evidence behind each line.

## Ways in
| Source | How |
|---|---|
| Research documents, articles, filings, testimony, books | `extract.py DOC [--import]`. Writes a review JSON first; check it, then load. ~$0.05–0.20 per document |
| LinkedIn work histories | `import_apollo.py FILE.json` on Apollo lookups (public professional data, no scraping). Later: a Claude session can call the Apollo connector and save results |
| Hand entry | `db.py add-edge ...` or `db.py import-csv edges.csv` |
| Forum scanner (later) | replied_to / mentioned edges between accounts, then `affiliated_with` from account to person once a source confirms it |

## Questions it answers
- `who NAME`: everything linked to a node, with quotes.
- `path A B`: shortest chain between two nodes.
- `roster ORG [YEAR]`: who was at an institution, optionally in a given year.
- `moves ORG_A ORG_B`: people linked to both (revolving door).
- `overlap A B`: shared institutions, events, projects.
- The map: filter by node and edge type, year range, search, click for evidence, shift-click two nodes for a path.

## Housekeeping
- `db.py merge KEEP DROP` folds duplicates ("Norman" vs "Montagu Norman") when the alias match misses.
- Each document contributes only what it says; contradictions between sources stay visible as separate edges with their own quotes.
- `graph.db`, `review/` and `graph.html` hold investigation data. Local only; not in shared drives or chat.
