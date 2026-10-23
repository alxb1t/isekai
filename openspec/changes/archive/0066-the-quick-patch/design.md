# The quick patch — design

Repair the surface's existing display and shutdown contracts. **Verdict: feasible.**
The scope is the [proposal](proposal.md); the [delta](specs/ui/spec.md) supplies the test keys.

## Context

Rechecked at `c70c753aaddb1882dad5ba723815cd429521a70d`, after the instruction-file move to `AGENTS.md`.
Application code is unchanged from the grilling's `c94599080244dacd7f53b2678f675f692020ace4`.
The source's workflow commands and declarations of completed checks are evidence only; this cut re-runs its own checks.

| premise | evidence at the cut |
|---|---|
| Streams close after the server waits | `isekai/interface/ui/events.py:82–99`; lifespan closes the broadcast at `isekai/interface/ui/app.py:229–236`; grace is configured at `:1404–1408` |
| Interrupt escapes `serve` | `isekai/interface/ui/__init__.py:31–63` calls `run` without handling `KeyboardInterrupt` |
| Initial empty separators, missing totals | `ui/src/views/Hub.vue:482`; `_Job` at `isekai/interface/ui/jobs.py:119–145` lacks progress; `:469–470` sets stage/flow when a child starts |
| The progress unit is a cell | `ui/design/spec.md:80–82,145`; the accepted plan's `(flow, run)` pairs are available at `jobs.py:96–115` |
| The clock already ticks | `ui/src/composables/useLive.ts:11,16,40–44`; `ui/src/App.vue:20–29` uses it for Render |
| Count nouns are hardcoded | `ui/src/views/Home.vue:90,103,110`, `Hub.vue:360`; `ui/src/components/AppHeader.vue:31`, `ImportSheet.vue:269`, `RenderDialog.vue:88`, `SheetHeader.vue:23` |
| Header spacing is inconsistent | `ui/src/app.css:1414–1420,1731–1734` lacks a header gap and gives Add sources its own right margin |
| Confirmation checks the total and limit | `app.py:481–498`; the SHALL is accurate at `openspec/specs/ui/spec.md:865–866`, its why at `:870–872` is not |
| A finished failed close loses its remedy | `jobs.py:310–318` tests thread liveness; `:407–412` marks a failed close; `app.py:233–234` has closed billing |
| Existing snapshot equality needs extension | `tests/test_ui_jobs.py:157–164` compares the complete Prepare slot |
| Preview is already part of the result | `openspec/specs/ui/spec.md:749–752,775–780` and the existing preview test in `tests/test_ui_api.py` |
| Current prose misstates imports and revision helpers | `docs/principles.md:75–81`; `app.py:424–455`; `isekai/interface/ui/library.py:343–357`; `isekai/pipeline/review.py:728–734` |

## Goals / Non-Goals

**Goals:** restore the designed totals, end streams before graceful shutdown waits on them, and preserve cleanup.
Keep the patch's [scope boundary](proposal.md#not-in-this-change) and existing CLI, artifact and spend semantics.

**Non-Goals:** restructure shared state, redesign views, suppress logger output, move architectural debt or edit frozen history.
No dependency, format migration, paid phase or human-operated phase is needed.

## Decisions

