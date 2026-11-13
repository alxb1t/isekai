# The sheet and the keys — design

The page's sheet saves, key dispatch and chooser decision are held by tests that read the wrong evidence, and one product line drops a render's move during a read. This change lets the replay run vitest, holds each line, fixes the one, and pins them with mutants. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The audit ran each vitest test against mutants of the page's source, read at the cut, at `d3f72349`. `0135-the-paydown` adds the replay mode `--edits`, `tests/mutants.json` and `make mutants`, which run pytest alone. `0137-the-server` adds `ui/src/api.test.ts` and leaves its mutants of `ui/src/api.ts` to this change. Phase 5 uses the replay, the file and that test.

| gap | where it lives at the cut |
|---|---|
| the replay runs pytest alone | `tools/mutate.py` `run_tests`, `run_edits`; `tests/test_mutate.py` |
| a lone failed save is never sent again; a refused save and a failed read show nothing; the debounce is held from above | `ui/src/composables/useSheet.ts` `write`, `open`, `DEBOUNCE`; `ui/src/composables/useSheet.test.ts` |
| a screen's command could lose a shared key to the keys offered everywhere; a textarea or an editable element is no text field | `ui/src/stores/keys.ts` `reached`, `isField`; `ui/src/stores/keys.test.ts` |
| whether Review is the chooser is decided by `chooses`, which no test calls | `ui/src/composables/useQueue.ts` `chooses`; `ui/src/composables/useQueue.test.ts` |
| a render that moves while the sheet is being read is dropped | `ui/src/views/Review.vue` the watch on `live.jobs.render`; `ui/src/cancel.ts` `readsAgain`; card `0124·S2` |

```
 tools/mutate.py ── runner: pytest | vitest ─▶ npm run test -- <files>, in the copy's ui/   (phase 1)
 useSheet.test.ts ── lone save · refusal · failed read · burst                               (phase 2)
 keys.test.ts · useQueue.test.ts ── screen first · textarea · editable · chooses             (phase 3)
 cancel.ts ◀── Review.vue    rereads(): moved · landed                                        (phase 4)
 tests/mutants.json ◀── mutants.json                                                          (phase 5)
```

## Goals / Non-Goals

**Goals**
- A vitest mutant is replayed like a pytest one: its entry names the runner and the test files, and a survivor exits 1.
- A save refused with nothing behind it is sent again by the next flush, a refusal and a failed read are shown, and a burst of typing is one save.
- A screen's command runs before the same key offered everywhere, and a textarea and an editable element take the keys as a text field does.
- A render that moves during a read leaves *Cancel approve* true once the read lands, and a sheet that is not approved is never read again for it.
- Each finding's mutant dies, and stays dead: `tests/mutants.json` holds it.

