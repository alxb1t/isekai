---
version: v0.22.9
---

# 0031 — the backlog

The deferred work the earlier patches left: the parts of v0.22.8's fixes its build missed, the guards
rules still lack, and the documentation that drifted. Behaviour changes only where an existing requirement
demands it.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each row, the rule that selected it, and every choice that settles how |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | a scenario for the approval race, and a rationale reworded |

## Why

**v0.22.8 closed families of defects, and each family kept a member.** A JSON list from the endpoint still
escapes as a traceback; other missing keys in a hand-edited draft still raise; the damaged frame's remedy names
a step a run id cannot reach; an autosave can still land after an approval.

**Rules the principles state are held by nothing**: the retry rule is written twice, and nothing checks
that every run file's writer annotates its artifact.

**Documentation drifted in the moves**: READMEs, `docs/modules.md`, a principle, the tools' `--help`, and a
spec sentence.

## What Changes

- **The rest of v0.22.8's families**: a wrong-shaped answer is refused; every missing key is refused by name;
  the damaged frame's remedy offers the photograph again by its path; approval takes the draft lock
  ([D1](design.md#d1)).
- **Guards**: one predicate for *may this stage try again*; an AST test that every `write` gets an annotated
  artifact; a golden for the draft `save_draft` rewrites ([D2](design.md#d2)).
- **Test nits**: a `ty: ignore` and an unused fixture go ([D2](design.md#d2)).
- **Documentation**: the README's vocabulary step, the group READMEs, `docs/modules.md`, the principle's
  *path in the run*, the tools' `--help`, a spec sentence, and the sheet budget's comment
  ([D3](design.md#d3)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui` · *An approved input is read-only on the surface until it is re-opened* — an update that overlaps an
  approval is refused.
- `run-directory` · *An unknown schema version is refused, naming the fix* — its rationale says *"a format this
  build does not know"*; no SHALL or scenario changes.

## Impact

- **Files:** `isekai/boundary/comfy/client.py`, `isekai/pipeline/` (`generate.py`, `review.py`, `sheet.py`),
  `isekai/foundation/` (`run.py`, `artifacts.py`), `isekai/interface/ui/app.py`, `tests/`, `README.md`,
  `docs/modules.md`, `docs/principles.md`, the group READMEs, the tools' and the evaluator's CLIs.
- **Behaviour:** refusals where tracebacks were; the frame's refusal text; an autosave that overlaps an
  approval answers 409. The product is unchanged.
- **Patch conditions:** met ([D4](design.md#d4)).
- **Dependencies:** none.

## Not in this change

- **Behaviour no requirement demands**: `show` surviving a bad frame, the models root's working-directory
  dependence, control bytes in the endpoint's error body, a reader checking a file's kind, the sidecar's
  name, `entry_for`'s message, the frame's `id`, the UI bundle's build timeout, `Origin`-less requests.
- **A CLI `approve` from another process** racing the review surface: the lock is in-process.
- **The manifest's mirror-primary entries**: a move did not open the file.
- **An audit of every scenario against the code.**
