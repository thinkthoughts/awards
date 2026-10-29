# RPI-1: Reading Point Identifiers

An **RPI** identifies one L2 mathematical reading, not an award, manuscript, repository, or release. The existing `RP-` identifiers and JSP catalog are retained. The frozen `survey/data/rpi-crosswalk.json` assigns `RPI-000001` onward to the existing readings, preserving their existing order. Never renumber this crosswalk.

New readings receive an embedded `rpi` and legacy-compatible `id` (`RP-RPI-0000NN`). The allocator uses the largest existing RPI; it never reuses retired identifiers. Do not concurrently run onboarding on two branches without resolving ID collisions during merge.

## Source types and identity

`kind` can be `foundational`, `jsp`, `arxiv`, `news`, `repository`, `other`. New external readings carry `origin` (source type, canonical HTTPS URL, external identifier, title; optional source pin/retrieval date) and a distinct `source_review` (`discovered`, `reviewed`, `disputed`, `superseded`). Repository and publication IDs are provenance, not the reading's identity. Distinct mathematical statements from the same repository may require multiple readings; the CLI treats the pair (source kind, external identifier) as unique, allowing claim-specific identifiers to share one repository URL. It does not automatically extract or verify claims.

The mathematical/formalization/verification state axes remain independent. Intake starts as `open` / `prose` / `unverified`, where **open describes unproved status in the registry, not a verdict on the source claim**. A future phase should add a separate `reported` mathematical state for news. Source review is never proof evidence. No declaration is claimed until it has been checked and connected to evidence.

## Intake

First register or reuse an L1 `SPEC-...` whose hypotheses and statement actually fit the reading. Then run:

```sh
python3 survey/scripts/onboard_reading.py --kind repository \
  --url https://github.com/example/repository --external-id example/repository \
  --title 'An example reading' --spec SPEC-nat-add-one \
  --statement 'A statement associated with this reading' --dry-run
```

Remove `--dry-run` to write `registry/readings.json`; then validate:

```sh
python3 survey/scripts/validate_registry.py --quiet
python3 -m unittest discover -s survey/tests -v
```

This command is an illustrative *syntax* example, not a recommendation to associate an unrelated source with `SPEC-nat-add-one`. Do not use that specification for DAM or another paper unless its content actually matches. RPI-1 does **not** onboard DAM, rewrite catalog data, or compile Lean. Source extraction, multiple readings per repository, graph edge proposals and richer intake queues are later stages.

## RPI-2: DAM pilot

RPI-000005 (CP6c.1, conditional mean-zero cross-talk), RPI-000006 (CP6c.2, exact conditional expected gap), and RPI-000007 (CP6c.3, open finite second-moment target) cite `thinkthoughts/lean-dense-associative-memory` at commit `f37611f`. The first two use `upstream-reported` evidence from the DAM release report, **not** independent survey kernel or Comparator checks; the third remains unverified. The same repository URL has distinct claim-specific external identifiers. No DAM proof files were copied or rebuilt.
