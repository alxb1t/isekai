# Design — 0071 the review patch

How each overdue card from `v0.44.0` is paid within a patch.
**Verdict: feasible** — wording, one narrowed promise and two test steps; no requirement, format or product change.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `0477084` (`v0.44.0`):

- **`0070·R3`** — `openspec/specs/ui/spec.md:62` "name the artifact that holds it"; no file name shows since `v0.44.0`.
- **`0070·R4`** — `README.md:259` "Approve moves to the next"; `README.md:264` "opens Review on each draft".
- **`0070·R5`** — `ui/src/composables/useSheet.ts:92` and `ui/src/views/Review.vue:203` send refusals to "the header
  line"; `ui/src/components/TagInput.vue:22` "while the lens moves the batch".
- **`0070·R6`** — `openspec/specs/ui/spec.md:1416` "the others in the rail"; `rail()` holds one flow
  (`ui/src/composables/useQueue.ts:43`); `ui/src/components/ReviseConfirm.vue:33-34` opens the first draft.
- **`0070·R7`** — `openspec/specs/review/spec.md:304` "seeds listed a seed outside".
- **`0070·R16`** — no test drives `ui/src/views/ReviewHead.vue:20-31`; `test_a_reload_lands_on_the_same_hub_and_the_same_review`
  (`tests/e2e/test_routes.py:9-36`) opens the main batch, whose head is `ada`'s draft. The `shown` batch holds one
  approval with all its images, so its head is the empty page (`tests/e2e/conftest.py:58`, `:185`).
- **`0070·R18`** — `openspec/specs/ui/spec.md:69` "lists only the sheets not yet rendered"; `rail()` also keeps the
  open sheet.
- **`0070·R19`** — `openspec/specs/ui/spec.md:650` asks whenever a save is unanswered; `leave()` asks only while an
  edit waits (`useSheet.ts:142-145`, `Review.vue:457-461`).
- **`0070·R21`** — `useSheet.ts:59-62` "Two saves can be in flight at once".

## Goals / Non-Goals

**Goals:** every card closed; the text says what the code does. **Non-Goals:** Revise across flows; any behaviour.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the delta: R3 "approved and when, naming no file"; R18 "the sheets not yet rendered and the one open"; R19 "while an edit waits behind a save in flight"; R6 "the others of its flow in the rail"; R7 the comma restored | each card's first fix; a patch narrows, it does not add | opening the flow with most drafts (R6) |
| [D2](#d2) | `README.md:259` "Approve moves to the next" → "Approve stays on the sheet, read-only"; `:264` "opens Review on each draft" → "opens Review on the first draft it wrote, the rest in the rail"; the comments: "the header line" → "the approve bar"; "while the lens moves the batch" → "while the viewer steps its images"; `useSheet.ts:59-62` → "A save can answer while a later one of its input waits behind it, so its budget and refusal are stale" | the cards' fixes | |
| [D3](#d3) | the reload test gains steps: `/b/<main batch>/review` lands on `ada`'s draft URL; `/b/shown/review` says none waits; the scenario `ui:routes:a-reload-lands-on-the-same-screen` gains both as ANDs | a test carries one scenario's key, so a step extends this one (T2) | a new scenario and test |

**Erratum, archived 0070:** `openspec/changes/archive/0070-review/design.md`'s D9 and `proposal.md` do not record
that a page closing while an edit waits behind a save in flight asks before it goes (`0070·R19`). The archive is
frozen; this note and the corrected SHALL are the record.

## Tests

| layer | added | edited | where |
|---|---|---|---|
| e2e | none | `test_a_reload_lands_on_the_same_hub_and_the_same_review` gains the head and empty-page steps | `tests/e2e/test_routes.py` |

**End-to-end runs added:** none — two steps in an existing test (T2).

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Trade-off]** Revise over two flows still leaves the second flow's drafts to the batch's head → the spec now says
  so; a cross-flow rail waits for the next change to the rail.

## Verdict

**Feasible.** Nothing a patch may not hold.
