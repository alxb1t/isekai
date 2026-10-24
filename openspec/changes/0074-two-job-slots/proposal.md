---
version: v0.47
backlog: [0073·R9]
---

# 0074 — two job slots

One Prepare and one render can run at once, each with its own slot, its own Stop and its own reasons. A render in
one batch no longer holds back a Prepare in another, or in the same one.

| read | for |
|---|---|
| this file | why, and what changes |
| [design](design.md) | the slots, the refusals, Stop, shutdown, the log, the wire, the screens |
| [tasks](tasks.md) | the phases, in build order |
| `specs/` | `ui` |

```
Jobs
├─ prepare slot ── tag → caption → sheet children     Stop: POST /api/jobs/prepare/stop
└─ render slot  ── volume up → render → volume down   Stop: POST /api/jobs/render/stop
      a second job of a kind is refused; the other kind runs beside it
```

## Why

**One slot holds both kinds.** A render of half an hour blocks every Prepare, in every batch, though the two share no
file and no machine: Prepare runs on the local models, a render on a rented GPU.

**The single slot runs through the whole surface** — the server's job runner, the stream's snapshot, the live store,
the Stop route, the bars' reasons and the job strip.

## What Changes

- **Two slots in the job runner** — refusals, Stop and the child per kind; shutdown of both ([D1](design.md#d1),
  [D2](design.md#d2)).
- **The batch's log names each job** ([D3](design.md#d3)).
- **The wire** — the snapshot's `jobs`, the `job` event's kind, Render's hold, Stop per kind ([D4](design.md#d4)).
- **The screens** — each reader its own slot; the job strip shows both ([D5](design.md#d5)).
- **The docs and the card** — design spec rule 6 and §8; `0073·R9` ([D6](design.md#d6)).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui`:
  - MODIFIED *Prepare runs what changed as one job, and refuses before it starts when Ollama does not answer* — one
    job of each kind at a time; Stop per kind; stopping the surface interrupts both; the log names each job.
  - MODIFIED *The page is told of a job as it runs* — the snapshot carries both slots.
  - MODIFIED *Render is confirmed in a dialog that quotes what renders, its limit and its price at most* — the bar is
    disabled while a render runs, not any job.

## Impact

- **Code:** `isekai/interface/ui/jobs.py`, `isekai/interface/ui/app.py`, `ui/src/api.ts`, `ui/src/types.ts`,
  `ui/src/stores/live.ts`, `ui/src/stores/batch.ts`, `ui/src/App.vue`, `ui/src/views/Hub.vue`,
  `ui/src/views/SessionPage.vue`, `ui/src/views/Billing.vue`, `ui/src/components/RenderBar.vue`,
  `ui/src/components/RenderDialog.vue`, `ui/src/bars.ts`, `ui/src/sessions.ts`.
- **Tests:** `tests/test_ui_jobs.py`, `tests/test_ui.py`, `tests/e2e/test_prepare.py`, `ui/src/stores/live.test.ts`.
- **Docs:** `ui/design/spec.md`, `isekai/interface/README.md`, `isekai/interface/ui/README.md`.

## Not in this change

- **Job records on disk** — the server's memory and the reconnect snapshot stay the state; a review of state
  management decides that.
- **Two jobs of one kind.**
- **gpunit, the session record, a format.**
