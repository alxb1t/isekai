---
version: v0.16
---

## Why

**A flow is meant to be the complete, frozen specification of how an input becomes an image, and it is
not one.** Its schema and both briefings live at the repository root and are loaded once per *build*,
so every flow in the registry gets the same ones; `build_graph` looks up eleven node roles
unconditionally, so a flow declaring fewer passes the entire suite and dies on a rented GPU; `--flow`
reaches three of six verbs, is a single string where it should be repeatable, and silently falls back
to every tracked flow; and the run directory nests stage-first, so a second flow scatters four entries
across four stage directories instead of adding one subtree.

**Two of those are worse than untidy.** A flow's model weights are declared as bare destination paths
with their digests in `scripts/models.json`, joined by a path string — so re-pinning a checkpoint
changes what a frozen flow renders, under the same flow identifier, **with the gate green**. And a
caption is keyed on nothing but the run, so a second flow silently inherits a reading written to answer
a different question.

**Now, because the next version is a directory.** v0.17 adds `conjure-v1` and changes no code. That is
only true if this version makes it true.

## What Changes

- **A flow becomes five flat files.** `schema.json`, `caption.briefing.md` and `sheet.briefing.md` land
  in `flows/<id>/` beside `flow.json` and `graph.json`. `schemas/` and `briefings/` leave the
  repository root. **Flat, not nested**: `manifest_digest` filters `directory.iterdir()` through
  `path.is_file()`, so a subdirectory would leave the freeze silently not covering them.
- **BREAKING — `flow.json`'s format.** Eight keys, naming none of its siblings: `flow` ·
  `manifest_version` · `inputs` · `vocabulary` · `prompt` · `dials` · `nodes` · `models`. `"schema"`
  and `"graph"` are deleted, `schema_version` is renamed `manifest_version` and bumped to **2**.
- **BREAKING — a flow pins its own model digests.** `"models"` becomes `[{dest, sha256}, …]`, and the
  gate compares those digests against `scripts/models.json` rather than only the paths.
- **`Schema` loses `version`.** Inside a frozen directory it protects nothing; a changed field list is
  a new flow.
- **BREAKING — a flow shares nothing.** Caption sharing and sheet sharing are **removed**, not
  relocated. `captions/` moves inside the flow subtree; `_matching_flows` is deleted.
- **BREAKING — the run layout.** `runs/<input-id>/<flow-id>/{captions,sheets,review,prompts,outputs}`,
  and the run id becomes `<12 hex>_<slug>` — an underscore, because a slug is hyphenated and the
  boundary was unreadable.
- **BREAKING — `--flow` is required and repeatable on all five stage verbs.** Today it is optional, a
  single string, and absent from `caption` and `sheet`.
- **Eleven unconditional node-role lookups become four required and seven guarded.** `positive`,
  `negative`, `latent` and `sampler` are checked in `load_flow`; the rest are guarded in `build_graph`.
  `flow.inputs` gets its first production reader, gating the photograph upload.
- **The last stage→stage import is retired.** `sheet.validate` moves to `isekai/shared/fields.py`.
- **Resume stops assuming a PNG.**
- **A one-time digest re-pin**, recorded as an explicit exception: the flow's configuration did not
  change; its manifest's format did.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `image-generation`: the flow directory's shape, the manifest's keys, model pinning by digest, and
  the node roles a render may assume.
- `sheet`: a schema is a field list with no version and lives inside its flow; the one-fill-serves-
  every-matching-flow requirement is removed.
- `caption`: a caption belongs to one flow; the flow-neutral reuse scenario is removed. The reader
  still receives only the photograph and its standing instructions.
- `cli`: `--flow` is required and repeatable on every stage verb.
- `run-directory`: the layout is input-first and flow-second, the run id's shape is stated, and
  captions sit inside the flow.

## Impact

| | |
|---|---|
| **`flows/summon-v1/`** | 2 files → 5, flat; `flow.json` rewritten; the committed digest re-pinned once |
| **repository root** | `schemas/` and `briefings/` deleted |
| **`isekai/`** | `pipeline/sheet.py`, `pipeline/caption.py`, `pipeline/review.py`, `pipeline/generate.py`, `foundation/flow.py`, `foundation/run.py`, `interface/cli.py`, `interface/wiring.py`, `interface/run_view.py`; one new module, `shared/fields.py` |
| **deletions** | `schema_path()` · `SCHEMAS_DIR` · `BRIEFINGS_DIR` · both `BRIEFING_PATH` · `sheet.SCHEMA_VERSION` · `_matching_flows` · `flow.json`'s `"schema"` and `"graph"` |
| **`tests/`** | ~60 hard-coded layout assertions across 8 files; `test_package_paths.py`'s anchor table; `_scratch()` must copy all five files; a new `tmp_path` fixture flow declaring fewer roles |
| **`openspec/specs/`** | five capabilities — requirements and `Source:` lines |
| **`CLAUDE.md`, `README.md`** | the repository-layout tree and the flow-directory paragraph |
| **dependencies** | none. The runtime stays stdlib-only |
| **not touched** | `Dockerfile`, `scripts/download_models.sh`, `start.sh`, CI, `infra/`, the gate array — **verified by `git grep`, not assumed**; `scripts/models.json` keeps its shape |
