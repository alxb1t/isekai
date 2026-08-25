# Tasks — 0001-mf-standard

## Progress

- [x] 1 — SDD scaffold: `openspec/changes/` + `archive/` + this change's four artifacts
- [x] 2 — Relocate the gate config to `.minions/minions.toml`; ignore `.minions/` run artifacts
- [x] 3 — Pin the toolchain: `.python-version` + explicit ruff `select`
- [x] 4 — Mirror the gate in a root `Makefile`
- [x] 5 — Backfill `openspec/specs/` across the five capabilities
- [x] 6 — Bind the 87 tests: register both markers, mark every test
- [x] 7 — Rewrite `CLAUDE.md` onto the in-tree contract
- [x] 8 — Verify: re-run `mf-teardown`, confirm `compliant`
- [x] 9 — Close the release-gate review findings (Tier A + B)
- [x] 10 — Close review round 2 (findings 1–6); defer 7–8

## The per-phase ritual

Every phase, without exception:

1. **Test-first where there is logic to test.** Phases 2–4 and 7 change config and prose and have no new logic;
   phase 6 changes how existing tests are *labelled*, not what they assert. The standing rule still holds for any
   phase that does grow logic: red → green.
2. **Gate green before the commit** — `make gate` once phase 4 lands, and until then the five commands directly:
   `uv sync --locked` · `uv run ruff format --check .` · `uv run ruff check .` · `uv run ty check` ·
   `uv run pytest`. All tests pass at every phase (87 at phase 8, 97 after phase 9); a phase that leaves the gate red is not done.
3. **One commit per phase**, carrying the trailer `Change: 0001-mf-standard` **contiguous** with
   `Co-Authored-By:` — no blank line between them, or git stops parsing the trailer block.
4. **Check the box** in the `## Progress` list above, in that phase's own commit. The first unchecked entry is
   the current phase; that is how the loop reads this file.

## Phase detail

### 1 — SDD scaffold
Create `openspec/changes/archive/` (tracked via `.gitkeep`) and `openspec/changes/0001-mf-standard/` with all
four artifacts: `proposal.md` (frontmatter `version: v0.7`), `design.md`, this `tasks.md`, and `specs/` holding a
`README.md` marking the delta **N-A**.
**Closes:** `sdd:changes-tree` · keeps `sdd:active-change-contract` satisfied now that an active change exists.

### 2 — Relocate the gate config
`git mv minions.toml .minions/minions.toml`. **Do not edit the array.** Add to `.gitignore`, in this order:
`.minions/*` then `!.minions/minions.toml`.
**Closes:** `wiring:gate-config` (blocking) · `wiring:gitignore`.
**Also unblocks** the four criteria the round-1 report could not measure — `gate:covers-axes`,
`gate:contract-agrees`, `py:gate-commands`, `sdd:checker-in-gate` — by making the array readable at the path the
orchestrator uses. Nothing downstream is confirmable until this lands, which is why it is first after the
scaffold.

### 3 — Pin the toolchain
Write `.python-version` = `3.12`. Add `[tool.ruff.lint] select = ["E", "F", "I"]` to `pyproject.toml`.
**Outcome:** `I` flagged nothing — imports were already ordered. The 7 errors were all `E501`, because ruff's
default set is the `E4`/`E7`/`E9` subset and selecting `E` whole enables line-length. All 7 were one-line
docstrings and comments at 89–91 chars, wrapped by hand in this commit; no logic touched, and
`ruff format --check` confirmed no reformatting followed. See `design.md` §6.
**Closes:** `py:pinned-runtime` · `py:lint-select`.

### 4 — Mirror the gate
Add a root `Makefile` with a `gate` target whose recipe runs the five array commands **in the array's order**.
A missing, extra or reordered command is a mismatch; a variable in place of a literal is not.
**Closes:** `gate:make-mirrors`.

### 5 — Backfill the specs
Write `openspec/specs/<capability>/spec.md` for `model-registry`, `workflow-injection`, `workflow-mutation`,
`comfy-transport` and `cli`, per the mapping table in `design.md`. Every `#### Scenario:` carries a `- **Key:**`
and a `- **Layers:**` bullet; every key is `<capability>:<requirement-slug>:<scenario-slug>`; every layer is
`unit`.
**Descriptive only** — these state behaviour that already ships and already passes. A scenario that turns out not
to match the code is a **backlog finding**, never a silent edit to the code or a softened scenario.
**Outcome:** 85 scenarios across 22 requirements, in 5 capability files — `cli` 24, `workflow-mutation` 28,
`workflow-injection` 15, `model-registry` 13, `comfy-transport` 5. All keys unique, all three-segment lower-kebab
and capability-prefixed, every scenario carrying both required bullets, every layer `unit`.
**One mismatch found, and it was raised rather than absorbed:** the unknown-model exit message carried a stray
`$` (`isekai/models.py:30`). Per the rule above it was **not** fixed inside this phase — the human was asked, and
elected to repair it test-first in its own pre-phase commit, which is why the scenario now states the behaviour
plainly with no defect note.
**Closes:** `sdd:specs-tree` (blocking) · keeps `sdd:scenario-shape` satisfied.

