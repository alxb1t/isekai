# Design — 0070 review

How Review opens a batch, which sheets its rail holds, what Approve does, and how the screen is laid out.
**Verdict: feasible** — the batch store holds the hub, `shortfall` counts what is short, and `ImageViewer` exists;
the screen is recomposed from them.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `c71e5af` (`v0.43.0`):

- **The queue:** Approve opens `after(…)` or the hub (`ui/src/views/Review.vue:207-236`); Revise's queue rides
  `?queue=` (`nextRevised`, `:175-185`); `after`, `reviewQueue`, `queued` (`ui/src/composables/useQueue.ts:35`,
  `:116`, `:121`); `useQueue` lists the queue and the open sheet (`:49`). e2e `tests/e2e/test_queue.py:16`, `:25`,
  `:34`; `test_revise_opens_review_on_the_revision_and_approving_it_ends_at_the_hub` (`tests/e2e/test_render.py:113`).
- **Routes:** `/b/:batch/review/:digest/:flow` only (`ui/src/router.ts:18`). `⇧R` pushes the queue's head
  (`ui/src/App.vue:66-71`); the Review tab is a `<span>` (`:109-110`); the hub's *Review next* and *nothing left to
  review* (`ui/src/views/Hub.vue:82`, `:395-397`).
- **The cell:** `library.Cell` holds `stage`, `renders`, `refusal`, `status`, `newest` (`isekai/interface/ui/library.py:165-179`);
  `shortfall` (`isekai/pipeline/generate.py:323`); `status` is `approved | re-opened | draft` (`isekai/pipeline/review.py:109`).
- **The header:** `ui/src/components/AppHeader.vue` (`Review.vue:488-513`) — `isekai review`, the run line, receipts
  named by file, the page's refusal line. `ui/src/components/SheetHeader.vue:24-26` — "n fields, schema order. n
  filled · n empty."
- **A revision:** `render being revised · <seed>` heads the render alone (`ui/src/components/SourcePanel.vue:84-86`);
  "click or `↵` to fill window" (`:73`). Discard and its ask sit under ④ (`Review.vue:571-600`).
- **④:** `ui/src/components/RendersBlock.vue`, chips and a `+ seed` input; the fourth pane (`ui/src/panes.ts`).
  `renders_of` refuses a seed out of range and a count below its seeds, not a repeat (`isekai/foundation/artifacts.py:451`).
- **The lenses:** `PhotoOverlay` (`Review.vue:610`); `CheatsheetOverlay` composes its `.overlay` classes;
  `ui/src/components/ImageViewer.vue` takes keys as an overlay, with no stepping.
- **Saves:** `useSheet.flush` tracks saves in `inFlight` (`ui/src/composables/useSheet.ts:52`, `:119-151`); `useApproval.approve`
  states the page's `saved` receipt (`ui/src/composables/useApproval.ts:26`).

| measured at the cut | value | command |
|---|---|---|
| e2e tests | 23 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |
| vitest tests | 20 | `cat ui/src/*.test.ts ui/src/*/*.test.ts \| grep -c "^spec("` |
| tests in `tests/test_review.py` | 60 | `grep -c "def test_" tests/test_review.py` |

## Goals / Non-Goals

