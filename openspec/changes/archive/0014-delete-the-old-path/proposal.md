---
version: v0.14
---

## Why

v0.13 shipped the staged pipeline beside the old one and suspended the repository's
own rule — *"There is one path. A version may replace it; it may not add a second"* —
for exactly one version. **This version discharges that suspension.**

The old path is not deleted because the new one beat it. It is deleted because it
**cannot enter the registry L3 defines**: a selectable implementation is a measured
one, and `workflows/pipeline.json` was measured on style and rejected, and never
measured on identity at all. Every identity figure in this project — F37 5/6, F40
8/10, F41 14/17, F47 10/10 person-level — belongs to the flow that became
`summon-v1`. The old path has none.

The supporting evidence is **F24**: against the old architecture's *best tuning*
(`notile-d045` — `tile 0.0`, `denoise 0.45`, a candidate that was never shipped),
`fromnoise-v1` renders **0.0240** median linework to its **0.0043**, on the same six
subjects, each read at its own photograph's canvas. **That comparison covers style
and nothing else. No identity comparison between the two paths exists, on either
instrument.** The record must say so rather than imply a head-to-head that was never
run.

Carrying it a version longer is the failure the original one-path rule was written
against — and it would mean building v0.15, the riskiest version in the arc, against
a tree holding 149 dead tests, a `cli` capability describing flags that no longer
exist, and a deviation nobody wrote down again.

## What Changes

- **BREAKING — `convert.py photo.jpg` is deleted**, with `isekai/cli.py`,
  `isekai/pipeline.py`, `isekai/mutate.py`, `isekai/overrides.py`,
  `workflows/pipeline.json` and `workflows/pipeline_ui.json`. There is one render
  path: `python -m isekai … generate`, flow `summon-v1`.
- **`isekai/workflow.py` becomes `isekai/photo.py`.** Injection dies;
  the JPEG/PNG header walk, the EXIF transpose, `image_dimensions` and
  `working_resolution` survive as what they always were — *what is this photograph,
  and what render target does it imply*. No ComfyUI graph is touched by what remains,
  so `workflow` is a name that would lie.
- **The 4:1 target ceiling is restored to the surviving path.**
  `MAX_TARGET_LONG_SIDE` is enforced only inside `inject`; `generate.py`'s
  `photo_resolution` has never applied it. **This is a live gap on `main` today, not
  a regression this change introduces** — and deleting `inject` is what makes it
  permanent unless it moves. It moves, as a `Refusal` rather than a `sys.exit`, so a
  batch survives one extreme photograph.
- **The living spec goes 11 → 9 capabilities.** `workflow-injection` and
  `workflow-mutation` are **replaced, not renamed**. Nine survive:
  `cli`, `run-directory`, `caption`, `sheet`, `review`, `image-generation`,
  `comfy-transport`, `evaluation`, `model-provisioning`.
- **`--runs` can no longer write inside the repository working tree.** It is a free
  `type=Path` today, and the comment beside it claims a containment check that exists
  nowhere; `run.py` copies the photograph into the run directory by construction. Any
  path *outside* the repository is still accepted — the flexibility is the point, and
  the working tree is the only place it was ever dangerous.
- **`infra/up.sh` gains the bounded readiness wait** already proven on the prototype
  branch — a 420 s deadline that tears the pod down itself on timeout. `main`'s poll
  is `while true` with no deadline: the one thing here that can bill indefinitely
  while looking like it is working. **The prototype's HTTP-proxy fallback is
  deliberately not taken** — it opens a public, unauthenticated ComfyUI.
- **`CLAUDE.md`'s one-path bullet is replaced by L3's entry gate, not restored.**
  A count would forbid the flow registry v0.16 adds.
- **The README's work-in-progress banner names no version**, and every runnable
  command in the file becomes the six verbs.

## Capabilities

### New Capabilities

<!-- None. Every surviving contract already has an owner. -->

### Modified Capabilities

- `cli`: **30 scenarios REMOVED** — every requirement belonging to `convert.py`'s
  surface — and **one MODIFIED and RENAMED**: the pipeline surface was specified as a
  *second* entry point standing beside the render surface and leaving it unchanged,
  which is a clause about a surface this version deletes. It becomes the only entry
  point. Of `convert.py`'s own requirements the honest count of survivors is still
  zero, and the three the vault records as surviving do not.