**Non-Goals**
- A browser test. The page in a browser is the next version's, proven by CI after the merge.
- A requirement, a format version, a flag, a verb, or a decision in force. `docs/decisions.md` is not edited.
- The sheet's undo, redo, remove and ④, and `⌥`: the spec audit takes them.
- The edit a failed save drops after the person switched sheet: the refactor's page version fixes it.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | An entry of the replay may name `"runner": "vitest"`, its `tests` files under `ui/src/`; the default is `pytest` | the audit's mutants name a runner already; one file, one replay | a second file for vitest; a second command |
| [D2](#d2) | A vitest entry runs `npm run test -- <files>` in the copy's `ui/`, its files named from `ui/`'s root, and the copy links `ui/node_modules` for those entries alone | the link is for vitest alone, so a pytest entry never reaches the checkout's modules, and a copy holds no more of the checkout than a run needs | linking it for every entry; `npx vitest` |
| [D3](#d3) | Each case is held at the lowest layer that fails for its mutant: the composable or store in node | a browser test costs a CI round trip and hides the line | a browser test for each |
| [D4](#d4) | Scenarios are added under the requirements that name each behaviour; tests with no scenario of their own carry an existing key | a patch adds a scenario under a requirement, never a requirement | `skip_specs`; a MODIFIED SHALL |
| [D5](#d5) | The fix is `rereads` in `ui/src/cancel.ts`: it remembers a render's move met during a read and reads once the read lands, an approved sheet alone | the memory is then held by vitest, which mounts no component | a flag in `Review.vue`, held by nothing |
| [D6](#d6) | Phase 5 adds this change's mutants to `tests/mutants.json`, with those of `api.ts` that `0137-the-server` leaves | the replay is where a mutant that must stay dead lives | the change directory alone |

### D1

The entry's keys are `finding`, `path`, `find`, `replace` and `tests`, with `why`, `equivalent` and now `runner`. A `runner` that is neither `pytest` nor `vitest` is refused naming the finding. The audit's `expect` key is not an entry key: the cut dropped it.

```json
{"finding": "VT-16", "runner": "vitest", "path": "ui/src/composables/useSheet.ts",
 "find": "const DEBOUNCE = 400", "replace": "const DEBOUNCE = 0",
 "tests": ["ui/src/composables/useSheet.test.ts"], "why": "…"}
```

### D2

`run_tests(copy, args, timeout, runner="pytest")` runs `[sys.executable, "-m", "pytest", *args]` in `copy` for pytest, and `["npm", "run", "test", "--", *args]` in `copy / "ui"` for vitest, `args` the test files, which vitest takes as filters of the path from its root, `ui/`. An entry names a file from the repository's root, as the audit's do, so `runner_args(runner, tests)` returns `pytest_args(tests, False)` for pytest and the files with a leading `ui/` removed for vitest: `ui/src/cancel.test.ts` is run as `src/cancel.test.ts`. The exit codes read as now: 0 survived, 1 killed, other invalid.

`linked_modules(copy, root)` is a context manager that makes `copy/ui/node_modules` a link to `root/ui/node_modules` and removes the link in `finally`. `run_edits` holds it around the baseline of each vitest list and around each vitest edit, never around a pytest one. A vitest entry with no `ui/node_modules` in `root`, or with no `npm` on `PATH`, is refused before any line prints.

A file that is not Python is not parsed, so an edit that breaks a `.ts` file is killed by vitest's own error. Each `find` of this change keeps its file valid.

### D3

The tests extend the files that hold each subject, and use `useSheet.test.ts`'s hand-released `fetch`: `answer` and `refuse` release the oldest call to a URL, under fake timers. No test is deleted. [Tests](#tests) holds no table of removals.

### D4

| requirement | scenario added | key |
|---|---|---|
| `ui` · *The page's save state is true to the requests in flight, and a pending edit is sent on leaving* | a lone failed save is sent again | `ui:save:a-lone-failed-save-is-sent-again` |
| the same | a burst of edits is one save | `ui:save:a-burst-of-edits-is-one-save` |
| `ui` · *Review opens a collection at its own address, lists every unrendered sheet, and Approve stays on the sheet* | a refused save is shown in the approve bar | `ui:review:a-refused-save-is-shown` |
| the same | a sheet that cannot be read says so | `ui:review:a-sheet-that-cannot-be-read-says-so` |
| the same | a render that moves during the read is read again once it lands | `ui:review:a-render-that-moves-during-the-read-is-read-again` |
| `ui` · *Each command has one key, declared once, and none fires while typing* | a screen takes the keys before everywhere | `ui:keys:a-screen-takes-the-keys-before-everywhere` |

Each requirement's text is the living one, unchanged: the delta restates it with its scenarios. The brief names the lone failed save's scenario and leaves the others' keys to the cut, which reads the nearest requirement that speaks of each: the debounce is the save requirement's own word, and the approve bar is where Review's requirement says a failure is shown, never dropped. The reviewer may move them.

The tests with no scenario of their own carry an existing key:

| test | key it carries | because |
|---|---|---|
| a textarea and an editable element take no command | `ui:keys:no-command-fires-in-a-text-field` | they are text fields; the case extends the test in place |
| `chooses` is true when more than one flow waits and false for a batch with a single flow | `ui:review:two-flows-waiting-open-the-chooser` and `ui:review:a-batch-opens-its-head` | the decision those scenarios state |
| the cancel's table follows the render | `ui:review:the-cancel-follows-the-render` | the table gains the sheet's reading |

### D5

`readsAgain` takes the sheet's reading in place of its `approved` flag, and answers when to read. `rereads` holds what a render's move met during a read is owed. `ui/src/cancel.ts` gains:

```ts
/** What the watcher reads of the open sheet. */
export interface Reading {
  loading: boolean
  readonly: boolean
  detail: unknown
}

/** Read the sheet again `now`, `later` once the read in flight lands, or `no`. */
export type Again = 'now' | 'later' | 'no'

export function readsAgain(
  before: JobSlot | null,
  after: JobSlot | null,
  collection: string,
  sheet: Reading,
): Again {
  if (holdsCancel(before, collection) === holdsCancel(after, collection)) return 'no'
  if (sheet.loading) return 'later'
  return sheet.readonly && sheet.detail !== null ? 'now' : 'no'
}

/** A value the page holds, as a ref or a computed one is read. */
interface Held<T> {
  readonly value: T
}

/** The sheet's own refs, which `rereads` reads each time. */
export interface Sheet {
  loading: Held<boolean>
  readonly: Held<boolean>
  detail: Held<unknown>
}

export function rereads(collection: () => string, sheet: Sheet, reread: () => void) {
  const reading = (): Reading => ({
    loading: sheet.loading.value,
    readonly: sheet.readonly.value,
    detail: sheet.detail.value,
  })
  let missed = false
  return {
    moved(before: JobSlot | null, after: JobSlot | null): void {
      const again = readsAgain(before, after, collection(), reading())
      if (again === 'later') missed = true
      if (again === 'now') reread()
    },
    landed(): void {
      const now = reading()
      if (now.loading) return
      const owed = missed && now.readonly && now.detail !== null
      missed = false
      if (owed) reread()
    },
  }
}
```

`holdsCancel` is unchanged. `Review.vue` replaces its watch, and the comment above it, with the lines below. `ui/src/views/Review.vue` is listed in `tests/test_ratchets.py` at its ceiling, so it must end no longer than it is: the block is shorter than the one it replaces.

```ts
/* The server's reason for Cancel approve follows the render slot, so an approved sheet is
   read again when a render for its collection starts or ends, or once the read in flight lands. */
const follow = rereads(() => props.collection, sheet, () => void reread(current.value))
watch(() => live.jobs.render, (after, before) => follow.moved(before, after))
watch(() => sheet.loading.value, () => follow.landed())
```

```
 render moves ─▶ sheet loading? ─ yes ─▶ remember ─▶ read lands ─▶ approved? ─ yes ─▶ read once more
                      │ no                                              └ no ─▶ forget
                      └─▶ approved? ─ yes ─▶ read now
                                     └ no ─▶ nothing
```

A re-read sets `loading` again, so a move met during it is remembered too, and `landed` spends the memory once. The server still checks a cancel before it writes: a stale button costs a refusal, never a wrong cancel.

### D6

The change's mutants are in [mutants.json](mutants.json), each `tests` a list of files, each with `"runner": "vitest"`. Phase 5 appends them to `tests/mutants.json` and replays the file.

The audit's `VT-8` mutant names the watcher's `approved` argument, which the fix removes: its entries `VT-8a` to `VT-8f` are written for the fixed lines of D5. `VT-15`'s undo mutant and `VT-17`'s `⌥` mutant are not here, as their behaviour is the spec audit's. `VT-15b` and `VT-17c` are the cut's own, for the read failure and the editable element.

## Tests

Every case is a unit test: no browser, no end-to-end test is added, and none runs on an engine. The tests each file holds at the cut, by `git grep -c -E '^spec\(' -- <file>` for vitest and `git grep -c -E '^def test_' -- tests/test_mutate.py` for pytest, and what it gains:

| file | tests at the cut | gains | phase |
|---|---|---|---|
| `tests/test_mutate.py` | 26 | a vitest replay with the modules linked for it alone and its files named from `ui/`'s root, a refusal with no modules or no `npm`; the vitest file named from `ui/`'s root; a case in the refused-entry table | 1 |
| `tests/test_unlinked.py` | none: the test of `tests/test_mutate.py` writes it into its own repository | a test that `ui/node_modules` is absent, run by a pytest entry of that repository | 1 |
| `ui/src/composables/useSheet.test.ts` | 6 | a lone failed save, a refused save, a failed read, a burst | 2 |
| `ui/src/stores/keys.test.ts` | 12 | a screen before everywhere; the text-field case extended | 3 |
| `ui/src/composables/useQueue.test.ts` | 5 | `chooses` asserted in the chooser's case and the head's | 3 |
| `ui/src/cancel.test.ts` | 1 | the table over the sheet's reading, and `rereads` in a case of its own | 4 |
| `tests/test_ratchets.py` | unchanged | `ui/src/views/Review.vue` stays within its listed ceiling | 4 |

The vitest of these files runs in `make gate` through `tools.test_ui`: each case costs milliseconds under fake timers. The replay costs one vitest run per mutant, and `tests/mutants.json` is not in the gate; `make mutants` replays it.

The mutants, where each lies at the cut and the files that must kill it:

| mutant | where at the cut | killed by |
|---|---|---|
| `VT-14` | `ui/src/composables/useSheet.ts:240` | `ui/src/composables/useSheet.test.ts` |
| `VT-15a` | `ui/src/composables/useSheet.ts:241` | `ui/src/composables/useSheet.test.ts` |
| `VT-15b` | `ui/src/composables/useSheet.ts:119` | `ui/src/composables/useSheet.test.ts` |
| `VT-16` | `ui/src/composables/useSheet.ts:8` | `ui/src/composables/useSheet.test.ts` |
| `VT-17a` | `ui/src/stores/keys.ts:169` | `ui/src/stores/keys.test.ts` |
| `VT-17b` | `ui/src/stores/keys.ts:87` | `ui/src/stores/keys.test.ts` |
| `VT-17c` | `ui/src/stores/keys.ts:86` | `ui/src/stores/keys.test.ts` |
| `VT-19` | `ui/src/composables/useQueue.ts:80` | `ui/src/composables/useQueue.test.ts` |
| `VT-8a` to `VT-8f` | `ui/src/cancel.ts`, the lines D5 writes | `ui/src/cancel.test.ts` |
| `VT-18a` to `VT-18c` | `ui/src/api.ts:53-66`, `:226-241`, `:448-458` | `ui/src/api.test.ts` of `0137-the-server` |

No test is deleted or merged, so no row maps one test to another. The case of `ui/src/cancel.test.ts` is rewritten in place for the new signature and keeps every row of its table.

## Dependencies

None.

## Risks / Trade-offs

- **A vitest run per mutant is slow.** Each replay starts vitest over the files its entry names; `make mutants` takes minutes and stays outside the gate.
- **`Review.vue` sits at its ceiling.** The fix replaces its watch with a shorter block, so the file shrinks; the ceiling is not raised, and a longer block is a plan problem.
- **A `find` of `cancel.ts` that the build writes differently makes the replay refuse.** Task 5.3 writes each as the line phase 4 wrote it.
- **`Review.vue`'s watches are held by review, not by a test.** vitest mounts no component; `rereads` holds the logic, and the wiring is a few lines.
- **The scenarios of D4 are placed by the cut's reading.** Each describes a behaviour the page has; none adds one.
- **Phase 5 builds on `0135-the-paydown` and `0137-the-server`.** The replay and the file, and `ui/src/api.test.ts`, must be merged: its first tasks are **HALT CHECK**s for them.

## Verdict

Ready to build. Each phase ends on a green `make gate`, and phase 5 on a replay with no survivor. The one product edit is reversible: a pure function and its watches.
