# The paydown — design

The decisions that pay the debt cards no open version claims, each under a requirement already in force. Verdict: feasible-with-caveats, ready to build, in the phases of [tasks](tasks.md).

## Context

`0119` and `0120` take the other cards. The cards left are fixes to code `0111`, `0072`, `0070` and `0118` shipped; each sits under a living requirement, so this is a patch ([CONTRIBUTING](../../../CONTRIBUTING.md): a scenario may be added under a requirement, a requirement may not).

```
phase  card              where                                   proof
1      0111·R1           review.py  _copy_approval               pytest, tests/test_review.py
2      0111·R2           decisions.md, review spec, README       git grep
3      op·chained-source render.py  in_session_sources           pytest, tests/test_render.py
4      0072·R5           Review.vue, cancel.ts                   vitest
5      0070·R20          useSheet.ts                             vitest
6      0118·S1           app.css, tests/e2e                      browser, outside the gate
```

## Goals / Non-Goals

Goals: each card closed by code or prose, each fix bound to a scenario under its requirement, the gate green at every phase.

Non-goals: the cards `0119` and `0120` pay; a check of a copy's fields against its source's latest approval; a new decision id; `DraftDialog`'s several-image path.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A copy is in step when the target holds the copy's seeds, listed or rendered | the target's group is the only place its rendered seeds are | comparing listed seeds only: the target's seeds are in its group after a render |
| [D2](#d2) | The copy's prose says what a `T=S` render takes; no check | `0111` removed the check on purpose | a free check of the copy's fields against the source's latest approval |
| [D3](#d3) | `in_session_sources` refuses a chained source before the pod | a plan short of the work breaks the limit's estimate | planning the chain's sum |
| [D4](#d4) | Review reads an approved sheet again when `jobs.render` moves for its collection | the server's reason follows the render slot | a poll; reading the sheet on every job event |
| [D5](#d5) | A save finding a queued, unsent save of its input replaces that save's payload | the queued save carries the whole draft | queueing every pause; dropping the older edit |
| [D6](#d6) | `.pick--cell .pick__tiles` does not shrink, and a browser test measures it | the rows are scrollers in a capped column | changing `.pick__tiles`, which `ComparePick` shares |
| [D7](#d7) | A scenario binds each new test; the requirement's sentence changes only for D1 | vitest and e2e tests carry a key, and a patch adds no requirement | a `spec_exempt` on a behaviour |

### D1

`_copy_approval` in [review.py](../../../isekai/pipeline/review.py) compares the target's newest approval through `copied_renders`, as it lists the source's, not through `renders_of`. In step means: the newest approval is a copy, its fields equal, its count equal, and its seeds equal as sets.

```
before   renders_of(mine, newest, afresh) == renders
after    held = copied_renders(run, flow, approved_versions(directory)[-1], newest)
         held["count"] == renders["count"] and set(held["seeds"]) == set(renders["seeds"])
```

A target that has not rendered the seeds is not in step, so it is copied again and its renders list them. `review.py` lists the group itself, as `copied_renders` does, so no import of `generate` is needed ([test_layers](../../../tests/test_layers.py) holds that). The docstring says "listed or rendered".

### D2

D49's *Why*, D38's note, the review spec's rationale and the README's `--seeds-from` line say one thing: the copy lists the source's seeds, a render naming the source reads the source's latest seeds when it runs, and the copy's fields follow the source's only when `approve --from` is run again. `0111` D5 removed `refuse_out_of_step` on purpose, so nothing checks; the prose stops saying nothing needs to. The review spec's rationale is the delta's, and folds into the living spec at release.

### D3

`in_session_sources` in [render.py](../../../isekai/interface/render.py) collects the source requests of the line, those that are not by count. A source request whose source is another source request's flow is refused, in either order, with this message:

```
template   '<T>' takes its seeds from '<S>', itself a source request; write '<T's flow>=<S's source>' for the same seeds
the test   refused: 'summon-flat-anime-wai=control-anime-wai' takes its seeds from 'control-anime-wai=summon-anime-wai',
           itself a source request; write 'summon-flat-anime-wai=summon-anime-wai' for the same seeds
```

The message is the template alone, with no `e.g.` after it; the test line is what the test expects in the log, on one line.

The refusal runs from `_session` before `seams.open_session`, so no pod opens. `_requested`'s docstring says what it plans: a by-count request's count, the count of a by-count source in the line, else the images its source holds now. A source of a source never reaches it.

### D4

A pure function decides, in a new [cancel.ts](../../../ui/src/cancel.ts): `holdsCancel(slot, collection)` is true while the slot runs for the collection, as `_rendering` in `app.py` says, and `readsAgain(before, after, collection, approved)` is `approved` and `holdsCancel(before) !== holdsCancel(after)`. `Review.vue` watches `live.jobs.render` and calls `reread(current.value)` when it answers true. `approved` is `sheet.readonly.value && sheet.detail.value !== null`, the state in which the approve bar draws the button.

A re-read resets edits and undo, which an approved sheet does not hold. `App.vue` already follows the route's collection, so the stream is open on Review. `renderRunning` is not used because it counts disk sessions the server's reason does not.

### D5

Each `inFlight` entry in [useSheet.ts](../../../ui/src/composables/useSheet.ts) gains `queued`, a holder `{ unsent }`. `unsent` is the draft `{ payload, asking, asked }` from `send()` until `write()` passes its wait, then null. `write()` reads its draft from `queued` after the wait.

```
send():  draft = { payload, asking, asked: generation += 1 }
         last = newest save of this input in inFlight
         last?.queued.unsent set  -> last.queued.unsent = draft; return        (replaced, no new write)
         else                      -> as now, with queued = { unsent: draft }
write(): after its wait, draft = queued.unsent; queued.unsent = null; saveDraft(draft)
catch:   dirty = true only if no save of this input started after this one
```

`waiting` counts each queued save once, so `leave()` answers as before.

### D6

[app.css](../../../ui/src/app.css) gains `.pick--cell .pick__tiles { flex-shrink: 0; }` beside `.pick--cell .tile`, so a cell modal's rows keep their natural height and `.pick` scrolls. `ComparePick`'s rows are in `.pick__row`, which the selector does not reach. The card's verdict is *plausible* until a browser measures it; the test is outside the gate.

The browser test opens the cell of ten renders, a new collection `tenfold`, in a 1280×768 window:

```
1  goto the collection's hub; click the cell's thumbnail         the cell modal opens
2  the rows: .pick--cell .pick__tiles                            four rows
3  each row: scrollHeight <= clientHeight                        no row scrolls on its own
4  .pick--cell: scrollHeight > clientHeight                      the grid scrolls
5  scroll the fourth row into view                               .pick--cell scrollTop > 0
```

### D7

A new vitest test binds through `spec("<key>", …)`, and a new browser test through `@pytest.mark.spec`; neither may be exempt, since each proves a behaviour. The `ui` scenarios and the `cli` scenario are added under their requirements, and D1 also rewords the review requirement's sentence, as the brief's Q2 settled. The other requirements' SHALL paragraphs are unchanged.

## Tests

The change deletes and merges no test, so no row of the removed-test table is owed. Each new test sits at the lowest layer that can fail for its behaviour (T1); the e2e test is the one only a browser shows.

| layer | tests added, in | removed | counted by |
|---|---|---|---|
| python unit | a copy in step after both rendered, parametrized over a target that rendered and one that did not, in `tests/test_review.py`; a chained source refused, in `tests/test_render.py` | none | `git grep -n -E "a-copy-is-in-step-once-both-have-rendered|a-chained-source-is-refused-before-the-pod" -- tests` prints two lines |
| vitest | the cancel rule, in `ui/src/cancel.test.ts`; several pauses in one slow save and a failed save with one queued, in `ui/src/composables/useSheet.test.ts` | none | `git grep -n -E "the-cancel-follows-the-render|edits-inside-a-slow-save-are-sent-as-one-request|a-failed-save-leaves-nothing-to-send-again" -- ui/src` prints three lines |
| end-to-end | a cell of ten renders, on Chromium, in `tests/e2e/test_render.py` over a collection `tenfold` made in `tests/e2e/conftest.py` | none | `git grep -n "a-cell-of-ten-renders-scrolls-its-grid" -- tests/e2e` prints one line |

The end-to-end test runs on Chromium alone: layout is the same question on every engine here. No existing browser test reaches a cell of ten renders, whose fixture adds a collection, so the phase's commit body says why none fits (T2). The wiring in `Review.vue` has no DOM test, as vitest runs in node; the rule it follows is the pure function under test, and the watch is read.

## Dependencies

None.

## Risks / Trade-offs

- A new fixture collection joins the e2e library. A test listing the library's collections could change; the build runs `make e2e` where Chromium starts, and CI holds it.
- D4's watch is read, not run, by the gate. A wrong `approved` would re-read a draft and reset its edits; the pure function takes `approved` so its test holds the rule.
- D5 touches the save path every edit takes. The existing save tests hold its ordering, and the new ones hold the replacement and the failure.
- `0119` and `0120` share files with this change in other lines. The version that releases second takes a catch-up merge.

## Verdict

Feasible-with-caveats. Each phase is a small change under a living requirement; the caveats are the browser test, which the gate does not run, and the Review wiring, which is read.
