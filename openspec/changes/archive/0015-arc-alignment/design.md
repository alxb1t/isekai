# Design — v0.15, arc alignment

**Verdict: `feasible`.** Nothing here is untested at cut time and nothing here is new code — every edit
moves or renames something the suite already exercises, and the five largest have blast radii of 87–149
tests each, failing at **collection** rather than silently.

**Two caveats, both settled below rather than left as conditions.** `eval_backends.py`'s three
first-party imports are invisible to every gate command (D9), and are held by one named verification in
phase 7 — an exception with an expiry, not a habit. And `DATA_ROOT`'s anchor is the one breakage that
would fail *quietly* (D7), which is why phase 1 lands its detector, with a falsification twin, before a
single file moves.

**One extraction the record scheduled does not happen.** `flow.assemble()` stays where it is (D5), and
the reasoning is written into the design record rather than dropped.

See [`proposal.md`](proposal.md) for why.

## Context

See `proposal.md` — Why. The constraints that shape the approach, each verified against the tree at
`v0.14.0` rather than taken from a note:

```
  22 flat files · 6,462 lines · 56 first-party import statements · 51 deduplicated
  edges · 54 at module scope · 2 lazy (vocabulary.py:244,245) · no cycles ·
  no TYPE_CHECKING · no relative imports · 591 tests
```

- **`python -m isekai` resolves through `runpy` to `isekai/__main__.py`.** That path is fixed.
- **The runtime is stdlib-only**, guarded by `python -S` importing the entry point in a subprocess,
  with a falsification twin. A shim must not break it.
- **Seven files anchor a repo-root path on `Path(__file__).resolve().parent.parent`** — `run.py:52`,
  `flow.py:35`, `sheet.py:59`, `caption.py:52`, `provision.py:26,34`, `eval_models.py:38`,
  `claude_cli.py:51`. Every one is wrong a directory deeper.
- **`pyproject.toml:103` sets `unresolved-import = "ignore"` for `isekai/eval_backends.py`**, so the
  gate stays green without the `[eval]` extra. It also blinds `ty` to first-party imports there.
- **`ty check` is whole-tree**: root `evaluate.py`, `probe/` and `scripts/` are covered even where no
  test imports them. `eval_backends.py` is the sole exemption.
- **The design record is `Lab/isekai/architecture-v2/` in the operator's notebook.** Nothing here
  resolves a path outside this repository, and nothing there is promoted as a specification.

## Goals / Non-Goals

**Goals**

- The package's directory structure carries the six groups the design already reasons in.
- Every seam that has a consumer outside its own module gets its own file.
- Five of the six stage→stage imports stop existing.
- Every capability's `Source:`/`Tests:` metadata names a file that exists.
- **A later version does no structural work to build its feature.**

**Non-Goals**

- **No observable change.** If a user could see it, it is not in this change.
- **No new enforcement.** No test is added that asserts the import graph. See Decisions D1.
- **Not the flow consolidation, and not the run-layout move.** Both are v0.16's, blocked on four open
  questions, and both are observable.
- **Not the evaluation sub-system's five renames.** See D8.
- **Not the evaluator adopting `atomic_write`.** See D4.

## Decisions

### D1 · No import-graph test. The claim is retired, not enforced.

`verifications.md` records that nothing in the gate checks the import graph. The obvious acceptance is a
test asserting the real graph against a declaration.

**Refused.** A 51-edge declaration is a snapshot, not a check: it holds no opinion about whether a new
edge is *good*, and the repair for a red run is to add the edge and move on — the same failure this
repo already records against its hand-maintained spec↔test bindings. And the errors such a test would
supposedly have caught are errors **in the design record**, which nothing here reads.

**Alternatives considered.** (a) A 22-key graph declaration in a test file — refused above. (b)
Assertions on the three extracted modules' dependency sets only — narrower and opinionated, but it
guards two modules against a failure that has never occurred. (c) Nothing — **chosen.**

