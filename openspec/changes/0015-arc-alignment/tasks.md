# Tasks — 0015 arc alignment

## Progress

- [x] 1 — The anchor detectors, written while the anchors are still correct
- [x] 2 — `atomic_write` out of `run`
- [x] 3 — `wiring` out of `__main__`
- [ ] 4 — `cli` out of `__main__`, behind a three-line shim
- [ ] 5 — `show` → `run_view`, `photo` → `image`
- [ ] 6 — `Schema` → `flow`, the layout names → `run`: six stage edges become one
- [ ] 7 — The restructure: 22 files into six directories, seven READMEs
- [ ] 8 — The record: nine capability files, `CLAUDE.md`, `README.md`

## The per-phase ritual

Every phase, without exception:

1. `make gate` green — all five commands. **Never weaken the gate to pass.**
2. A `CHANGELOG.md` entry under `## [Unreleased]`.
3. The phase's box ticked **in this file**, in that phase's own commit.
4. One Conventional Commit, staged **by name**, carrying `Change: 0015-arc-alignment`.

**No phase is metered.** There is no render in this change; no pod goes up, and none may.

**Every verification below is a command.** Run it; do not describe it.

---

## 1. The anchor detectors — written first, while the anchors are still correct

> Seven files compute a repo-root path as `Path(__file__).resolve().parent.parent`. Phase 7 moves each
> one directory deeper and every one silently becomes `isekai/`. Six would fail loudly; **`DATA_ROOT`
> would not** — it becomes `isekai/.data`, `RUNS_ROOT` moves with it, and tests asserting the
> *relationship* between them still pass, while `__main__.py:194`'s `REPOSITORY = DATA_ROOT.parent`
> quietly narrows `_check_run_root` to refuse only paths inside `isekai/`. Design D7.
>
> **These tests are written now, against the correct tree, so they pass today and go red the moment
> phase 7 moves a file without fixing its anchor.** They are the detector, not the fix.
>
> **No shared path module is introduced.** Each file keeps its own expression; phase 7 adds one
> `.parent` to each. A shared constant would need a home every one of those seven could import, which
> is a module this change did not propose and new edges phase 6 exists to remove.

- [x] 1.1 Add `tests/test_package_paths.py` asserting each of the seven repo-root anchors resolves to the directory that contains `pyproject.toml` — `run.DATA_ROOT`, `flow.FLOWS_DIR`, `sheet.SCHEMAS_DIR`, `caption.BRIEFINGS_DIR`, `provision.MANIFEST_PATH` and `VOCABULARY_MANIFEST_PATH`, `eval_models`' manifest path, `claude_cli.ROOT`. Assert the **absolute** property — that the anchor's repo root *is* the repo root — never a relationship between two constants that move together. Verify: `uv run pytest tests/test_package_paths.py -q`
- [x] 1.2 Add the falsification twin: a test proving the assertion in 1.1 **fails** when an anchor is one level short, so the detector cannot be a check that cannot fail. Verify: `uv run pytest tests/test_package_paths.py -q`
- [x] 1.3 Verify the guard these protect is intact before anything moves: `uv run pytest tests/test_run_directory.py -q -k "run_root or containment"`
- [x] 1.4 Verify the gate: `make gate`

## 2. `atomic_write` out of `run`

