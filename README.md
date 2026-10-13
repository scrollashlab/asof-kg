# AsOf-KG

AsOf-KG is a bitemporal extension for Biolink knowledge graphs. Every statement carries two time dimensions:

- **Valid time:** when the statement holds in the world.
- **Record time:** when a source first published it and, if it applies, when it was withdrawn or superseded.

A query names a record date *k* and a valid date *v*. It is answered only from statements that were in the record at *k*, so no answer can use information published after *k*.

This repository holds the ontology excerpt submitted with a Phase 1 concept paper for the NIH challenge "It's About Time: Temporal Reasoning in Biomedical Knowledge Graphs." It also holds the scripts that check the ontology and run the as-of query.

## Contents

| Path | What it is |
|---|---|
| `ontology/asof-kg.ttl` | OWL 2 DL ontology plus SHACL shapes and a worked example (Turtle). This is the file of record. |
| `ontology/asof-kg.owl` | The same ontology in RDF/XML, converted with ROBOT. |
| `tests/negative/` | Six broken variants. Each must be rejected by SHACL, HermiT or both. |
| `tests/positive/` | One variant that must stay consistent and yield inferred ordering between statements. |
| `scripts/validate.py` | Runs pySHACL, HermiT (through Owlready2) and ROBOT (OWL API) on the ontology and on every test. |
| `scripts/asof_query.py` | Runs the as-of SPARQL query over the worked example for five (*k*, *v*) pairs. |
| `scripts/leakage_check.py` | Runs the same as-of query at every interval boundary in the example, and one second either side, and fails if any answer uses a statement that was not yet in the record, or was already withdrawn, at the query's record date. It also checks each answer against a separate Python version of the interval rule. |
| `output/` | The results of the last run. |

## Worked example

The example uses public U.S. records from 2022:

- FDA issued an emergency use authorization for bebtelovimab on February 11, 2022. On November 30, 2022, FDA announced that bebtelovimab was not currently authorized in any U.S. region, because it was not expected to neutralize the BQ.1 and BQ.1.1 subvariants. The FDA page is no longer online; CDC Health Alert Network update CDCHAN-00483 records the announcement.
- CDC's estimate of the U.S. share of BQ.1.1 for the week ending November 12, 2022 changed from release to release. The example holds three of them: 0.241 in the Nowcast of November 11, 0.184 in the Nowcast of November 18, and 0.164 in the weighted estimate of December 2.

The same question about that week returns 0.241, 0.184 or 0.164, depending on the record date of the query (see `output/asof_query_output.txt`).

## Run it

You need Python 3 and Java 11 or later.

```
pip install -r requirements.txt
./run.sh
```

`run.sh` downloads ROBOT 1.9.11 into `tools/` on first use, then writes the three result files to `output/`.

## Expected results

- SHACL: the base file conforms.
- HermiT: the base file is consistent, under both Owlready2 and ROBOT.
- ROBOT: the file is in the OWL 2 DL profile.
- Negative tests: interval order, leakage, record-before-source and supersede order are caught by SHACL. An ended open interval, a reversed supersession and an assignment with two statuses make the ontology inconsistent under HermiT.
- Positive test: each of the three BQ.1.1 statements is inferred to be valid before, and valid disjoint from, the prediction statement.
- Leakage check: 648 as-of queries (2 subjects, 18 record dates, 18 valid dates), no leaked or withdrawn statement, and every answer matches the Python version. A deliberately broken query with the record-date filter removed fails the check.

## Reused vocabularies

W3C OWL-Time, W3C PROV-O, Biolink Model, BFO 2020, SKOS and SHACL. External identifiers in the example come from ChEBI, MONDO, MeSH, GAZ, NCBITaxon, IAO, STATO and RxNorm.

## AI use

Generative AI tools (Grok) were used extensively to research, draft, edit, and validate this entry, including ontology authoring and software for validation. The entrant directed the work, reviewed it, and is responsible for its content.

## License

The ontology (`ontology/`, `tests/`) is licensed under CC BY 4.0 (`LICENSE-ontology.txt`). The scripts are licensed under the MIT License (`LICENSE-code.txt`).