**Consequence, accepted and recorded:** the extractions ship claims nothing holds. The moment
`atomic_write.py` grows a first-party import, the module has no reason to exist and no gate says so.

**Acceptance instead:** the suite stays green. 591 tests, blast radii of 87–149 per edit, every one a
direct module-path import that fails at **collection** rather than silently.

### D2 · Six group directories, not a flat package.

22→25 files is the band where flat and nested are both idiomatic (`httpx` is flat at ~20; `django` is
nested). The deciding argument is that the taxonomy was checked against the files first and is **total**
— all 21 seam-bearing files land in exactly one group, none in two.

`__init__.py` files stay **empty**. Re-exporting through them is how nested packages acquire the import
cycles this one does not have.

**Alternative considered:** `evaluation/` alone, because it is a real install boundary. Rejected — it
leaves five other groups asserting nothing, and the `[eval]` boundary is already carved by path in
`pyproject.toml`.

### D3 · `cli` moves to `interface/cli.py`; `__main__.py` becomes a shim.

```python
# isekai/__main__.py
from isekai.interface.cli import main

raise SystemExit(main())
```

`runpy` pins `__main__.py`'s path; it does not pin where the parser lives. `pip`, `black` and `flask`
all ship this shape.

**Alternative:** leave the parser at the package root. Rejected — it makes the package's largest
interface surface the one file outside the filing scheme, which is the exact thing D2 was decided to
avoid.

**Risk:** the `-S` guard imports `isekai.__main__`. Acceptance row 6 proves the shim does not break it.

### D4 · `atomic_write` is extracted; the evaluator is not rewired.

The record justifies the extraction on the evaluator's two non-atomic writes into `runs/`
(`evaluate.py:183`, `:186`). **That file has zero test importers** — it says so at `evaluate.py:18` —
and is documented as unable to read a run this pipeline produces (`:11-17`). Rewiring it is the one edit
in this change that no gate command would catch, and it is the same disqualification that moved
`eval_backends` out of this version.

The extraction rests instead on what is countable today: **`generate.py:386` writes the rendered PNG
with it**, importing it by name at `generate.py:57`. A consumer outside the module already exists.

**`write_json` (`run.py:181`) stays in `run`.** It encodes the run's artifact JSON convention
(`indent=2`, trailing newline) — a run format, not a write primitive.

**This edit is not mechanical.** `tempfile` is imported at `run.py:36` and used at exactly one place,
`run.py:165`, inside the moved function. After the move the import is dead, `ruff` refuses it as unused,
it is removed — and `tests/test_run_directory.py:253`'s `monkeypatch.setattr(run_module.tempfile, ...)`
then raises `AttributeError`. **That test is retargeted by hand.** It is a good detector: it fails on the
move rather than sleeping through it. The other two atomicity tests (`:197`, `:215`) patch
`run_module.os`, which *is* the global `os` module object, and would pass regardless.

### D5 · `flow.assemble()` does not move.

The record scheduled a third extraction on the tier rule — *a module straddling two tiers is a module to
split.* Reading both files shows **one name was being used for two functions**:

```
  flow.assemble()      flow.py:182   PURE. fields + order + flow -> 2 strings. 1 caller.
  generate.prepare()   generate.py:204  reads the sheet off disk, checks a budget,
                                        writes the prompt artifact. Offline, NOT pure.
```

The tier rule describes the second. The first has **one caller** (`generate.py:171`) and **one
implementation** — the exact condition that refused `run`'s four-way split — and it consumes
`flow.prompt`'s four keys and nothing else, with `REQUIRED_PROMPT` declared 126 lines above it in the
same file. It is the reader of a declaration `flow` owns.

Recorded as internal, as `multipart.py` is internal to the transport. **Trigger for revisiting: a second
flow declaring a prompt register the comma-joined Danbooru path cannot express.**

