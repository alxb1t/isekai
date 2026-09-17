# No spec delta

**This change alters no requirement and no scenario** — which is the same statement as its own claim,
*nothing a user can observe*. The six verbs, every flag, every artifact format and every byte on disk
are unchanged.

Nine `openspec/specs/*/spec.md` files **are** edited, and none of those edits is a delta:

- **`Source:` and `Tests:` lines**, in all nine. The restructure moves every `isekai/*.py` into a group
  directory, so every path goes stale at once.
- **Two preambles.** `cli` names a model selection and dial flags that do not exist; `comfy-transport`
  points at `isekai/pipeline.py` and `tests/test_polling.py`, **both real and both deleted together in
  `8baf2b3` at v0.14** — a stale pointer rather than a fiction, so the fix is a redirect.

**The delta format cannot express either.** A delta carries `## ADDED` / `## MODIFIED` /
`## REMOVED Requirements` containing `### Requirement:` and `#### Scenario:` blocks. There is no
construct for a preamble or a metadata line. Those files are therefore edited directly, in phase 8.

**Do not invent a requirement to satisfy the validator.** `.openspec.yaml` declares `skip_specs: true`
beside `schema: spec-driven`; both keys are load-bearing.

→ `proposal.md` — Capabilities · `design.md` — D10

> **Why this file is not `specs/README.md`.** The validator treats **every** file under `specs/` as a
> delta spec, so an explanation placed there fails `--strict` with *"skip_specs is set but spec files
> exist"*. `0001-mf-standard`'s `.openspec.yaml` points at a `specs/README.md` it never had.
