# Design — 0045 the spec bound

How one test makes the gate hold every spec↔test binding, how it reads keys while a change is being built, and the
rebindings it needs to pass on day one. **Verdict: feasible** — a stdlib test over files the repository already
holds.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut (`be1e2bb`):

- **Keys:** 388 scenario keys, each a `- **Key:** \`…\`` line in `openspec/specs/*/spec.md`. A delta in
  `openspec/changes/<id>/specs/<capability>/spec.md` carries keys under `## ADDED Requirements` and
  `## MODIFIED Requirements`; a `## REMOVED Requirements` block names a requirement by title, with no scenarios.
  `openspec/changes/` holds only `archive/` between changes.
- **Markers:** 918 test functions under `tests/`. 720 carry `@pytest.mark.spec("<key>")`, some spanning lines, and 198
  carry `@pytest.mark.spec_exempt("<reason>")`. None carries `spec` and `spec_exempt` together, none more than one
  key, and no marker sits in a `pytest.param` or a module-level `pytestmark`. 387 distinct keys are named, none
  missing from the specs.
- **The unbound key:** `run-directory:identity:a-prefix-collision-refuses` (`openspec/specs/run-directory/spec.md:56`).
  `test_a_digest_prefix_collision_is_refused_rather_than_mixed` (`tests/test_run_directory.py:887-888`) exercises it
  under `run-directory:identity:same-name-different-bytes-differ`, which `:136` also holds.
- **The no-scan refusal:** `test_a_scan_no_one_answers_is_refused_as_such` (`tests/test_infra.py:1993-1994`) and the
  `no-scan` parameter of `test_a_failed_teardown_claims_none_and_names_no_re_run` (`:2005-2019`, ids `mismatch` and
  `no-scan`) are bound to `pod-image:host-key:a-mismatch-is-refused`. The twin at `:2022-2023` names the first.
- **The hold:** `test_the_hold_ends_on_its_own_well_inside_the_session_ceiling` (`:308-317`) checks `HOLD_SECONDS`
  and `sleep "$HOLD_SECONDS"` inside `shell_function(start_sh, "hold")`. `start.sh`'s `hold` ends in
  `exec bash "$STOP_POD"`.
- **`CLAUDE.md:140-141`:** "There is **no spec↔test binding checker in this repo**, so `spec` / `spec_exempt`
  bindings are maintained by hand and reviewed, not enforced; that gap is known and open."
- **`pyproject.toml:210-213`** registers `spec` and `spec_exempt`.

## Goals / Non-Goals

**Goals:** every key bound, every marker real, every test marked once, held by the gate; the rebindings that make it
green today.

