# Design — 0074 two job slots

How the job runner holds a Prepare and a render at once, and how the wire and the screens follow.
**Verdict: feasible** — each job is already its own child process watched by its own thread; the single slot is
bookkeeping in `Jobs` and the readers of one `job`.

## Context

See [proposal](proposal.md) — *Why*. What holds at the cut, `main` at `15bb6a9` (`v0.46.0`):

- **`Jobs` holds one of everything:** `_job`, `_child`, `_stopping`, `_thread` (`isekai/interface/ui/jobs.py:196-199`);
  `_refuse_running` refuses any job while one runs (`:286`); `stop` (`:296`), `wait` (`:304`), `shutdown` (`:310`)
  and `_interrupt` (`:349`) act on it; `_spawn` starts the child with its stderr written straight to the batch's log
  (`:515-531`).
- **The app:** billing asks `jobs.running() == "render"` (`isekai/interface/ui/app.py:235`); `post_prepare` (`:422`);
  `POST /api/job/stop` (`:424-427`); `_held` names *Prepare is running.* (`:442-447`); `jobs.slot()` for the render
  check (`:525`) and the snapshot's `job` (`:573`). Prepare checks no billing alert.
- **The browser:** the live store's one `job` (`ui/src/stores/live.ts:32`, `:42`), filled by the snapshot and the
  `job` event (`:131`, `:136`), stopped by `stop` (`:143`); `stopJob` posts `/api/job/stop` (`ui/src/api.ts:102-103`).
  Its readers: `ui/src/App.vue:20-31`, `:179`; `ui/src/stores/batch.ts:33`, `:170-181`; `ui/src/views/Hub.vue:45-47`,
  `:79`, `:229-232`, `:504`; `ui/src/components/RenderBar.vue:22`, `:50-54`; `ui/src/components/RenderDialog.vue:32-38`;
  `ui/src/views/Billing.vue:11`.
- **The rule:** design spec rule 6, *One job slot* (`ui/design/spec.md:24`), whose billing alert *holds the slot*;
  §8's lifecycle (`:430`).
- **`0073·R9`:** `ui/src/sessions.ts:23` and `Hub.vue:45` describe slot-only liveness; the `render.py` row of
  `isekai/interface/README.md:39` misses `ui/library.py` and `tests/test_ui_api.py`.

| measured at the cut | value | command |
|---|---|---|
| tests in `tests/test_ui_jobs.py` | 22 | `grep -c "def test_" tests/test_ui_jobs.py` |
| e2e tests | 27 | `cat tests/e2e/test_*.py \| grep -c "def test_"` |
| vitest tests | 29 | `cat ui/src/*.test.ts ui/src/*/*.test.ts \| grep -c "^spec("` |

## Goals / Non-Goals

**Goals:** a Prepare and a render side by side, in any batches; each with its own Stop and reasons; both stopped
with the surface. **Non-Goals:** job records on disk; two of one kind; a change to gpunit or the session record.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `Jobs` keeps a `_Slot` per kind — job, child, stopping, thread — in `_slots: dict[Kind, _Slot]`; `_refuse_running(kind)` refuses only that kind, naming its job; `slot(kind)`, `running(kind)`, `stop(kind)`, `wait(kind)` per kind; one lock still guards both | each kind waits only for its own | two `Jobs` instances |
| [D2](#d2) | `shutdown` interrupts both slots at once, then waits for each: the render's bounded wait (teardown plus one volume verb) and its terminal remedy unchanged; Prepare's children stop at once | no window left billing; nothing waits on Prepare | stopping one before the other |
| [D3](#d3) | `_spawn` pipes the child's stderr; a reader thread per job writes each line to the batch's log as `[prepare] …` or `[render] …` | interleaved lines stay readable | the CLI prefixing its own lines |
| [D4](#d4) | the snapshot carries `jobs: {prepare, render}`, each `null` or a slot; the `job` event carries `kind`; `_held` keeps a render running, a pod billing and no key, and drops Prepare; `POST /api/jobs/{kind}/stop`, `kind` refused unless `prepare` or `render`; `POST /api/job/stop` goes, with no shim | one wire per slot | |
| [D5](#d5) | the live store holds `jobs.prepare` and `jobs.render`; each reader reads its own — the Prepare bar, the Render bar, `SessionPage.vue`, the indicator, the batch store's watches, the cancel's render check; `Hub.vue`'s `blocked` and *A render is running* go; the job strip shows one item per running job with its totals, else each kind's last outcome | each screen reads what it shows | |
| [D6](#d6) | design spec rule 6 → *Two job slots, one Prepare and one render; a job of either kind waits only for its own; an unresolved billing alert holds the render slot*; §8's lifecycle per slot; `0073·R9`: `sessions.ts:23` and `Hub.vue:45` reworded to disk liveness and the render slot, the README's `render.py` row completed | the rule where it lives; the card's fix | |

## Tests

| layer | added | edited | where |
|---|---|---|---|
| unit · pytest | `ui:prepare:a-render-runs-beside-a-prepare`, `ui:prepare:stopping-the-surface-interrupts-both`, `ui:prepare:the-log-names-each-job` | `ui:prepare:one-job-at-a-time` — a second of one kind; `ui:events:a-connection-starts-with-a-snapshot` — both slots | `tests/test_ui_jobs.py`, `tests/test_ui.py` |
| unit · vitest | `ui:events:a-job-event-fills-its-kinds-slot` | none | `ui/src/stores/live.test.ts` |
| e2e | none | `test_prepare_takes_the_assigned_cells_to_their_sheet_and_no_other` gains a step: while Prepare runs, the Render bar of the `render` batch is enabled | `tests/e2e/test_prepare.py` |

**End-to-end runs added:** none — one step in the Prepare test, which already holds a Prepare running (T2).

**Removed or merged:** none.

## Dependencies

None.

## Risks / Trade-offs

- **[Risk]** shutdown with both running leaves the render's window open if Prepare's wait comes first → both are
  interrupted at once and the render's wait is the bound; Prepare adds none.
- **[Risk]** a reader that keeps reading the old `job` shows a stale state → `job` leaves the live store, so a reader
  left behind fails the typecheck.
- **[Trade-off]** a reader thread per job for the log → it ends with its child.

## Verdict

**Feasible.** The concurrency exists; the slots, the wire and the readers follow it.
