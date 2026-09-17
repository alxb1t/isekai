# Tasks — 0016 flow registry

## Progress

- [x] 1 — The detectors, written while the anchors are still correct
- [x] 2 — `validate` leaves `sheet`, and the last stage→stage import with it
- [x] 3 — The fold: five flat files, eight keys, and the one-time re-pin
- [x] 4 — The code stops assuming eleven node roles
- [x] 5 — `--flow` is required and repeatable on every stage verb
- [x] 6 — The run layout: input above, flow below
- [x] 7 — Resume stops assuming a PNG
- [ ] 8 — The living spec, the docs, and the blast-radius sweep

## The per-phase ritual

Every phase, without exception:

1. `make gate` green — all five commands. **Never weaken the gate to pass.**
2. A `CHANGELOG.md` entry under `## [Unreleased]`.
3. The phase's box ticked **in this file**, in that phase's own commit.
4. One Conventional Commit, staged **by name**, carrying `Change: 0016-flow-registry`.

**No phase is metered.** There is no render in this change; no pod goes up, and none may. There are no
live runs to migrate — `RUNS_ROOT` is `.data/runs` and it does not exist — so nothing on disk outside
the repository is touched.

**Every verification below is a command.** Run it; do not describe it.

---

## 1. The detectors, written while the anchors are still correct

> Two tests pin a path the fold is about to change, and only one of them can fail. `test_caption.py:197`
> asserts against a record the code produced; `test_run_directory.py:324` and `:335` assert against a
> record **the test constructs itself**, so they stay green while the code writes something else.
> Design D7. This phase makes them able to fail, before anything moves — the shape v0.15 used for
> `DATA_ROOT`. It is **not** the fold, and it changes no production code.

- [x] 1.1 Rewrite `tests/test_run_directory.py:311-338` so the producer record under assertion is
      produced by `claude_cli.instructions_record`, not built inline. Verify:
      `uv run pytest tests/test_run_directory.py -k briefing -q` — passes.
- [x] 1.2 Prove the new test can fail: temporarily change `briefings/caption.md`'s path in a scratch and
      confirm red. Verify: `uv run pytest tests/test_run_directory.py -k briefing -q` — **fails**, then
      revert. *A check that cannot fail is not a check.*
- [x] 1.3 Fix `test_no_second_ordering_is_defined_anywhere_else` (`tests/test_sheet_schema.py:64-73`):
      it globs `(root / "isekai").glob("*.py")`, which since v0.15's six-group restructure reaches only
      `__init__.py` and `__main__.py` — so `carriers == []` has been **vacuously true** for a day.
      Change it to `rglob("*.py")`. Verify:
      `uv run pytest tests/test_sheet_schema.py -k no_second_ordering -q` — passes, **and** the globbed
      list is non-empty: `uv run python -c "from pathlib import Path; print(len(list(Path('isekai').rglob('*.py'))))"`
      — greater than `20`.
- [x] 1.4 Verify the gate: `make gate`

## 2. `validate` leaves `sheet`, and the last stage→stage import with it

> `review.py:56` imports and calls `sheet.validate` — the sixth of six such edges and the only one
> v0.15 did not close. Design D8. It lands before the fold because it is small, pure and reviewable on
> its own, and because phase 3 edits the same function's body anyway.

- [x] 2.1 Create `isekai/shared/fields.py` holding `validate` verbatim, and its `__init__.py` entry if
      the group needs one. Verify: `uv run python -c "import isekai.shared.fields"` — exits `0`.
- [x] 2.2 Repoint `isekai/pipeline/sheet.py:390`, `isekai/pipeline/review.py:56` and
      `tests/test_sheet_schema.py:20`. Verify:
      `grep -rn 'from isekai.pipeline' isekai/pipeline/` — **no output**.
- [x] 2.3 Confirm no new package cycle: Verify:
      `grep -n 'from isekai' isekai/shared/fields.py` — names `foundation` and `shared` only, never
      `pipeline` or `interface`.
- [x] 2.4 Verify the gate: `make gate`

## 3. The fold: five flat files, eight keys, and the one-time re-pin

> The version's centre. Design D1, D2, D3, D4. **Flat, not nested** — `manifest_digest` filters on
> `path.is_file()`, so a sub-directory would leave the schema and both briefings outside the freeze with
> the gate green. The digest moves once, under the exception D2 records; the message at
> `tests/test_flow.py:256` gains no escape clause.

- [x] 3.1 Move the three files in, renaming both briefings to say they are briefings:
      `schemas/identity.v1.json` → `flows/summon-v1/schema.json` ·
      `schemas/identity.v1.briefing.md` → `flows/summon-v1/sheet.briefing.md` ·
      `briefings/caption.md` → `flows/summon-v1/caption.briefing.md`. Verify:
      `ls flows/summon-v1/ && test ! -e schemas && test ! -e briefings && echo gone` — five files, then
      `gone`.
- [x] 3.2 Strike `version` and `vocabulary` from `schema.json`, leaving `{name, fields}`. Verify:
      `uv run python -c "import json;print(sorted(json.load(open('flows/summon-v1/schema.json'))))"` —
      `['fields', 'name']`.