### 6 — Bind the tests
Register both markers in `[tool.pytest.ini_options] markers` (see `design.md` §4), then mark all 87 tests:
`@pytest.mark.spec("<key>")` for behavioural, `@pytest.mark.spec_exempt("<reason>")` for genuinely structural
ones. Verify with `uv run pytest -q --strict-markers` that nothing is silently unregistered.
**Outcome:** 87 tests bound to 85 scenarios; **zero exemptions** — `spec_exempt` is registered but unused,
because every test turned out to prove a stated behaviour. The three `test_multipart.py` tests were expected to
need exemption and did not: wire-format assertions are behaviour, and the spec states them.
Two tests-per-scenario in three places: the three "unspecified dial is left alone" tests share one scenario, as
`design.md` §4 anticipated. Cross-checked both directions — no key bound that the specs do not define, no
scenario left without a test — and `-m "not spec"` collects nothing.
**Closes:** `sdd:test-binding`.

### 7 — Rewrite `CLAUDE.md`
Re-point the source of truth from the vault's `implementation_plans/vX.Y_implementation_plan.md` to the in-tree
`openspec/changes/<id>/` contract; describe progress as the `## Progress` checklist in `tasks.md`; correct the
gate account so it matches the array command for command, **flags included**.
**Keep:** the vault (`VAULT_PROJECT_DIR`, research/findings, `log.md`), the `.env` hygiene rules, the
metered-GPU protocol and the guardrails — all still accurate.
**Outcome:** all three (J) clauses now hold, each verified mechanically rather than by eye — the five commands
in the doc's gate list were compared against the parsed `gate` array and match on **order and flags**, and the
`Makefile` recipe was compared against the same array. `implementation_plans/` survives only as explicitly
**historical** (it is genuinely useful for *why* v0.6 and earlier are as they are), never as the authority.
Progress is now stated as the `## Progress` checklist with the first unchecked box as the current phase.
Confirmed path-free and placeholder-free.
**Kept as it was:** the pipeline facts, the metered-GPU protocol, the stdlib-only rule, the cu128 pin and the
`.env` hygiene — all still accurate, so the edit stayed narrow rather than becoming a rewrite of the repo's
description of itself.
**Closes:** `wiring:claude-md` (blocking). Last, because its clauses assert the end state of phases 2–6.

### 8 — Verify
Re-run `mf-teardown` against this branch. Expected: `verdict: compliant`, `open_blocking: 0`,
`open_required: 0`, the four previously-withheld criteria now **measured**, and at most one open gap —
`sdd:checker-in-gate` at `advisory`, unsatisfiable by any target repo today for the reason the rubric states
inline. The re-run is the independent checker for this milestone; it is not a formality and its report is the
acceptance record.
**Outcome — `verdict: compliant`** at `9ace528`, round 2. `open_blocking: 0`, `open_required: 0`,
`criteria_total: 23 — 23 − 0 not measured`: every criterion in the baseline was assessed, because the relocated
gate config made round 1's four withheld criteria readable. **22 of 23 pass** (A 6/6 · B 5/6 · C 4/4 ·
`python-uv` 7/7). All 9 round-1 gaps verified closed and cleared into the resolution log.
**One open gap, `sdd:checker-in-gate` at `advisory`** — measured for the first time this round and left open
deliberately: it is unsatisfiable by any target repo while MinionsFactory ships no packaging metadata, which is
why the rubric grades it advisory and why it does not withhold `compliant`. The binding it would enforce does
exist and is complete; only its automated enforcement is missing.
Measured by two fresh subagents, blind to this change and to the prior report, split by group.

### 9 — Close the release-gate review findings
Cutting the release ran the repo's own gate from `release_log.md`, which requires **Review: clean** and
**Security: clean**. Security came back clean (two candidates, both refuted under adversarial filtering). The
**code review came back `changes-requested` with 11 findings** — no functional regression, but a suite weaker
than its pass count and, worse, **three phase-5 specs that overstated the code**. Tier A and B closed here; Tier
C triaged to the backlog.

