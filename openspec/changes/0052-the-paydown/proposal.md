---
version: v0.31.4
backlog: [0009·S3, 0018·R12, 0019·S1, 0024·R11, 0032·R3, 0033·R4, 0033·R8, 0039·R4, priv·clear, 0043·S4, 0044·S4, op·show-skips, 0048·R5, 0048·R6, 0049·R6, 0049·R9]
---

# 0052 — the paydown

The backlog's last cards, paid: `show` hides nothing, the clone guard reads every ssh form, the accepted risks are
written where their topic is read, and the lines that say something false are corrected.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the records, `show`'s new lines, the guard, the words |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `cli` |

## Why

**The backlog's last cards wait on no version.** Each is cheap, or is a risk already accepted but written only in the backlog
or a frozen archive. Nothing else would take them, and the backlog empties when they close.

**`show` hides what a run holds.** Inspection's job is reading a run in any state. It lists only artifact names, so
a failure record, a stray file, or a directory it does not know is invisible, and a stage whose only content is a
failure reads `(none)`.

**The clone guard misses the ssh and scp forms.** `ADD_GIT` knows `git://`, `git@` and `.git`; BuildKit also clones
`ssh://deploy@host/repo` and `deploy@host:repo`.

## What Changes

- **The accepted risks get an `Accepts:` bullet in their topic's decision, or a *Known breaks* line** — D6, D27,
  D35, D36; *A component is a contract* ([D1](design.md#d1)).
- **The records gain a line each**: `refusal_for`'s docstring, *Only a front end composes*'s *Known breaks*, and the
  boundary README's `ollama.py` row ([D2](design.md#d2)).
- **`show` lists every failure record under its stage and output group, with a `!` line per attempt**
  ([D3](design.md#d3)).
- **`show` names every file or directory below a flow that it does not read, on a `not read` line**
  ([D4](design.md#d4)).
- **`show` says "declares no kind" for a file with none** ([D5](design.md#d5)).
- **The clone guard refuses an `ADD` from an ssh or scp address** ([D6](design.md#d6)).
- **The review surface's false or loose lines are reworded** ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`: MODIFIED *Inspection prints the run directory with its provenance* — the SHALL adds failure records and
  unread names; gains *failure records are listed under their stage* and *a name it does not read is named*.

## Impact

- **Files:** `isekai/interface/run_view.py`, `isekai/foundation/run.py`, `tools/derive_image_project.py`,
  `isekai/interface/ui/batch.py`, `ui/src/components/BatchRail.vue`, `ui/src/ReviewApp.vue`, `docs/decisions.md`,
  `docs/principles.md`, `isekai/boundary/README.md`, `tests/test_run_view.py`, `tests/test_infra.py`.
- **Behaviour:** `show` prints more lines; the rail's run button reads `in the manifest`. Nothing a stage writes
  changes.
- **Formats:** none. No file the image copies changes.
- **Dependencies:** none.
- **Spend:** none.

## Not in this change

- **Clearing ComfyUI's history or cache** — accepted in D36 instead, since the pod does not outlive its batch.
- **A UI test runner, and `keepalive` on the draft `PUT`** — the ui version's.
- **Passing the Ollama and pod-record seams as parameters, or moving `_once`'s transience rule into a stage** —
  recorded as *Known breaks*, reopened by the next caller that needs them.
- **An unprivileged `USER` in the image** — a rebuild; accepted in D35.
- **A per-tagger `--new-version`** — the docstring says `tag` re-runs both taggers.