- [x] 3.3 Rewrite `flow.json` to eight keys: delete `"schema"` and `"graph"`, rename `schema_version` to
      `manifest_version` and set it to `2`, and make `"models"` a list of `{dest, sha256}` taking each
      digest from `scripts/models.json`. Verify:
      `uv run python -c "import json;d=json.load(open('flows/summon-v1/flow.json'));print(sorted(d), d['manifest_version'])"`
      — the eight keys and `2`.
- [x] 3.4 Update `isekai/foundation/flow.py`: `REQUIRED` loses `schema` and `graph`, gains
      `manifest_version`; `FLOW_SCHEMA_VERSION` becomes `MANIFEST_VERSION = 2`; the five filenames become
      constants; `load_flow` refuses a missing sibling naming it; `Flow.schema` is deleted. Verify:
      `uv run pytest tests/test_flow.py -q` — green.
- [x] 3.5 Delete `schema_path()`, `SCHEMAS_DIR`, `BRIEFINGS_DIR`, both `BRIEFING_PATH` constants,
      `sheet.SCHEMA_VERSION` and `_matching_flows`; repoint `wiring.py` to resolve a flow's schema and
      briefings from its own directory, and the four test modules that import the deleted names —
      `tests/test_caption.py:32`, `tests/test_sheet_stage.py:26`, `tests/test_sheet_schema.py:19`,
      `tests/test_package_paths.py:40`, all of which fail at **collection**. Verify:
      `grep -rn 'SCHEMAS_DIR\|BRIEFINGS_DIR\|BRIEFING_PATH\|schema_path\|_matching_flows' isekai/` — no
      output; and `grep -rn 'SCHEMA_VERSION' isekai/` — `isekai/foundation/run.py` only.
- [x] 3.6 Update `tests/test_package_paths.py:37-58`, dropping the `schemas/` and `briefings/` anchors.
      Verify: `uv run pytest tests/test_package_paths.py -q` — green.
- [x] 3.7 Teach `_scratch()` (`tests/test_flow.py:45`) to copy **all five** files, or `:271`'s assertion
      becomes accidentally true. Verify: `uv run pytest tests/test_flow.py -k scratch -q` — green.
- [x] 3.8 Add the test that a **sixth** file in a flow directory moves its digest. Verify:
      `uv run pytest tests/test_flow.py -k a_new_file -q` — green.
- [x] 3.9 Add the digest binding: every `{dest, sha256}` a flow declares equals `scripts/models.json`'s
      entry for that destination, and a disagreement fails naming the flow. Verify:
      `uv run pytest tests/test_flow.py -k models -q` — green.
- [x] 3.10 Re-pin `PINNED` (`tests/test_flow.py:34`) to the new digest, with a comment naming this change
      and the distinction — *the configuration did not change; the manifest's format did.* **Do not edit
      the failure message at `:256`.** Verify: `uv run pytest tests/test_flow.py -k digest -q` — green.
- [x] 3.11 Verify the gate: `make gate`

## 4. The code stops assuming eleven node roles

> `build_graph` performs eleven lookups across ten call sites, none guarded, and `load_flow` checks only
> that the key `nodes` exists. A flow declaring fewer passes the entire gate and dies on a rented pod —
> after `upload_image` has spent it. Design D9.

- [x] 4.1 Add `REQUIRED_NODES = ("positive", "negative", "latent", "sampler")` to
      `isekai/foundation/flow.py` and check it in `load_flow`, refusing naming the missing role. Verify:
      `uv run pytest tests/test_flow.py -k required_nodes -q` — green.
- [x] 4.2 Guard the seven optional lookups in `generate.py:273-323` — `photo`, `scale`, `identity`,
      `openpose`, `clip_skip`, `hires_resize`, `hires_sampler`. Verify:
      `uv run pytest tests/test_generate.py -q` — green.
- [x] 4.3 Gate `upload_image` (`generate.py:361`) on `"photo" in flow.inputs`, giving `Flow.inputs` its
      first production reader. Verify: `uv run pytest tests/test_generate.py -k upload -q` — green.
- [x] 4.4 Add the `tmp_path` fixture flow declaring only the four required roles, and drive it through
      `build_graph` and `render`. **It does not go in `flows/`.** Verify:
      `uv run pytest tests/test_generate.py -k fewer_roles -q` — green; and
      `ls flows/` — `summon-v1` only.
- [x] 4.5 Verify the gate: `make gate`

## 5. `--flow` is required and repeatable on every stage verb

> Today it reaches three of six verbs, is a single string that silently keeps the last occurrence, falls
> back to every tracked flow, and **has no test coverage at all** — one hit in the suite and it asserts
> a refusal string.

- [x] 5.1 Declare `--flow` with `action="append"` and `required=True` on all five stage verbs, and delete
      `_flows_for`'s fallback in favour of a refusal listing the tracked flows. Verify:
      `uv run python -m isekai caption --help | grep -c -- --flow` — `1`; repeat for `sheet`, `review`,
      `approve`, `generate`.
