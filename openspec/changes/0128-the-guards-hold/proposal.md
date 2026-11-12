---
bump: patch
after: [0127-green-main]
debt: [0123·R2]
---

# The guards hold

The suite's guards are made to see what they were written to see: each one that passes blind is widened, and its twin goes red without it.

Reading map: [design](design.md) holds the decisions, the tables the phases read and the cost of the tests, [tasks](tasks.md) the binding guard, the exemptions, then the guards that pass blind.

## Why

The refactor that follows leans on the gate to say when it broke something. An audit found guards that stay green when the thing they hold is gone: a binding guard that reads no scenario's key or layer, a history pattern for change ids this repository no longer writes, a tripwire that reads one writer of four, a parse that drops a principle when its heading moves one level.

```
today                                   after

guard ──▶ reads a slice ──▶ green       guard ──▶ reads the whole ──▶ green
          (the rest unseen)                       a twin is red without it
```

## What Changes

Edits to tests, one test-side data table, goldens for an edit, a placement and a session record, and the comments of `pyproject.toml` and the drift workflow. No product file moves.

- `tests/test_spec_bindings.py` reads each scenario's key and layer, holds a key to a test on its own layer, refuses a blank exemption reason and a key whose every test is skipped.
- A symlink case in `tests/test_run_directory.py` holds the containment key on a case-sensitive filesystem, and `tests/test_field_map.py` reads `FILED`, not the gitignored runs.
- An exemption reason is `structural: <rule>` or `structural: twin of <test>`, and the reasons off both are reworded.
- The behaviour tests exempt as structural that fit an existing scenario are bound to it, and the rest are listed in a table that may only shrink.
- The history pattern in `tests/test_spec_prose.py` reads this repository's change ids and versions, and reaches `pyproject.toml` and the workflows, whose citations are removed.
- The principles parse, the anchors, the artifact scan, the writer tripwires, the surface's import scan, the schema-order scan and the ONNX telemetry scan each learn what they missed, with a twin.
- Goldens pin the whole bytes of an edit, a placement and a session record.

No requirement is touched, so the delta is empty and `.openspec.yaml` carries `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- Guards edited, with their twins: `tests/test_spec_bindings.py`, `tests/test_spec_prose.py`, `tests/test_principles.py`, `tests/test_package_paths.py`, `tests/test_artifact_bytes.py`, `tests/test_ui.py`, `tests/test_sheet_schema.py`, `tests/test_wd14.py`, `tests/test_run_directory.py` and `tests/test_field_map.py`.
- Goldens added: `tests/golden/edit.json`, `tests/golden/placement.json` and `tests/golden/session.json`.
- Exemption reasons reworded or rebound in `tests/test_ollama.py`, `tests/test_manifest.py`, `tests/test_ui_api.py`, `tests/test_resume.py`, `tests/test_infra.py`, `tests/test_edit.py`, `tests/test_render.py`, `tests/test_pipeline_cli.py` and the other test files [design](design.md#d5) lists.
- Comments reworded in `pyproject.toml` and `.github/workflows/drift.yml`.
- Read and not edited: `tests/e2e/`, `docs/principles.md`, `tests/test_edit_placement.py` and `tools/derive_field_map.py`.
- No format version moves, no verb or flag is deprecated, and the product is the same for the same inputs, so the change meets each condition of a patch in [CONTRIBUTING.md](../../../CONTRIBUTING.md).
- No dependency is added.
- The debt card `0123·R2` is paid: the form check and the table of [D5](design.md#d5) and [D6](design.md#d6) hold the exemptions it names, with a twin that goes red.

## Not in this change

- The mis-bound scenarios, and the new scenarios the shrink-only table of [D6](design.md#d6) points to — the *spec audit*.
- The tattoo screens' browser tests — *e2e tattoo*.
- The tests CI skips for want of the vocabulary or the placement models.
- The ratchets, the stage rule, the importer tables and the frozen files: the next version of this series.
- Stale claims in product comments and the image-frozen `Dockerfile`: the refactor version that edits each file.
