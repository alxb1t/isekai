# Tasks — 0001-mf-standard

## Progress

- [x] 1 — SDD scaffold: `openspec/changes/` + `archive/` + this change's four artifacts
- [x] 2 — Relocate the gate config to `.minions/minions.toml`; ignore `.minions/` run artifacts
- [x] 3 — Pin the toolchain: `.python-version` + explicit ruff `select`
- [x] 4 — Mirror the gate in a root `Makefile`
- [x] 5 — Backfill `openspec/specs/` across the five capabilities
- [x] 6 — Bind the 87 tests: register both markers, mark every test
- [x] 7 — Rewrite `CLAUDE.md` onto the in-tree contract
- [ ] 8 — Verify: re-run `mf-teardown`, confirm `compliant`

## The per-phase ritual

Every phase, without exception:

1. **Test-first where there is logic to test.** Phases 2–4 and 7 change config and prose and have no new logic;
   phase 6 changes how existing tests are *labelled*, not what they assert. The standing rule still holds for any
   phase that does grow logic: red → green.
2. **Gate green before the commit** — `make gate` once phase 4 lands, and until then the five commands directly:
   `uv sync --locked` · `uv run ruff format --check .` · `uv run ruff check .` · `uv run ty check` ·
   `uv run pytest`. All 87 tests pass at every phase; a phase that leaves the gate red is not done.
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
