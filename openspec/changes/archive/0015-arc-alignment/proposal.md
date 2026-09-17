---
version: v0.15
---

## Why

The record that describes this package was rebuilt and grilled on 2026-09-16, and **the package stopped
describing it**. Three seams live inside other modules, two files are named for the verb that calls them
rather than for what they do, and the living spec points at two files a previous release deleted.

The cost is not tidiness. Every version after this one builds on the package's shape: v0.16 moves the
run layout, v0.18 needs the composition without the argv parser, v0.19 opens five files that are
currently scattered among twenty-two. **Doing the structural work once, here, is what lets each of those
versions carry none of it.**

This is also the version that stops applying the record's own module test selectively. Two extractions
that were scheduled rest on consumers that exist today; one that was scheduled has a single caller and a
single implementation, and does not happen.

## What Changes

**Nothing a user can observe.** Same six verbs, same flags, same artifacts, same bytes on disk.

- **Two extractions.** `write_atomically` out of `run.py` into `atomic_write.py` — it takes a path and
  bytes and knows nothing about runs, and `generate.py:386` already imports it by name to write the
  rendered PNG. `Wiring`, `wiring()` and `_check_run_root` out of `__main__.py` into `wiring.py` — the
  suite already composes the pipeline without a parser, fourteen times (`tests/test_resume.py:49`).
- **One split.** The parser and dispatch move to `interface/cli.py`; `isekai/__main__.py` becomes a
  three-line shim. `python -m isekai` resolves through `runpy` to that path, so the path cannot move.
- **Two renames.** `show.py` → `run_view.py` (`show` is the verb *and* the file). `photo.py` →
  `image.py` (half its callers hand it a render, not a photograph). **The verb `show` does not change.**
- **Two seam moves.** `Schema` from `sheet.py` to `flow.py`; the stage directory-name constants to
  `run.py`. Together these remove **five of the six stage→stage imports**.
- **Eight anchor fixes.** Every `Path(__file__).resolve().parent.parent` — seven files — gains a
  `.parent`, because each file moves one directory deeper.
- **The package becomes six directories** — `foundation`, `pipeline`, `shared`, `boundary`,
  `evaluation`, `interface` — with empty `__init__.py` files and one `README.md` each, plus
  `isekai/README.md`.
- **Nine capability preambles corrected.** Every `Source:` path is invalidated by the restructure, and
  `cli` and `comfy-transport` carry seven prose defects between them.
- **`flow.assemble()` and `multipart.py` are recorded as internal** and do not move.

**Not breaking.** No public interface changes: the package is not distributed, and the CLI surface,
the on-disk layout and every artifact format are untouched.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. **No requirement or scenario changes**, which is the same statement as *"nothing a user can
observe."* The nine `openspec/specs/*/spec.md` files are edited, but only their `Source:`/`Tests:`
metadata and two preambles — and the delta format has no construct for either, expressing only
`ADDED` / `MODIFIED` / `REMOVED` requirements.

This change therefore declares `skip_specs: true` in its `.openspec.yaml`, beside
`schema: spec-driven`. Both keys are load-bearing: without a resolvable schema the marker is read,
rejected, and `openspec validate --strict` fails exactly as if it were absent.

## Impact

| | |
|---|---|
| **`isekai/`** | all 22 files move; 3 new modules; 2 renamed; 7 `README.md`; 7 `__init__.py` |
| **`tests/`** | ~10 import sites; `test_show.py` → `test_run_view.py`, `test_photo.py` → `test_image.py`; `test_run_directory.py:253`'s `run_module.tempfile` monkeypatch must be retargeted |
| **outside the package** | `evaluate.py` (4 import statements), `probe/loader_probe.py`, `scripts/derive_eval_manifest.py` |
| **`pyproject.toml`** | two `[[tool.ty.overrides]]` paths naming `isekai/eval_backends.py` |
| **`openspec/specs/`** | nine files — `Source:`/`Tests:` lines, plus `cli` and `comfy-transport` preambles |
| **`CLAUDE.md`, `README.md`** | the layout section and the repository-layout tree, which attributes four modules' work to `__main__.py` |
| **dependencies** | none. The runtime stays stdlib-only |
| **not touched** | `flows/`, `schemas/`, `briefings/`, `.data/`, `infra/`, `Dockerfile`, the gate array |