**Non-Goals:** reading a scenario's THEN against the code; checking a `spec_exempt` reason; rewriting a spec.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `tests/test_spec_bindings.py` reads keys with a regex and markers with `ast`, and fails on an unbound key, a marker naming no key, a test with neither marker or more than one, and a marker off a collected test's decorators | static reading is enough — no marker is built at runtime; it runs in milliseconds | a collection hook in `conftest.py`, which fails every run, not one test |
| [D2](#d2) | the key set is the living spec as each active change's delta leaves it: a RENAMED requirement keeps its keys under its new title, a REMOVED one loses them, a MODIFIED one's are replaced by the delta's, an ADDED one's join | the gate stays green while a change is built | the living spec alone, which is red mid-build |
| [D3](#d3) | `tests/test_run_directory.py:887` binds `run-directory:identity:a-prefix-collision-refuses` | it is the test that exercises the collision | a new test beside it |
| [D4](#d4) | a scenario for the scan no one answers; `test_a_scan_no_one_answers_is_refused_as_such` binds to it; the parametrised teardown test splits into a mismatch function and a no-scan function | a marker lives on a function, not on a parameter | a mark inside `pytest.param`, which the checker would have to read — it now refuses one instead (D1's `stray`) |
| [D5](#d5) | the hold's test asserts that `hold` ends in `exec bash "$STOP_POD"` | the scenario's THEN since v0.30 | a new test |
| [D6](#d6) | `CLAUDE.md:140-141` names the checker | the gap is closed | — |

### D1

**The checker.** `tests/test_spec_bindings.py`:

```
keys     ← openspec/specs/*/spec.md  ─┐
            + active deltas (D2)      ├─▶ unbound(keys, markers)   → []
markers  ← ast of tests/**/*.py  ─────┘   unknown(keys, markers)   → []
             (spec / spec_exempt per      unmarked(tests)          → []
              collected test)             stray(root)              → []
```

- `spec_keys(root)` returns the key set. `marked_tests(root)` returns each test pytest collects — a top-level
  `test_` function, or a `test_` method of a `Test*` class, nested or not, named `TestX::test_y` — with its markers,
  as `(file, test, [("spec", key) | ("spec_exempt", reason)])`.
- `stray(root)` returns every `spec` or `spec_exempt` mark that is not on a collected test's decorators — a module's
  `pytestmark`, a `pytest.param(marks=…)`, a class's decorator — as `file:line`; its gate test is
  `test_no_marker_sits_where_none_is_read`.
- Each of `unbound`, `unknown`, `unmarked` and `stray` returns a sorted list; each test asserts it is empty and names
  the first offenders.
- **Twins** run each function over a temporary tree that breaks it once: a key with no test, a marker naming no key,
  a test with neither marker, a test with more than one, an unmarked test inside a `Test*` class, a module
  `pytestmark` and a `pytest.param(marks=…)` naming a spec mark.

### D2

**Keys mid-build.** For each `openspec/changes/<id>/` other than `archive/`:

- each delta applies in OpenSpec's order, per requirement: a RENAMED requirement's keys move from its FROM title to
  its TO title; a REMOVED title drops that requirement's keys; a MODIFIED requirement's keys replace its living ones;
  an ADDED requirement's keys join.

Twins check that a key only a delta adds is bound, a key only a REMOVED requirement held is not demanded, a scenario a
MODIFIED requirement re-keys leaves its old key undemanded, and a RENAMED requirement keeps its keys until a MODIFIED
one re-keys them.

### D3

**The unbound key.** `tests/test_run_directory.py:887`:
`@pytest.mark.spec("run-directory:identity:same-name-different-bytes-differ")` →
`@pytest.mark.spec("run-directory:identity:a-prefix-collision-refuses")`.

### D4

**The unanswered scan.**

- **The scenario:** added under *A pod's host key is checked before anything is sent*, with its requirement sentence
  naming the case. See `specs/pod-image/spec.md`.
- **`test_a_scan_no_one_answers_is_refused_as_such`** (`:1993`) binds to
  `pod-image:host-key:a-scan-no-one-answers-is-refused`.
- **`test_a_failed_teardown_claims_none_and_names_no_re_run`** (`:2005-2019`) splits into
  `test_a_failed_teardown_after_a_mismatch_claims_none` (`a-mismatch-is-refused`) and
  `test_a_failed_teardown_after_an_unanswered_scan_claims_none` (`a-scan-no-one-answers-is-refused`), each with the
  same assertions.

### D5

**The hold's test.** `test_the_hold_ends_on_its_own_well_inside_the_session_ceiling` gains
`assert shell_function(start_sh, "hold").removesuffix("}").rstrip().endswith('exec bash "$STOP_POD"')`.

### D6

**`CLAUDE.md:140-141`:** `There is **no spec↔test binding checker in this repo**, so … that gap is known and
open.` →
`` `tests/test_spec_bindings.py` holds every binding: each key has a test, each marker a key, each test one marker. ``

## Dependencies

None.

## Risks / Trade-offs

- **A marker built at runtime would escape the checker** → none exists; `unmarked` fails a test whose decorator it
  cannot read as either marker.
- **A delta written loosely** (a key outside a section, a REMOVED title that matches nothing) → the checker reads only
  the ADDED, MODIFIED, REMOVED and RENAMED headings OpenSpec validates, and a REMOVED title matching no living requirement
  drops nothing.

## Verdict

**feasible** — a stdlib test and the rebindings, all in `tests/`.
