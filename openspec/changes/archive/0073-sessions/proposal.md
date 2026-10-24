---
version: v0.46
backlog: [0063·R17, 0070·R10, 0072·R4, 0072·R8, 0072·R9, 0072·R11, 0072·R14, 0072·R15]
---

# 0073 — sessions

Every render session is a record on disk, and the app shows it from there. `isekai render` writes
`<batch>/sessions/<id>.json` as it starts and keeps it current until it ends; each batch has a Sessions tab, a list
and a page per session; a running render shows on every screen.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the record, its id, the routes, the screens, the indicator, the viewer, the cards |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `cli` · `ui` · `review` |

```
isekai render --session 20261024T091200Z
   │ start ─▶ <batch>/sessions/20261024T091200Z.json   outcome: running, images: []
   │ image ─▶ replaced whole                            images: [1]
   │ end   ─▶ replaced whole                            outcome: done
   ▼
/b/<batch>/sessions ─▶ /b/<batch>/sessions/20261024T091200Z      ● render 09:12 on every screen
```

## Why

**A session lives only in the server's memory.** `/session` shows the job in the slot and redirects to Home
otherwise, so a finished session cannot be found again, and a render started in the terminal never shows.

**`/session` names no batch.** The app bar shows no tabs there, and nothing outside it says a render is running.

**`v0.45.0` shipped with five cards past their trigger** — wording in the README, the design spec, the living specs
and a docstring.

## What Changes

- **The session record** — written by `isekai render` from start to end; `--session <id>` ([D1](design.md#d1),
  [D2](design.md#d2)).
- **The routes** — a batch's sessions and one session, read from the records ([D3](design.md#d3)).
- **The screens** — the Sessions tab, list and page; `/session` gone; the alert's way out at `/billing`
  ([D4](design.md#d4)).
- **The indicator and `⇧S`** ([D5](design.md#d5)).
- **The viewer** — finished images and the batch's photographs, at the Renders tile size ([D6](design.md#d6)).
- **The cards** — `0063·R17`, `0070·R10`, `0072·R4`, and the overdue `0072·R8`, `R9`, `R11`, `R14`, `R15`
  ([D7](design.md#d7)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cli`:
  - ADDED *A render session writes its record into the batch, from its start to its end* — the record, its id,
    none on a refusal before renting.
- `ui`:
  - ADDED *Each batch's render sessions are listed and shown from their records* — the tab, the list, the page, the
    indicator, the viewer.
  - MODIFIED *Render is confirmed in a dialog that quotes what renders, its limit and its price at most* — the
    confirmation opens the session's page.
  - MODIFIED *The render job opens the volume, renders, and closes the volume unless kept* — the job names its
    session; an opening that raises fails its step.
  - MODIFIED *Billing state is read from gpunit's own records* — the alert's way out at `/billing`.
  - MODIFIED *Every screen has a URL naming its batch and its run* — the sessions' addresses and `/billing`.
  - MODIFIED *Review opens a batch at its own address, lists every unrendered sheet, and Approve stays on the sheet*
    — a copy's cancel leaves the sheet on what the flow holds (`0072·R14`).
- `review`:
  - MODIFIED *An approval nothing derives from can be cancelled back to its draft* — `--from` copies the source's
    newest approval again (`0072·R11`).

## Impact

- **Code:** `isekai/foundation/artifacts.py`, `isekai/interface/render.py`, `isekai/interface/cli.py`,
  `isekai/interface/ui/jobs.py`, `isekai/interface/ui/app.py`, `isekai/interface/ui/library.py`,
  `isekai/pipeline/review.py`, `ui/src/router.ts`, `ui/src/App.vue`, `ui/src/api.ts`, `ui/src/types.ts`,
  `ui/src/views/Review.vue`, `ui/src/components/ImageViewer.vue`, `ui/src/app.css`; new `ui/src/views/Sessions.vue`,
  `ui/src/views/SessionPage.vue`, `ui/src/views/Billing.vue`; deleted `ui/src/views/Session.vue`.
- **Tests:** `tests/test_render.py`, `tests/test_ui_jobs.py`,
  `tests/test_ui_api.py`, `tests/e2e/test_render.py`, `tests/e2e/conftest.py`.
- **Docs:** `README.md`, `isekai/interface/README.md`, `isekai/interface/ui/README.md`, `ui/design/spec.md`.

## Not in this change

- **A second job slot.**
- **Money after the quote** — the record holds none.
- **gpunit** — its session and records are unchanged.
- **A run file's format** — the record is a batch's file, beside its log.