- `model-provisioning`: **MODIFIED** — the completeness rule is stated over
  `workflows/pipeline.json` by name, and that file is deleted here. It is restated
  over a tracked flow's graph, which is what the bound test already reads.
- `image-generation`: **ADDED** — the nine surviving working-resolution scenarios,
  rekeyed here as the capability that owns *"the render target is derived from the
  photograph's own header"*; the 4:1 refusal; the seed's 64-bit width, whose only
  binding today dies with `workflow-mutation`; and one scenario that is new rather
  than migrated — that the dimensions are *read* from the photograph's own frame
  header, which is the half of `dimensions-are-written-by-injection` that survives
  its writer.
- `run-directory`: **ADDED** — a run root is under the ignored root or outside the
  repository entirely. Design decision D14 was never a requirement, which is why the
  comment could contradict it for a whole version.
- `comfy-transport`: **MODIFIED** — the polling and retrieval scenarios keep their
  text and lose their only test with `pipeline.py`. Their source becomes
  `isekai/generate.py`.
- `evaluation`: **MODIFIED** — `evaluation:canvas:resolution-comes-from-the-injector`
  names the injector in its own THEN clause. One scenario, reworded to name the
  render path. The report requirement is **not** touched: two of its five tests
  drive the deleted pipeline and go with it, and the other three hold the scenario
  on their own (design.md D13).
- `workflow-injection`: **REMOVED** — 14 of 23 scenarios. The nine that survive move
  to `image-generation`.
- `workflow-mutation`: **REMOVED** — 43 of 44 scenarios. `seed-is-64-bit` moves.

## Impact

**Deleted:** `convert.py` · `isekai/cli.py` · `isekai/pipeline.py` ·
`isekai/mutate.py` · `isekai/overrides.py` · `workflows/` · `tests/test_cli.py` ·
`tests/test_variations.py` · `tests/test_mutation.py` · `tests/test_overrides.py` ·
`tests/test_polling.py` · `comfy_types.Overrides`.

**Renamed:** `isekai/workflow.py` → `isekai/photo.py`, minus injection.

**Edited:** `tests/conftest.py` (the `workflow` fixture is repointed at
`flows/summon-v1/graph.json`) · `tests/test_workflow_injection.py` (splits: 41 header
tests survive, 21 die) · `tests/test_manifest_binding.py` (3 LineArt/Tile tests) ·
`tests/test_infra.py` (2 annotator-count tests) · `tests/test_evaluate.py` (3 tests
deleted: the `-S` guard on `convert`, and two driven by the deleted pipeline) ·
`isekai/__main__.py` · `isekai/evaluate.py` and `isekai/generate.py` (one import line
each) · `scripts/models.json` and `scripts/derive_manifest.py` (four artifacts and
three publishers are orphaned by the old graph's deletion, ≈2 GB) · `infra/up.sh` ·
`pyproject.toml` · `.gitignore` (`outputs/` goes; `.inputs/` stays — it still has a
reader in `baseline/build_contact_sheets.py:107`) · `README.md` · `CLAUDE.md`
(13 sites) · `CHANGELOG.md`.

**Tests:** 726 today → **146 die, 583 land** after the three rebound and moved tests,
rising to **590** as phases 3 and 4 add their own, and to **591** with the regression
test converge round 1 adds for `up.sh`'s teardown path.

**Not touched:** every stage module · `isekai/run.py` · `isekai/flow.py` ·
`isekai/provision.py` · `isekai/comfy_client.py` · `isekai/eval_backends.py` ·
`flows/summon-v1/` · `schemas/` · `briefings/` · `probe/` · `baseline/`.

**Dependencies:** none added or removed. `dependencies = []` holds.

**Deviation closed.** v0.13 stated two: that it carried both paths, scoped to itself,
and that the one-path bullet would be replaced by an entry gate. It discharged
neither — the first lapses only when the old path is deleted, and the second was
declared and never performed. **This version does both**, in `CLAUDE.md`, in as many
words.