The operator settled the product choices; the implementation choices below make those outcomes runnable.

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | keep preview as a file's result; remove its redundant SHALL clause | the operator accepted this interpretation and kept the shipped numbering | retagging, removing previews |
| [D2](#d2) | retain total/limit confirmation and correct its why | equal-total source changes are outside the agreed comparison | exact-work identity tokens |
| [D3](#d3) | keep Prepare progress in the job slot | snapshots must restore it and the accepted plan fixes its denominator | browser-local counters, a disk record |
| [D4](#d4) | end streams when signal handling begins | lifespan shutdown comes after uvicorn's wait | longer waits, blanket log suppression |
| [D5](#d5) | warn from window-close state after the wait | a failed close may finish its worker and still leave a volume open | using thread liveness as billing evidence |
| [D6](#d6) | correct current prose and record archive errata here | archived designs are frozen by `AGENTS.md` | rewriting archived proposals and designs |
| [D7](#d7) | share count grammar and extend existing browser flows | grammar is a pure function and the target pages already have tests | a new browser setup for a label or gap |

### D1

Keep each staged file's preview and its existing scenario and tests.
The import SHALL drops only `, and a preview of each file read`; the result still includes that preview.
The release-rule interpretation is settled; no shipped version or tag changes.

### D2

The existing confirmation body is `{keep_open, limit_s, images}`.
It rejects a longer limit and any changed total; it does not compare source or approval identities.
Clarify that boundary in the living requirement's why through the delta and in [D4](../../../docs/decisions.md#d4--the-ui-runs-stages-only-as-the-clis-children).

### D3

A **cell** is an accepted `(flow, run)` pair; its identity and the denominator come from `Step` entries, not live hub counts.
Add optional Prepare `progress: {started, of, done}` to `_Job.describe()` and `ui/src/types.ts`'s `JobSlot`.
The start is recorded once with `Jobs`' existing `now` seam; the completed identities remain an internal set.

Increment only for an accepted cell's successful sheet report whose returned cell has reached sheet or later.
Ignore other stages, refusals, unknown identities and repeated completions; publish changed job progress as well as the cell event.
Keep the denominator fixed and copy the public progress object when describing the slot.

The `/events` snapshot already reads `Jobs.slot()`; retain its start, total and completed count on reconnect.
Expose shared Prepare formatting from `ui/src/composables/useLive.ts`, using its existing `now` and `clock`.
`App.vue` and `Hub.vue` draw the same progress, including `0 of N` before the first stage and a ticking elapsed time.

```text
accepted cells -> fixed total + started
stage report   -> verified sheet completion -> completed set -> slot + job event
reconnect      -> slot snapshot             -> strip + bar, same start and counts
```

The initial null stage/flow values explain empty separators only before a child starts; this cut makes no claim that they stay empty.
Render's session data and formatting stay unchanged; the motion work beyond the ticking timer is excluded.

### D4

Make the broadcast's close state durable in memory and idempotent, so a stream subscribing after close also ends promptly.
At signal handling, mark the stop state without taking a broadcast lock and schedule queue wake-up on the event loop.
Then delegate to uvicorn's normal exit handler; the scheduled close wakes subscribed queues before its graceful wait.

`stream()` observes close state before waiting and yielding; lifespan cleanup still interrupts jobs and closes imports and billing.

Use `uvicorn.Server` with a local `handle_exit` override inside `app.py`'s `run`; retain the existing Config settings.
Delegate signal bookkeeping and repeated-interrupt semantics to the base handler; do not replace uvicorn's signal capture/replay.
Catch a surviving `KeyboardInterrupt` at `serve()` and return 130 after the cleanup path finishes.

```text
SIGINT -> close flag + wake streams -> uvicorn graceful shutdown -> lifespan cleanup -> quiet status 130
                                               running job -> interrupt -> pod teardown -> window close
```

The installed uvicorn source confirms this seam: `Server.handle_exit` owns exit bookkeeping, while `Server.shutdown` waits before lifespan shutdown.
The implementation must retain wait announcements, teardown output and the recovery command; it must not suppress genuine cleanup failures.

### D5

After the existing bounded shutdown wait, inspect the render session's `volume down` state under the job lock.
States `done` and `kept` need no remedy; failed and unfinished closes print `uv run --env-file .env gpunit volume down`.
A completed failed close must not be described as a wait timeout; preserve the timeout wording for an unfinished close.

Do not add provider calls to shutdown or change how long it waits.
The job still owns interruption and cleanup; the terminal remedy is evidence about the close, not an inferred provider inventory.

### D6

Correct the current descriptions without moving the implementations.
Leave the backlog intact during cut and build; release consumes the proposal's qualified ids.

| card | current change |
|---|---|
| `0063·R25` | `isekai/interface/ui/__init__.py`: `Prepare is the exception` -> `Prepare and Render are the exceptions`; the module map names both |
| `0063·R26` | `docs/principles.md`: UI quote imports are `short`, `quote` and `run_ids`; `quote` reaches `estimate` |
| `0065·R16` | `docs/principles.md`: `_origin` duplicates review-field comparison; only `paired` and `_revision` need rendered seeds |
| `0063·R27` | the delta and `docs/decisions.md` clarify [D2](#d2), without altering confirmation code |
| `0064·R7` | the delta records [D1](#d1), preserving preview coverage |
| `0063·R28` | [D5](#d5) repairs the terminal remedy and the delta states the kept-window exception |

### D7

Add the planned `ui/src/words.ts` with `noun(count, singular, plural = singular + "s")`, returning the singular only at one.
Pass `"batches"` explicitly for `"batch"`; the other named labels use the default plural.
Use it for batch, source, flow, input, file, image and field labels in the source files named by the evidence table.
The planned `ui/src/words.test.ts` checks zero, one and plural values under the delta's count-label key.

Set `.hub__head`'s `gap` to `12px` and remove `.hub__add`'s redundant right margin, keeping its alignment.
Extend `test_a_tick_assigns_the_flow_and_survives_a_reload` to assert the computed header gap independently of the tick.
Document the count grammar and gap in `ui/design/spec.md`; do not change its disabled-reason rule.

## Tests

Use the lowest useful layer; keep every existing test and scenario binding.
New symbols and files in this table are planned additions, not claims about HEAD.

| layer | test / file | assertion and binding |
|---|---|---|
| browser unit | new `ui/src/words.test.ts` | zero/one/plural grammar; `ui:batch-folder:count-labels-use-singular-at-one` |
| unit | new `test_prepare_totals_count_cells_once` in `tests/test_ui_jobs.py` | multiple flows, tag/caption reports, successful sheet completion, refusal, unknown identity and duplicate completion; `ui:prepare:totals-count-cells-not-stages` |
| unit | new `test_reconnect_keeps_prepare_progress` in `tests/test_ui_jobs.py` | snapshot preserves original start, fixed total and completed count; `ui:events:a-reconnect-keeps-prepare-progress` |
| unit | existing `test_stop_interrupts_the_stage_and_starts_no_later_one` | extend exact slot equality for progress; retain its existing binding and assertions |
| unit | new `test_closed_broadcast_ends_existing_and_late_streams` in `tests/test_ui.py` | an existing subscription wakes promptly and a late subscription terminates after close; `ui:events:stopping-ends-open-streams-quietly` |
| unit | new `test_sigint_ends_streams_without_cancellation_output` in `tests/test_ui.py` | real subprocess and HTTP streams, parametrized over idle, an open stream and concurrent streams; `ui:events:stopping-ends-open-streams-quietly` |
| unit | new `test_serve_returns_130_for_keyboard_interrupt` in `tests/test_ui.py` | stub the server call, verify quiet status 130 through `serve`; same stopping key |
| unit | new `test_failed_close_at_stop_names_the_fix` in `tests/test_ui_jobs.py` | failed volume close completes within the wait, worker ended, remedy still printed; `ui:render-job:a-failed-close-at-stop-names-the-fix` |
| unit | new `test_kept_window_at_stop_needs_no_remedy` in `tests/test_ui_jobs.py` | teardown occurs, kept window stays open, no close warning; `ui:render-job:a-kept-window-needs-no-close-remedy` |
| unit | existing successful-stop and timeout tests in `tests/test_ui_jobs.py` | retain teardown/wait assertions; successful close has no remedy and unfinished close still has one |
| e2e | existing `test_a_tick_assigns_the_flow_and_survives_a_reload` in `tests/e2e/test_prepare.py` | computed 12 px gap; retain tick/reload assertions and `ui:hub:a-tick-assigns-the-flow` |
| e2e | existing `test_prepare_takes_the_assigned_cells_to_their_sheet_and_no_other` in `tests/e2e/test_prepare.py` | running totals in strip/bar, second tick, reload stability and unchanged nonassigned cells; retain `ui:prepare:prepare-runs-the-assigned-cells` |

For the running Prepare test, add a file-controlled reader only for `hub-prepare` in `tests/e2e/wiring.py`.
`tests/e2e/conftest.py` exposes its release path through `Served`; the browser test releases it in `finally`.
The reader waits with a deadline, so the test can observe a timer tick and reload without timing a fast fake stage.
No fixture file is written into the real library or read by production wiring.

The subprocess test calls the real `serve` with the suite's wiring, using real uvicorn and loopback HTTP.
Its test harness replaces `ensure_built` with a minimal temporary bundle and points the library and billing records at temporary roots.
Wait for each stream's snapshot before SIGINT, verify EOF and status 130, and capture output without keys or real billing records.
Use `finally` to terminate and reap a child even when an assertion fails; the idle case also verifies the fallback with no subscribers.

| measurement | value | command / basis |
|---|---|---|
| existing browser test functions | 17 | `python3 -c 'import ast,pathlib; print(sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith("test_") for p in pathlib.Path("tests/e2e").glob("test_*.py") for n in ast.walk(ast.parse(p.read_text()))))'` |
| additional browser tests and runs | 0 | the plan extends the named functions in `tests/e2e/test_prepare.py`; the same AST command must remain `17` |
| browser engine | Chromium | `Makefile`'s `browsers` target; no engine matrix added |

**Deletion/merge table:** None. No test is deleted, renamed or merged; no scenario id is removed.
No additional end-to-end setup is justified: the existing hub tests already reach the states needed.

## Historical errata

These cards concern frozen artifacts; their corrections live here and the original files stay unchanged.
`AGENTS.md:64–66` freezes archived design, and `openspec/changes/archive/0023-backlog-paydown/proposal.md:8–10` records the archive-only retirement precedent.

| card | archived claim | correction and evidence |
|---|---|---|
| `0063·R24` | `openspec/changes/archive/0063-render/design.md:137` omits `images` | the request body and comparison are those in [D2](#d2); implementation `app.py:481–498` |
| `0064·R8` | `openspec/changes/archive/0064-the-import-sheet/proposal.md:57–59` omits impacted files | `git diff --name-only v0.39.0 v0.39.1` also names `isekai/shared/image.py`, UI `events.py` and `library.py`, `ui/src/api.ts`, `ui/src/app.css`, `tests/test_importing.py` and the interface/UI/pipeline/shared READMEs |
| `0065·R18` | `openspec/changes/archive/0065-revise/proposal.md:67–71` omits impacted files | `git diff --name-only v0.39.1 v0.40.0` also names `isekai/foundation/run.py`, `artifacts.py`, `isekai/interface/ui/library.py`, `isekai/pipeline/generate.py`, `docs/decisions.md`, `docs/principles.md`, directory READMEs, `tests/e2e/conftest.py`, `tests/test_pipeline_cli.py` and browser files listed below |

The browser omissions for `0065·R18` are `ui/src/api.ts`, `app.css`, `types.ts`, `components/FieldRow.vue`,
`ReviseConfirm.vue`, `SheetForm.vue`, `SourcePanel.vue`, `composables/useQueue.ts` and `composables/useSheet.test.ts`.
The commands above also show the spec, lock and release metadata; they are the complete change inventory, not the proposal's short list.

## Cut self-check

This checks the planned build contract, not the unbuilt behaviour. Task `Verify:` checks were read and not executed.

| item | state | evidence |
|---|---|---|
| I1 | at commit | branch `v0.40.1_the_quick_patch` cut from clean `main`; commit and final clean-tree check close it |
| I2 | met | proposal, design, tasks, UI delta and metadata; strict OpenSpec validation exits 0 |
| I3 | met | `make gate` exits 0; source code and living specs are unchanged by the cut |
| I4 | met | `tasks.md` has Progress rows, matching phase headings, numbered subtasks and a Verify for each |
| I5 | met | checks use available `uv`, `npm`, `rg` commands and named on-disk facts; planned test names match Tests |
| I6 | met | tasks name files and a chosen action, with no alternative implementation branches |
| I7 | met | stopped-slot equality, JobSlot, clock formatting, affected views and browser fixtures are named in tasks |
| I8 | met | prose -> layout -> progress -> shutdown; each phase contains its own related implementation/tests |
| I9 | met | delta modifies existing UI requirement titles, preserves existing keys and covers changed behaviour |
| I10 | met | evidence rechecked at HEAD; planned additions are explicitly labelled; source references use AGENTS.md |
| I11 | met | Dependencies is None; stdlib and installed Vue/uvicorn/test tools suffice |
| I12 | met | no build ritual, release, archive, tag, review, convergence or commit tasks |
| I13 | met | proposal version is `v0.40.1` |
| I14 | not applicable | no human-operated or metered phase |
| I15 | met | task 1.1 is a HALT CHECK for the server seam |
| I16 | not applicable | Tests states no deletion, rename or merge; retained assertions and keys are named |

The checks for the reused browser tests already have runnable node ids; their existing assertions pass before the build.
Their new gap, totals, ticking-time and reload assertions are required by the task text, so a bare rerun is not completion.
Decision links, named scope boundaries, task size and the proposal's final exclusion section were checked for P9/P12/P13/A2.

## Dependencies

None.

## Risks / Trade-offs

- Signal timing can race a subscription -> durable close state plus subprocess tests wait for stream snapshots.
- A stale completion can inflate totals -> accepted identities, a completed set and copied snapshots under the job lock.
- Browser progress can finish before observation -> the fixture reader's release file and deadline make the observation controlled.
- A failed close can leave billing active -> preserve its terminal recovery command; no provider call is introduced by this patch.
- Equal-total confirmation can change composition -> [D2](#d2) makes the accepted boundary explicit rather than claiming identity checks.

## Verdict

**Feasible.** Existing requirements and the designed JobStrip cover the repairs; the delta adds scenarios beneath those requirements.
No format, output, dependency or external service changes are needed; each build phase can leave the gate green independently.