- [x] 5.2 Resolve every named flow against `flows/` at selection, refusing an untracked one by name.
      Verify: `uv run pytest tests/test_pipeline_cli.py -k untracked -q` — green.
- [x] 5.3 Correct the flag's help text and `README.md:138`, both of which say *"every approved one by
      default"* — the fallback was every **tracked** flow. Verify:
      `grep -rn 'every approved one' isekai/ README.md` — no output.
- [x] 5.4 Add the coverage the flag has never had, including two flows in one invocation. Verify:
      `grep -rn -- '--flow' tests/ | wc -l` — greater than `5`.
- [x] 5.5 Verify the gate: `make gate`

## 6. The run layout: input above, flow below

> The largest mechanical edit in the change and it lands alone. The six directory **names** are in
> `run.py:93-98`; the **shape** is at seven call sites across five files, because `Run.directory(*parts)`
> is a variadic `joinpath` that enforces nothing. ~60 hard-coded path assertions across 8 test files
> fail loudly. Design D6, D10.

- [x] 6.1 Change `run_id` (`run.py:143`) and `_run_for`'s prefix (`:220`) to `<12 hex>_<slug>`, and
      update `slug()`'s docstring, which states the separator. Verify:
      `uv run pytest tests/test_run_directory.py -k run_id -q` — green.
- [x] 6.2 Move every stage's path construction to `runs/<input-id>/<flow-id>/<stage>/`, including
      `caption.py:155`, which is the one that is flat today. Verify:
      `uv run pytest tests/test_run_directory.py tests/test_resume.py -q` — green.
- [x] 6.3 Update `run_view.py:38-43`'s per-flow-ness table and its bespoke outputs walk at `:124-134`.
      Verify: `uv run pytest tests/test_run_view.py -q` — green.
- [x] 6.4 Rewrite the hard-coded assertions across `test_resume.py`, `test_generate.py`,
      `test_review.py`, `test_caption.py`, `test_run_view.py`, `test_sheet_stage.py`,
      `test_run_directory.py` — including `test_review.py:374`, which hard-codes the **depth** as
      `parent.parent.parent`. Verify: `uv run pytest -q` — 600+ green.
- [x] 6.5 Confirm nothing writes above the flow split but the input and its frame. Verify:
      `uv run pytest tests/test_run_directory.py -k layout -q` — green.
- [x] 6.6 Verify the gate: `make gate`

## 7. Resume stops assuming a PNG

> `rendered_seeds` (`generate.py:227`) filters on `path.suffix == ".png"`. The output path already
> generalises; the predicate does not. **This change owes exactly that and no more.** Design D11.

- [x] 7.1 Derive the extension from what the flow declares it produces, and delete the literal. Verify:
      `grep -n '"\.png"' isekai/pipeline/generate.py` — no output.
- [x] 7.2 Verify: `uv run pytest tests/test_resume.py -q` — green.
- [x] 7.3 Verify the gate: `make gate`

## 8. The living spec, the docs, and the blast-radius sweep

> The phase that catches what no gate command reads. **v0.15 shipped a broken `Dockerfile` COPY exactly
> here**, because the sweep hunted the modules being renamed and never asked what referenced the ones
> that merely moved.

- [ ] 8.1 Update `openspec/specs/sheet/spec.md:8`'s `Source:` line, which names
      `schemas/identity.v1.json` and `schemas/identity.v1.briefing.md`, and every other capability's
      `Source:` line this change invalidates. Verify:
      `git grep -nE 'schemas/|briefings/' -- openspec/specs/` — no output.
- [ ] 8.2 Update `README.md:187-217`'s repository tree, `README.md:198-199`'s flow description and
      `CLAUDE.md:166-169`'s flow-directory paragraph — all three describe a flow as two files. Verify:
      `grep -n 'caption.briefing.md' README.md CLAUDE.md` — both hit.
- [ ] 8.3 Update `isekai/pipeline/README.md:13`, `isekai/foundation/README.md:12`,
      `isekai/interface/README.md:11` and `isekai/shared/README.md` — the last gains `fields.py`. Verify:
      `grep -rn 'fields.py' isekai/shared/README.md` — one hit.
- [ ] 8.4 **The sweep.** `CHANGELOG.md` is history and `openspec/changes/` describes the move itself,
      so both are excluded — everything else is in scope, including files no gate command reads. Verify:
      `git grep -nE 'schemas/|briefings/|identity\.v1' -- . ':!CHANGELOG.md' ':!openspec/changes'`
      — **no output.**
- [ ] 8.5 Confirm the files no gate command reads are clean. Verify:
      `grep -nE 'schemas|briefings' Dockerfile scripts/download_models.sh start.sh Makefile docker-compose.yml .github/workflows/*.yml infra/*.sh` — no output.
- [ ] 8.6 Confirm the import graph claim this change makes true. Verify:
      `grep -rn 'from isekai.pipeline' isekai/pipeline/` — no output.
- [ ] 8.7 Verify: `openspec validate 0016-flow-registry --strict` — green.
- [ ] 8.8 Verify the gate: `make gate`
