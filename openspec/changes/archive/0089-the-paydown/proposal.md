---
bump: patch
version: 0.60.2
backlog: [0056·R5, 0056·R7, 0056·S2, 0058·R5, 0058·R6, 0058·R7, 0061·R7, 0062·R11, 0065·R14, 0068·R5, 0068·R12, 0069·R8, 0070·R8, 0070·R9, 0070·R12, 0070·R15, 0071·R4, 0071·R6, 0072·R3, 0072·R6, 0072·R7, 0072·R13, 0072·R16, 0073·R10, 0076·R9, 0076·R11, 0077·R4, 0077·R5, 0077·R6, 0077·R8, 0077·S3, 0078·R3, 0080·R7, 0081·R3]
---

# 0089 — the paydown

The backlog worked down before the first unattended run: the cards that need no pod paid, the moot ones closed, and
the stream test that flakes made steady. No format, verb or product moves.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | each decision, and the test merges |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `evaluation`, `review`, `ui` |

```
1 the flake      the stream test closes after its first frame
2 evaluation     the digest's wording · a frame that does not read · an unreadable file refused by name
3 the render     .env read as the shell reads it · a teardown keeps its cause · the endpoint's remedy
4 import         the 50 MP comment · a write refused alone
5 cancel         nothing to cancel · the remedies that fail · copied or drafted
6 the guard      the printed-command guard provokes draft, draft-from and cancel
7 the UI, docs   ④'s seeds and refusals · comments · README · the sheet's Purpose · a decision
8 the tests      a pid race · a comment · Review's browser tests merged
```

## Why

**Converge reads the backlog, and a finding that repeats a card counts one level worse.** With every card open, the
first `mf-ship` would turn old nits into blocking findings. Most cards are a line and a test, and a stream test that
fails one gate in several would halt an unattended run on its own.

## What Changes

- **The flaky stream test** reads its first frame before the stream closes ([D1](design.md#d1)).
- **Evaluation** names a run by the digest its frame records, states the unreadable frame's rule, and refuses an
  unreadable file by name ([D2](design.md#d2)).
- **The render** reads `.env` as the shell does, keeps a failed body's cause beside a failed teardown, and names the
  tunnel when the endpoint is unreachable ([D3](design.md#d3), [D4](design.md#d4)).
- **Import** refuses a failed write alone and says what its bound refuses ([D5](design.md#d5)).
- **Cancel and draft-from** print remedies that succeed, and a flow with nothing to cancel changes nothing
  ([D6](design.md#d6)).
- **The printed-command guard** provokes the refusals it skipped ([D7](design.md#d7)).
- **The UI and the docs** say what holds ([D8](design.md#d8)); **the tests** stop racing and share their pages
  ([D9](design.md#d9)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `evaluation` — *Every render is a row*: a run is named by the digest prefix its frame records.
- `evaluation` — *Attribute recall counts …*: the same naming, and a new scenario for a run whose frame does not read.
- `review` — *An approval nothing derives from can be cancelled back to its draft*: "copied or drafted", and a new
  scenario for a flow with no approval.
- `ui` — *The page is told of a job as it runs*: the why says what a reopened stream carries.

## Impact

- `isekai/`: `foundation/artifacts.py`, `boundary/gpu.py`, `boundary/comfy/client.py`, `interface/render.py`,
  `pipeline/importing.py`, `pipeline/review.py`, `interface/cli.py`.
- `ui/src/`: `slots.ts`, `components/RendersBlock.vue`, `SheetForm.vue`, `FieldRow.vue`, `ApproveBar.vue`.
- Docs: `README.md`, `docs/decisions.md`, `openspec/specs/sheet/spec.md`'s Purpose.
- Tests across `tests/` and `tests/e2e/test_review.py`.

## Not in this change

- `pod_start.py`'s cards: an edit there waits for an image rebuild.
- gpunit's output streamed to the log, a stale cancel reason on Review, queued saves in `useSheet`, and the
  draft-from gesture that reopens an older draft: each keeps its trigger.
- Carrying a cell's marks in the snapshot, reading an old repeated seed, and raising the 50 MP bound.