**The tier straddle inside `generate.py` is real and this change does not resolve it.** It is recorded
as open rather than claimed as obeyed.

### D6 · `Schema` → `flow` and the layout names → `run` come forward from v0.16.

Both are pure import changes with no behaviour, which is what this version is for. Together they close
five of the six stage→stage imports:

```
  1 sheet.py:32    -> caption DIRECTORY   ┐
  2 review.py:52   -> sheet DIRECTORY     │  run owns the layout names
  4 generate.py:47 -> review APPROVED     │
  5 generate.py:48 -> review DIRECTORY    ┘
  6 generate.py:60 -> sheet Schema        ← Schema moves to flow; this edge disappears
  ──────────────────────────────────────────────────────────────────────────────────
  3 review.py:53   -> sheet validate      ← SURVIVES. The one behavioural edge.
```

**Only the `Schema` type's home moves.** Striking its `version`, de-duplicating the vocabulary pin and
redefining what a schema *is* stay at v0.16 — those are observable.

**Consequence for v0.16:** it changes the directory *values* in one file instead of five.

### D7 · The eight repo-root anchors are fixed before anything moves.

Seven files compute a repo-root path as `Path(__file__).resolve().parent.parent`. One directory deeper
that expression yields `isekai/` instead of the repository root.

Six fail loudly — a missing `flows/`, `schemas/`, `briefings/` or manifest breaks dozens of tests at
collection. **`DATA_ROOT` (`run.py:52`) fails quietly.** It would become `isekai/.data`, and
`RUNS_ROOT = DATA_ROOT / "runs"` moves with it, so tests asserting the *relationship* between the two
still pass. `__main__.py:194`'s `REPOSITORY = DATA_ROOT.parent` would then be `isekai/`, and
`_check_run_root` — the gate-enforced guard that a run directory, which holds a copy of a photograph by
construction, is never one `git add` from publication — **would stop refusing `<repo>/runs/`**.

Acceptance row 3 asserts an **absolute** property, not a relative one, and phase 1 lands that assertion
**before** any file moves — so the detector exists in a passing state and the restructure cannot quietly
defeat it.

### D8 · The evaluation sub-system's five renames stay at v0.19.

Both reasons recorded on 2026-09-16 have expired. *"Two passes over one set of files"* is **inverted** —
this change makes a pass over all five anyway. *"`eval_backends` has zero test importers"* is
**accepted** rather than avoided (D9).

**What survives has evidence.** `eval_backends.py:42` imports `Box`, `Canvas`, `FaceReading`,
`Keypoint`, `Refusal` and `Region` **back from** `evaluate.py`. Those types are on the wrong side of a
seam nobody has drawn, so `evaluate → scoring` and `eval_backends → vision-models` would bake it in.
**The sub-system decides its own structure at v0.19.**

### D9 · `eval_backends.py`'s three imports are verified by hand, once.

`pyproject.toml:103`'s override makes the file's first-party imports invisible to `ty`, and no test
imports it. This change rewrites all three (`:40`, `:41`, `:42`).

Accepted because its only consumer — root `evaluate.py` — is already unable to read a run this pipeline
produces, so a mistake costs nothing until v0.19, which must verify them to build on them. Held by
**acceptance row 7**: an exception with an expiry, not a habit.

**v0.19 owes either gate coverage for the file or an override narrow enough to keep first-party imports
checked.** The override was written to survive a missing extra; taking first-party import checking with
it was never the intent.

### D10 · `skip_specs: true`, and the spec edits are direct.

This change alters no requirement and no scenario — the same statement as *nothing a user can observe*.
The nine `spec.md` files are edited only in their `Source:`/`Tests:` metadata and two preambles, and the
delta format expresses `ADDED` / `MODIFIED` / `REMOVED` **requirements** and has no construct for
either.

`.openspec.yaml` carries `schema: spec-driven` **and** `skip_specs: true`. Both are load-bearing:
without a resolvable schema the marker is read, rejected, and `--strict` fails as if it were absent
(`0001-mf-standard` records this).