> Design D4. Justified by `generate.py:386`, not by the evaluator — which this change does **not**
> rewire (root `evaluate.py` has zero test importers; that is v0.19's, with a harness).

- [x] 2.1 Move `write_atomically` (`run.py:156-176`) into `isekai/atomic_write.py`; `run.py` imports it. **`write_json` (`run.py:181`) stays in `run`** — it encodes the run's artifact JSON convention, not a write primitive. Verify: `uv run python -c "from isekai.atomic_write import write_atomically; from isekai.run import write_json; print('ok')"`
- [x] 2.2 Remove `run.py:36`'s now-unused `import tempfile` and retarget `tests/test_run_directory.py:253`'s `monkeypatch.setattr(run_module.tempfile, "mkstemp", ...)` at the new module. Verify: `uv run pytest tests/test_run_directory.py -q -k "temporary_file_shares"`
- [x] 2.3 Verify `atomic_write` took nothing from `run` with it — it must import no first-party module: `grep -c "^from isekai\.\|^import isekai" isekai/atomic_write.py` returns `0`
- [x] 2.4 Verify the gate: `make gate`

## 3. `wiring` out of `__main__`

> The suite is the second consumer: `tests/test_resume.py:49` composes the pipeline with **no parser**,
> and fourteen tests use it. `_check_run_root` has one caller (`wiring()` at `:228`) and travels with it.

- [x] 3.1 Move `Wiring` (`__main__.py:164`), `wiring()` (`:220`) and `_check_run_root` (`:200`) into `isekai/wiring.py`. Verify: `uv run python -c "from isekai.wiring import Wiring, wiring; print('ok')"`
- [x] 3.2 Update the three test import sites — `tests/test_run_directory.py:17`, `tests/test_resume.py:23`, `tests/test_generate.py:467` — to import from `isekai.wiring`. **No compatibility re-export is left behind in `__main__`:** the callers move, the name does not stay. Verify: `grep -rn "from isekai.__main__ import" tests/ | grep -i wiring` is empty
- [x] 3.3 Verify the gate: `make gate`

## 4. `cli` out of `__main__`

> Design D3. `runpy` pins `__main__.py`'s path; it does not pin where the parser lives. `pip`, `black`
> and `flask` all ship this shape.

- [ ] 4.1 Move the parser, the verb table and the dispatch functions into `isekai/cli.py`. Reduce `isekai/__main__.py` to `from isekai.cli import main` / `raise SystemExit(main())`. Verify: `wc -l isekai/__main__.py` is under 10, and `uv run python -m isekai --help` prints the six verbs
- [ ] 4.2 Verify the stdlib guard survives the extra hop, **and that it can still fail**: `uv run pytest -q -k "stdlib or dash_s or minus_s"`
- [ ] 4.3 Verify the gate: `make gate`

## 5. The two renames

> `show` is the verb **and** the file; `photo`'s callers hand it renders. **The verb `show` does not
> change** — pinned at `tests/test_pipeline_cli.py:20` and `tests/test_resume.py:38`.

- [ ] 5.1 `git mv isekai/show.py isekai/run_view.py`; `git mv tests/test_show.py tests/test_run_view.py`; update the importer in `cli.py` and `tests/test_run_view.py:17`. Verify: `uv run python -m isekai show --help` exits 0
- [ ] 5.2 `git mv isekai/photo.py isekai/image.py`; `git mv tests/test_photo.py tests/test_image.py`; update `isekai/generate.py`, `isekai/evaluate.py`, root `evaluate.py`, `tests/test_generate.py:34`, `tests/test_evaluate.py:27`, and the stale comment at `tests/test_generate.py:564`. Verify: `grep -rn 'isekai\.\(show\|photo\)\b' isekai tests scripts probe evaluate.py baseline` is empty
- [ ] 5.3 Verify history survived both renames: `git log --follow --oneline -- isekai/run_view.py | tail -3` reaches commits older than this change
- [ ] 5.4 Verify the gate: `make gate`

## 6. The two seam moves

> Design D6. Together these close five of the six stage→stage imports; only `review.py`'s call to ②'s
> `validate` survives. **Only the `Schema` type's home moves** — striking `version`, de-duplicating the
> vocabulary pin and redefining what a schema *is* are v0.16's, because those are observable.

- [ ] 6.1 Move the `Schema` type from `sheet.py:81` to `flow.py`; `sheet`, `review` and `cli` import it from `flow`. Verify `generate`'s import of `sheet` disappears entirely: `grep -n "from isekai.sheet" isekai/generate.py` is empty
- [ ] 6.2 Give `run` the stage directory names — `CAPTIONS`, `SHEETS`, `REVIEW`, `PROMPTS`, `OUTPUTS`, `APPROVED` — and point `sheet`, `review`, `generate` and `run_view` at `run` for them. Verify: `grep -n "from isekai.\(caption\|sheet\|review\|generate\)" isekai/run_view.py` names only `generate`, for `rendered_seeds`
- [ ] 6.3 Verify **exactly one** stage→stage import remains, and that it is the validator call: `grep -n "from isekai.\(caption\|sheet\|review\|generate\)" isekai/caption.py isekai/sheet.py isekai/review.py isekai/generate.py` returns one line — `review.py` importing `validate` from `sheet`
- [ ] 6.4 Verify the gate: `make gate`

## 7. The restructure

> Design D2. Contents unchanged; only paths, the import lines naming them, and one `.parent` per anchor.

- [ ] 7.1 `git mv` all files into `foundation/` · `pipeline/` · `shared/` · `boundary/` · `evaluation/` · `interface/`, leaving `isekai/__main__.py` at the package root. Add an **empty** `__init__.py` to each group. Verify: `uv run python -c "import isekai.foundation.run, isekai.pipeline.generate, isekai.shared.atomic_write, isekai.boundary.provision, isekai.evaluation.labels, isekai.interface.wiring; print('ok')"`
- [ ] 7.2 Add one `.parent` to each of the seven repo-root anchors. Verify with phase 1's detector: `uv run pytest tests/test_package_paths.py -q`
- [ ] 7.3 Rewrite every import path across `isekai/`, `tests/`, root `evaluate.py`, `probe/loader_probe.py` and `scripts/derive_eval_manifest.py`. Update `pyproject.toml`'s two `[[tool.ty.overrides]]` paths naming `isekai/eval_backends.py`. Verify: `make gate`
- [ ] 7.4 **Verify `isekai/evaluation/eval_backends.py`'s three first-party imports by hand.** `pyproject.toml`'s `unresolved-import` override blinds `ty` here and no test imports the file, so **this is the one edit in the change that no gate command sees** (design D9). Verify: `grep -n '^from isekai\.' isekai/evaluation/eval_backends.py` returns three lines, and `uv run python -c "import ast,pathlib,importlib.util as u; [print(n.module, u.find_spec(n.module) is not None) for n in ast.walk(ast.parse(pathlib.Path('isekai/evaluation/eval_backends.py').read_text())) if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith('isekai.')]"` reports `True` for every one
- [ ] 7.5 Write the seven `README.md` files — one per group plus `isekai/README.md`. Each carries a table of its files and a table of who imports them; **one screen, files and importers only** — seams and contracts stay in the design record (design D11). Verify: `for d in foundation pipeline shared boundary evaluation interface; do diff <(ls isekai/$d/*.py | xargs -n1 basename | grep -v __init__ | sort) <(grep -o '\`[a-z_0-9]*\.py\`' isekai/$d/README.md | tr -d '\`' | sort -u) > /dev/null || echo "MISMATCH $d"; done` prints nothing
- [ ] 7.6 Verify the gate: `make gate`

## 8. The record

> Paths are final only now.

- [ ] 8.1 Correct all nine `openspec/specs/*/spec.md` `Source:`/`Tests:` lines to the new paths, adding what each omits — `image-generation` gains `image.py`/`test_image.py`, `cli` gains `cli.py`, `wiring.py`, `run_view.py` and the three further test files holding `cli:*` keys, `run-directory` gains `atomic_write.py`, `model-provisioning` gains `test_derivation.py` and `test_vocabulary_manifest.py`. Verify: `grep -h 'Source:\|Tests:' openspec/specs/*/spec.md | grep -o '\`[^\`]*\`' | tr -d '\`' | sort -u | while read p; do [ -e "$p" ] || echo "MISSING $p"; done` prints nothing
- [ ] 8.2 Rewrite `comfy-transport`'s preamble. `isekai/pipeline.py` and `tests/test_polling.py` were **deleted together in `8baf2b3` at v0.14** — redirect them to `generate.py`'s polling loop and `tests/test_generate.py`, and add `comfy_types.py`, which holds the `ComfyTransport` Protocol the preamble's own sentence depends on. Verify: `grep -n "pipeline.py\|test_polling" openspec/specs/comfy-transport/spec.md` is empty
- [ ] 8.3 Rewrite `cli`'s preamble: delete *"dispatching the chosen model into a run"* and *"every dial is range-checked at parse time"* — **there are no dial flags**; dials live in `flows/summon-v1/flow.json`, and only `_seed` and `_count` validate at parse time. Verify: `grep -in "chosen model\|every dial" openspec/specs/cli/spec.md` is empty
- [ ] 8.4 Update `CLAUDE.md`'s layout section — it says *"the six stages"* and lists five, names `photo.py`, and mentions none of `atomic_write`, `wiring` or `cli`. Update `README.md`'s repository-layout tree, whose `└── __main__.py` line attributes **four** modules' work to the entry point. Verify: `grep -n "photo.py\|isekai/show" CLAUDE.md README.md` is empty
- [ ] 8.5 Verify the change is still well-formed: `openspec validate 0015-arc-alignment --strict`
- [ ] 8.6 Verify the gate: `make gate`