**A1 — `--seed` now covers the whole run.** `pipeline.py` derived only variation 0 from the seed; variations 1+
drew from the global unseeded `random`, so `--seed 77 --variations 3` reproduced one render of three while the
spec claimed all of them. Fixed the **code**, not the spec: every variation's seed now derives from a single
`random.Random(seed)`. **Variation 0 still uses the seed verbatim**, so the v0.4 byte-identical golden and every
other golden test stay valid. Test-first, confirmed red on variation 1 before the fix.

**A2 — `main()`'s plumbing is now asserted.** The three `run` doubles declared `mutate`/`seed`/`variations` as
defaults and never captured them, so deleting `mutate=model.mutate` left all 87 tests green while silently
disabling every dial. Replaced with one shared `*args, **kwargs` double that records everything. `--ip-weight`
had **zero** end-to-end coverage and now has it. Verified by deleting each of the four plumbing lines in turn:
all four now fail, none did before.

**A3 / A4 — specs trimmed to what is actually proven.** Five `cli` scenarios claimed run-level effects their
parse-only tests never reached, and one clause belonged to a `workflow-mutation` scenario entirely. The
ControlNet scenario asserted "no random values are drawn" — unobservable, since the CN loop runs last and stray
draws would leave every asserted value untouched. Restated as the byte-for-byte property its test does prove,
and the requirement sentence above it corrected to match.

**B1–B4 — four tests that could not fail.** The override-before-mutate test asserted a band containing the
override itself, so a reversed order passed; now pins the exact value. The seed-report test asserted `"7" in out`
— a different random number satisfies that ~86% of the time; now pins the line. The v0.6 clamps were asserted by
four scenarios and exercised by nothing, every base being strictly interior; added boundary tests at 0.0/1.0 and
0.0/30.0. Dial validation never pinned the inclusive edges, so `lo <= v <= hi` → `lo < v < hi` passed while
rejecting the documented `--denoise 1.0`; added edge acceptance plus one message assertion.

**Every fix was mutation-tested** — the defect was reintroduced and the new test confirmed failing — rather than
assumed to work. 87 → **97 tests**.

**Tier C, triaged rather than deferred wholesale.** Two were folded in because they are branch-introduced and the
backlog's no-tech-debt policy would otherwise require formally *accepting* them: `ci.yml` was a third
transcription of the gate that **had already drifted** (running `ruff format --check` and `ruff check` without
the `.` the array names) and now invokes `make gate`; and `.claude/settings.local.json`, which holds the
operator's absolute paths, was protected only by a machine-local global ignore and is now ignored by the repo
itself. The remaining three are genuinely pre-existing and went to the backlog's unversioned section.

### 10 — Close review round 2
The round-2 blind review returned **`changes-requested` with 8 findings**, and confirmed round 1's closures hold
under re-probing. Findings 1–6 closed here; 7–8 documented in the backlog.

**A real crash, and a regression we were about to ship.** v0.6 made the jitter base-relative, turning `mutate`
from write-only into read-modify-write — with no check that the dial it reads is a number. In ComfyUI API format
an input may legally be a `[node_id, slot]` link, and **this repo already ships such a graph**:
`workflows/qwen-image-edit.json` drives `cfg` from a Switch node. So
`convert.py photo.jpg --prompt anime --workflow workflows/qwen-image-edit.json` — a documented flag combination —
died with a bare `TypeError: unsupported operand type(s) for -: 'list' and 'float'`. Pre-v0.6 it exited cleanly.
Added a `_base()` guard that stops with a message naming the dial and the node driving it, applied at all four
read sites, which also collapses the duplicated reads.

**Three more tests that could not fail**, each confirmed by probe:
- `--seed X --variations 5` could collapse to **five identical paid renders**: the reproducibility test compared
  run A to run B element-wise, which an all-identical run satisfies. Now also asserts the variations differ from
  each other.
- Freezing two of three ControlNet nodes passed, because the assertion compared the whole dict and the band
  admitted an unchanged value. Now asserts per node.
- `--denoise 0.0` was silently discardable: switching the `is not None` guards to truthiness kept every test
  green while the workflow's baked value was used instead. Now pinned.

**Two spec-fidelity gaps of my own making.** Phase 9 fixed the seed behaviour but never wrote a scenario for it,
so the spec *understated* the release's headline change — and the test proving it was bound to a key whose WHEN
describes overrides the test does not supply. Added
`workflow-mutation:reproducibility:seed-covers-every-variation` and rebound it. Phase 9's A3 trim also introduced
two new run-level-clause mismatches; those clauses are in fact proven, by `main()` tests bound to other keys, so
the keys are now **stacked onto the tests that prove them** rather than the true claims being deleted.

88 scenarios, 105 markers, every scenario bound, no unmarked tests. 97 → **99 tests**.