The scope is all nine, not the two known-wrong ones: the restructure invalidates every `Source:` line,
so all nine are rewritten regardless, and leaving a line incomplete while rewriting it is worse than not
touching it.

### D11 · One `README.md` per group, plus `isekai/README.md`.

`modules/README.md` names a `docs/` that does not exist and waits for a later version. These are that,
scoped to seven files.

**The boundary that keeps them from lying:** the repo README answers *what files are in this directory
and who imports them* — derivable from the code. The design record answers *what the seam is and what
could replace it*. **Neither restates the other.** One screen each.

**No test.** A file table that must match `ls` is the same shape as the snapshot refused in D1.
Acceptance row 8 checks it at release instead.

## Risks / Trade-offs

| risk | mitigation |
|---|---|
| **`DATA_ROOT` silently relocates**, narrowing the photograph-publication guard | D7. Anchors fixed in their own phase **before** any file moves; acceptance row 3 asserts an absolute property |
| **`eval_backends.py`'s three imports are invisible to the gate** | D9. Acceptance row 7, a named `grep`; v0.19 owes the structural fix |
| **`tests/test_run_directory.py:253` breaks on the `tempfile` move** | D4. Expected, documented, retargeted in the same phase. It is a detector, not a defect |
| **A renamed file loses its history** | `git mv` throughout; acceptance row 11 proves `--follow` reaches back past the rename |
| **The restructure buries five edits that need argument in a rename storm** | Phase order: extractions and renames land and go green **before** the restructure. Each is reviewable alone |
| **Three extractions ship claims nothing holds** | D1, accepted deliberately and recorded in the design record rather than discovered later |
| **The CLI verb `show` is renamed by accident** | pinned at `tests/test_pipeline_cli.py:20` and `tests/test_resume.py:38`. The rename cannot reach the user surface |

## Migration Plan

**None required.** No artifact format, no on-disk layout and no CLI surface changes, so no run written
by any previous version becomes unreadable and nothing needs re-running.

Phases land in dependency order, each green before the next:

```
  1  detectors      tests pinning the 8 anchors to the REPO ROOT, + a
                    falsification twin. Green today; red the moment phase 7
                    moves a file without fixing its anchor
  2  atomic_write   extracted from run  (+ retarget one monkeypatch)
  3  wiring         Wiring, wiring(), _check_run_root, out of __main__
  4  cli            split out of __main__; 3-line shim
  5  renames        show -> run_view · photo -> image
  6  seam moves     Schema -> flow · layout names -> run        ← 6 edges become 1
  7  restructure    22 files -> 6 directories, 7 READMEs, + one `.parent` per anchor
  8  docs + spec    9 capability files · CLAUDE.md · README.md  ← paths final only now
```

**Phase 1 writes the detector, not the fix.** The anchors are *correct* today and wrong only once a
file moves, so there is nothing to repair in phase 1 — there is something to **pin**. Writing the
assertion while it passes, with a twin proving it can fail, is the discipline the `python -S` guard
already uses here.

**No shared path module is introduced.** A single repo-root constant would need a home all seven files
could import — a fourth new module this change did not propose, and new edges phase 6 exists to remove.
Each file keeps its own expression and phase 7 adds one `.parent` to each.

**Rollback** is `git revert` of the phase commit; every phase is one commit and independently green.

## Open Questions

None that affect this change. Three are recorded in the design record as deferred **with what each
blocks**, and none of them changes this change's specs, approach or tasks:

- `generate`'s tier straddle — `prepare()` free, `render()` metered, in one module. Unscheduled.
- `comfy-transport` is one seam of three files, and a group directory does not make it one. Blocks
  nothing; left as peers.
- The surviving stage→stage edge — ③ importing and *calling* ②'s `validate`. v0.16 decides whether it
  lands there.