**Goals:** Review at a batch's address; a rail of what is not done; Approve as an act; no path on screen; ④ that says
what the next render draws. **Non-Goals:** Cancel approve; a source's own name in labels; Sessions.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | route `/b/:batch/review`, `name: 'review-head'`, to a new `ui/src/views/ReviewHead.vue`: it reads `head(hub)` from the batch store and `router.replace`s to the sheet, or shows *No sheet waits for review* with a link to the hub; the Review tab is a `RouterLink` there carrying the unapproved count; `⇧R` goes there; the hub's *Review next* and *nothing left to review* go | the URL names the run; the tab has a target | resolving on the server |
| [D2](#d2) | `library.Cell` gains `short: int \| None` — `shortfall` of the newest approval; `None` while unapproved, `0` on a refused count | one count, the render stage's | `count - renders` in the browser |
| [D3](#d3) | `useQueue.ts` keeps pure functions: `head(hub)` per [D1](#d1); `rail(hub, flow, current)` — the flow's sheets that are unapproved or `short > 0`, plus the open one; `queue` stays for the tab's count; `after`, `queued`, `reviewQueue` go. `BatchRail` marks ○ ◐ ● ◌; the flow's name heads the rail | the rail is what is not done | |
| [D4](#d4) | Approve stays: after `approval.approve` the batch store reads the hub again and the sheet reopens read-only; Revise pushes Review on its first draft with no query; Discard stays on the sheet, which reloads | approving is an act | |
| [D5](#d5) | `AppHeader.vue` deleted: the saving spinner and `saved 13:59` join the sheet's kicker, `③ SHEET — DRAFT · saved 13:59`, and `APPROVED 14:12:40` when approved; every refusal shows in `ApproveBar`; the "n fields…" line goes | rule 2, no path; one place for a refusal | a slimmer header |
| [D6](#d6) | a revision: one header row — `① PHOTOGRAPH · 1073×1406`, `RENDER BEING REVISED · seed 5`, *Side by side* `⇧C` at its right — over the photograph and the render, top-aligned at equal height; no how-to text; Discard in `ApproveBar`, 12 px left of Approve, asking first | J5·4; the operator's screenshot | captions below |
| [D7](#d7) | `ui/src/slots.ts`: `slots(renders)` — `count` slots, the listed seeds first, the rest `null`; `renders(slots)` back; `−` drops the last random slot, else the last seed; a typed digit sets its slot at once; a repeat is refused in the slot. `RendersBlock` draws them in a ④ panel about 230 px right of the sheet rows; `Tab` through `−`, `+`, the slots, `j` / `k` between the count and the slots. `renders_of` refuses a repeated seed | the settled ④; the server holds the rule | a new `renders` shape |
| [D8](#d8) | `ImageViewer` takes `images` and an index, `←` / `→` stepping through them; Review opens the photograph with the rail's sheets and the revised render alone; *Side by side* is a second `<dialog>`, the pair at equal height, fit only; `PhotoOverlay.vue` deleted, its `.overlay` classes kept for `CheatsheetOverlay` | one viewer | keeping the lens |
| [D9](#d9) | `0065·R15`: *Discard asks before it deletes*, its own e2e test; `0065·R17`: the design spec reads *Discard draft* asks, then deletes; `0061·R8`: the queue e2e tests replaced per [Tests](#tests); `0061·R16`: `flush()` awaits the saves in `inFlight`, and Approve awaits `flush()` | the cards' fixes | |

**Arc Q110**, Approve moving to the next sheet, is overturned by [D4](#d4).

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | `ui:review:a-cell-counts-what-it-lacks`, `review:renders:a-repeated-seed-is-refused` | `ui:queue:opening-a-sheet-writes-its-draft` rebound to `ui:review:opening-a-sheet-writes-its-draft` | `tests/test_ui_library.py`, `tests/test_review.py`, `tests/test_ui_api.py` |
| unit · vitest | `ui:review:a-batch-opens-its-head`, `ui:review:the-rail-holds-every-unrendered-sheet`, `ui:review:each-image-has-a-slot`, `ui:save:an-approval-waits-for-a-save-in-flight` | `useQueue.test.ts` against `rail` | `ui/src/composables/useQueue.test.ts`, `ui/src/slots.test.ts`, `ui/src/composables/useSheet.test.ts` |
| e2e | `ui:review:approve-stays-on-the-sheet`, `ui:review:the-photograph-opens-in-the-viewer`, `ui:revise:discard-asks-before-it-deletes`, `ui:revise:side-by-side-shows-the-pair` | `ui:queue:a-failure-after-approval-is-shown` rebound to `ui:review:`; the revise test ends on its sheet | `tests/e2e/test_queue.py`, `tests/e2e/test_render.py`, `tests/e2e/test_review.py` |

**End-to-end runs added:** four tests, two removed — net two, on Chromium only (T4). Staying on the sheet, the viewer,
Discard's ask and *Side by side* are what a browser alone shows (T1); each carries its own scenario, so none is a step
of another test (T2). The head, the rail and the slots are vitest units.

| removed or merged | its assertions and scenario ids now carried by |
|---|---|
| `test_approve_opens_the_next_unapproved_sheet` (`tests/e2e/test_queue.py:17`), `ui:queue:approve-moves-to-the-next-sheet` | `test_approve_stays_on_the_sheet`, `ui:review:approve-stays-on-the-sheet` — the behaviour is replaced |
| `test_approving_the_last_sheet_opens_the_hub` (`tests/e2e/test_queue.py:26`), `ui:queue:after-the-last-sheet-the-hub-opens` | `test_approve_stays_on_the_sheet` — no approval leaves the sheet |

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** deleting `PhotoOverlay.vue` takes the `.overlay` classes `CheatsheetOverlay` composes → the classes stay
  in `ui/src/app.css`.
- **[Risk]** a sheet open in Review drops out of `rail` once rendered → `rail` always keeps the open sheet.
- **[Trade-off]** ◐ edited lasts one sitting → the server records *edited* only at approval.

## Verdict

**Feasible.** Every count and image the screen needs is already served; the change moves where they show.
