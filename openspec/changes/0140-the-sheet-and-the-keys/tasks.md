# The sheet and the keys — tasks

Phases that teach the replay vitest, hold the sheet's saves, the key dispatch and the chooser's decision, fix the one stale cancel, and pin them with mutants.

## Progress

- [x] 1 — The replay learns vitest · moderate
- [x] 2 — The sheet's saves · moderate
- [x] 3 — Key dispatch and the chooser · moderate
- [ ] 4 — Cancel approve after a read · hard
- [ ] 5 — The mutants die · moderate

## 1 — The replay learns vitest

- [x] 1.1 **HALT CHECK** `0135-the-paydown` is merged: the replay mode this phase extends exists; if it does not, the plan is wrong.
  Verify: `git grep -c -h -F 'def run_edits' tools/mutate.py` prints `1`.
- [x] 1.2 In `tools/mutate.py` add `RUNNERS = ("pytest", "vitest")` after `LINKED`, `"runner"` to `EDIT_OPTIONAL` and `EDIT_TEXTS`, and `runner: str` to `Edit` after `tests`. In `load_edit` read `runner = entry.get("runner", "pytest")`, refuse `f"{label}: runner is not pytest or vitest"` when it is not in `RUNNERS`, and pass it to `Edit` ([D1](design.md#d1)).
  Verify: `git grep -c -h -F 'RUNNERS = ("pytest", "vitest")' tools/mutate.py` prints `1`.
- [x] 1.3 In `tools/mutate.py` add `def runner_args(runner: str, tests: Sequence[str]) -> list[str]`, `pytest_args(tests, False)` for `pytest` and, for `vitest`, each test with its leading `ui/` removed, as vitest matches a filter against the path from its root. Give `run_tests` the keyword `runner: str = "pytest"`: for `vitest` it runs `["npm", "run", "test", "--", *args]` with `cwd=copy / "ui"`, else as now ([D2](design.md#d2)).
  Verify: `git grep -c -h -F 'def runner_args' tools/mutate.py` prints `1`.
- [x] 1.4 In `tools/mutate.py` give `try_bytes` and `baseline_limit` the keyword `runner: str = "pytest"` and pass it to `run_tests`; `try_edit` passes `edit.runner`. Update the module docstring's usage lines with `"runner": "vitest"`.
  Verify: `git grep -n -F 'edit.runner' tools/mutate.py` prints a line.
- [x] 1.5 In `tools/mutate.py` add `@contextmanager def linked_modules(copy: Path, root: Path) -> Iterator[None]`, importing `contextmanager` from `contextlib`: it makes `copy / "ui" / "node_modules"` a link to `root / "ui" / "node_modules"`, yields, and removes the link in `finally`.
  Verify: `git grep -c -h -F 'def linked_modules' tools/mutate.py` prints `1`.
- [x] 1.6 In `run_edits`, before the copy is made and when an entry's runner is `vitest`, raise `Refused("a vitest entry needs ui/node_modules: run npm ci --prefix ui")` when `root / "ui" / "node_modules"` is no directory, and `Refused("a vitest entry needs npm on PATH")` when `shutil.which("npm")` is `None`.
  Verify: `git grep -c -h -F 'a vitest entry needs ui/node_modules' tools/mutate.py` prints `1`.
- [x] 1.7 In `run_edits` key `limits` by `(e.runner, e.tests)` and compute each with `runner_args(e.runner, e.tests)`; replace `args = pytest_args(edit.tests, False)` and `limits[edit.tests]` in its loop with `args = runner_args(edit.runner, edit.tests)` and `limits[(edit.runner, edit.tests)]`; hold `with linked_modules(copy, root):` around the baseline of each vitest list and around each vitest edit's `try_edit`, never around a pytest one.
  Verify: `git grep -n -F 'with linked_modules(' tools/mutate.py` prints a line.
- [x] 1.8 In `tests/test_mutate.py` add `def fake_npm(bin_dir: Path) -> None`, writing an executable `npm` of `#!/bin/sh`, `case "$*" in *" ui/"*) exit 3;; esac` and `test -d node_modules && grep -q "limit = 10" limit.txt`, so an argument still named from the repository's root fails it; and `def build_vitest_repo(path: Path) -> Path`, `build_notes_repo(path)` plus a tracked `ui/limit.txt` of `limit = 10` and `remark: none`, an untracked `ui/node_modules/`, and `tests/test_unlinked.py`, a test asserting `ui/node_modules` is absent from its repository root.
  Verify: `git grep -c -h -F 'def build_vitest_repo' tests/test_mutate.py` prints `1`.
- [x] 1.9 In `tests/test_mutate.py` add `test_a_vitest_entry_replays_with_the_modules_linked_for_it_alone`, marked `spec_exempt("structural: a vitest entry is replayed with ui/node_modules linked for it alone")`, with `PATH` set to `fake_npm`'s directory before the rest. Entries: `ED-1` vitest over `ui/limit.txt`, `limit = 10` to `limit = 11`, its tests `ui/src/limit.test.ts`; `ED-2` vitest, `remark: none` to `remark: some`, the same tests; `ED-3` pytest over `notes.txt`, `limit = 10` to `limit = 11`, its tests `tests/test_unlinked.py`. Assert status `1`, `ED-1` killed, `ED-2` and `ED-3` survived, and the repository's files unchanged.
  Verify: `uv run pytest tests/test_mutate.py::test_a_vitest_entry_replays_with_the_modules_linked_for_it_alone` passes.
- [x] 1.10 In `tests/test_mutate.py` add `test_a_vitest_entry_with_no_modules_or_no_npm_is_refused`, marked `spec_exempt("structural: a vitest entry that cannot run is refused before any line prints")`, parametrized over `modules` (a repository with no `ui/node_modules`, `fake_npm` on `PATH`) and `npm` (`PATH` a directory holding a link to `git` alone). Assert status `2`, no printed line, and `ui/node_modules` or `npm` in the refusal.
  Verify: `uv run pytest tests/test_mutate.py::test_a_vitest_entry_with_no_modules_or_no_npm_is_refused` passes.
- [x] 1.11 In `tests/test_mutate.py` add the row `({"runner": "jest"}, (), "ED-X")`, id `unknown runner`, to the parameters of `test_an_entry_out_of_shape_or_whose_find_is_not_once_is_refused`.
  Verify: `git grep -c -h -F 'unknown runner' tests/test_mutate.py` prints `1`.
- [x] 1.12 In `tests/test_mutate.py` import `runner_args` and add `test_a_vitest_file_is_named_from_the_ui_root`, marked `spec_exempt("structural: vitest takes its files from the root of ui/")`: `runner_args("vitest", ["ui/src/a.test.ts"])` is `["src/a.test.ts"]`, and `runner_args("pytest", ["tests/test_a.py"])` is `pytest_args(["tests/test_a.py"], False)`.
  Verify: `uv run pytest tests/test_mutate.py::test_a_vitest_file_is_named_from_the_ui_root` passes.
- [x] 1.13 In `CONTRIBUTING.md`, after the sentence that says a mutant of a finding a version closed lives in `tests/mutants.json`, add: `A vitest mutant names "runner": "vitest" and the files of ui/src that kill it; the copy links ui/node_modules for it alone.`
  Verify: `git grep -c -h -F '"runner": "vitest"' CONTRIBUTING.md` prints `1`.
- [x] 1.14 The phase's file agrees with the runner.
  Verify: `uv run pytest tests/test_mutate.py` passes.

## 2 — The sheet's saves

- [x] 2.1 **HALT CHECK** The save that fails restores its edit as [D3](design.md#d3) reads it; if the line reads otherwise, the plan is wrong.
  Verify: `git grep -c -h -F 'if (current === id && !superseded(id, mine)) dirty = true' ui/src/composables/useSheet.ts` prints `1`.
- [x] 2.2 In `ui/src/composables/useSheet.test.ts` add `spec('ui:save:a-lone-failed-save-is-sent-again', …)`: open `a` at `saved` 10, `commit('hair', 'brown hair', null)`, `const first = sheet.flush()`, `await refuse('/api/c/b/review/a/f/draft', 'a draft is not at that save')`, and assert `await first` is `false`. Then `const again = sheet.flush()`: one call, a PUT whose body has `fields.hair` `['long hair', 'brown hair']` and `saved` `10`; answer it with `receipt(11)` and assert `await again` is `true`.
  Verify: `git grep -c -h -F "a-lone-failed-save-is-sent-again" ui/src/composables/useSheet.test.ts` prints `1`.
- [x] 2.3 In `ui/src/composables/useSheet.test.ts` add `spec('ui:review:a-refused-save-is-shown', …)`: open `a`, commit, flush and refuse as 2.2 does, and assert `sheet.refusal.value` is `'a draft is not at that save'`. Commit `'short hair'`, flush, answer `receipt(11)`, and assert `sheet.refusal.value` is `null`.
  Verify: `git grep -c -h -F "a-refused-save-is-shown" ui/src/composables/useSheet.test.ts` prints `1`.
- [x] 2.4 In `ui/src/composables/useSheet.test.ts` add `spec('ui:review:a-sheet-that-cannot-be-read-says-so', …)`: `const opened = sheet.open('a')`, `await refuse('/api/c/b/review/a/f', 'the sheet is damaged')`, `await opened`; assert `sheet.refusal.value` is `'the sheet is damaged'`, `sheet.loading.value` is `false` and `sheet.detail.value` is `null`.
  Verify: `git grep -c -h -F "a-sheet-that-cannot-be-read-says-so" ui/src/composables/useSheet.test.ts` prints `1`.
- [x] 2.5 In `ui/src/composables/useSheet.test.ts` add `spec('ui:save:a-burst-of-edits-is-one-save', …)`: open `a`; `commit('hair', 'brown hair', null)`, `advanceTimersByTimeAsync(100)`, `commit('hair', 'short hair', null)`, `advanceTimersByTimeAsync(100)`, `commit('hair', 'curly hair', null)`, `advanceTimersByTimeAsync(399)`; assert `calls` is empty. Advance `1`: one PUT whose `fields.hair` is `['long hair', 'brown hair', 'short hair', 'curly hair']`.
  Verify: `git grep -c -h -F "a-burst-of-edits-is-one-save" ui/src/composables/useSheet.test.ts` prints `1`.
- [x] 2.6 The phase's file agrees with the keys.
  Verify: `uv run python -m tools.test_ui` exits `0`.
- [x] 2.7 Each key a test names is one the living spec or this change's delta holds.
  Verify: `uv run pytest tests/test_spec_bindings.py` passes.

## 3 — Key dispatch and the chooser

- [x] 3.1 **HALT CHECK** `isField` reads a textarea by its tag, so the case below is one the store already answers; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -h -F "if (element.tagName === 'TEXTAREA') return true" ui/src/stores/keys.ts` prints `1`.
- [x] 3.2 In `ui/src/stores/keys.test.ts` add `spec('ui:keys:a-screen-takes-the-keys-before-everywhere', …)` after the overlay's: `screen = command('revise', 'KeyE')` declared in `'screen'`, `everywhere = command('library', 'KeyE')` declared in `'everywhere'`; `keys.press(press('KeyE'))`; assert `screen.run` was called once and `everywhere.run` not.
  Verify: `git grep -c -h -F "a-screen-takes-the-keys-before-everywhere" ui/src/stores/keys.test.ts` prints `1`.
- [x] 3.3 In `ui/src/stores/keys.test.ts` give `field` the parameter `kind: Record<string, unknown> = {}`, spread into the double after `type: 'text'`, so a caller sets its `tagName` and its `isContentEditable`.
  Verify: `git grep -c -h -F "kind: Record<string, unknown> = {}" ui/src/stores/keys.test.ts` prints `1`.
- [x] 3.4 In `ui/src/stores/keys.test.ts` extend `ui:keys:no-command-fires-in-a-text-field` in place: after its last assert, add `const textarea = field({ tagName: 'TEXTAREA' })` and `const editable = field({ tagName: 'DIV', isContentEditable: true })`. For each assert `keys.press(press('KeyE', { target }))` is `false`, `letter.run` is still not called, and `keys.press(press('Escape', { target }))` leaves `target.left` `true`.
  Verify: `git grep -c -h -F "const editable = field(" ui/src/stores/keys.test.ts` prints `1`.
- [x] 3.5 In `ui/src/composables/useQueue.test.ts` import `chooses` from `./useQueue`. In `ui:review:two-flows-waiting-open-the-chooser` assert `chooses(info)` is `true` after its `flowsWaiting` assert; in `ui:review:a-batch-opens-its-head` assert `chooses(collection('draft'))` is `false` after its `flowsWaiting` assert.
  Verify: `git grep -c -h -F "chooses(" ui/src/composables/useQueue.test.ts` prints `2`.
- [x] 3.6 The phase's files agree with the keys.
  Verify: `uv run python -m tools.test_ui` exits `0`.

## 4 — Cancel approve after a read

- [ ] 4.1 **HALT CHECK** The watch drops a render's move while the sheet is being read, as card `0124·S2` says; if it reads otherwise, the plan is wrong.
  Verify: `git grep -c -h -F "if (readsAgain(before, after, props.collection, approved)) void reread(current.value)" ui/src/views/Review.vue` prints `1`.
- [ ] 4.2 In `ui/src/cancel.ts` write `Reading`, `Again`, `readsAgain`, `Held`, `Sheet` and `rereads` exactly as [D5](design.md#d5) gives them, keeping `holdsCancel` and the comment above `readsAgain` true to what it now answers.
  Verify: `git grep -c -h -F "export function rereads(" ui/src/cancel.ts` prints `1`.
- [ ] 4.3 In `ui/src/views/Review.vue` import `rereads` in place of `readsAgain`, and replace the watch on `live.jobs.render`, and the comment above it, with the block of [D5](design.md#d5), `follow` and its watches, character for character.
  Verify: `git grep -c -h -F "follow.landed()" ui/src/views/Review.vue` prints `1`.
- [ ] 4.4 In `ui/src/cancel.test.ts` add the helper `sheet(given: Partial<Reading> = {}): Reading` returning `{ loading: false, readonly: true, detail: {}, ...given }`. Rewrite each `readsAgain(…, true)` of `ui:review:the-cancel-follows-the-render` as `readsAgain(…, sheet())`, `toBe('now')` where it was `true` and `toBe('no')` where it was `false`, and each `…, false)` as `sheet({ readonly: false })`, `toBe('no')`.
  Verify: `git grep -c -h -F "sheet({ readonly: false })" ui/src/cancel.test.ts` prints `2`.
- [ ] 4.5 In that case add rows: `sheet({ loading: true })` answers `'later'` for `idle` to `running` and `running` to `done` over `'a'` and `'no'` for a move that is not one; `sheet({ detail: null })` answers `'no'` for `idle` to `running`.
  Verify: `git grep -n -F "'later'" ui/src/cancel.test.ts` prints a line.
- [ ] 4.6 In `ui/src/cancel.test.ts` add `spec('ui:review:a-render-that-moves-during-the-read-is-read-again', …)` over `rereads(() => 'a', held, reread)`, `held` an object of `loading`, `readonly` and `detail` each `{ value }` the case sets, and `reread = vi.fn()`. Cases: a move into running while loading, then `landed()` of an approved sheet, reads once, and a second `landed()` still once; a move while loading, then `landed()` of a sheet that is not readonly, reads never; `landed()` while still loading, the sheet `readonly` with a `detail`, reads never and keeps the memory, the next `landed()` of the approved sheet reads once; a move of an approved sheet that is not loading reads at once.
  Verify: `git grep -c -h -F "a-render-that-moves-during-the-read-is-read-again" ui/src/cancel.test.ts` prints `1`.
- [ ] 4.7 The phase's files agree with the keys and the types.
  Verify: `uv run python -m tools.test_ui` exits `0`.
- [ ] 4.8 `Review.vue` and `cancel.ts` type-check under the gate's browser typecheck.
  Verify: `uv run python -m tools.typecheck_ui` exits `0`.
- [ ] 4.9 `ui/src/views/Review.vue` ends no longer than it began, so its listed ceiling in `tests/test_ratchets.py` stands; the ceiling is never raised.
  Verify: `uv run pytest tests/test_ratchets.py` passes.

## 5 — The mutants die

- [ ] 5.1 **HALT CHECK** `0135-the-paydown` is merged: the replay file exists and holds its entries; if it does not, this phase has nothing to run.
  Verify: `git grep -c -h -F '"finding": "PB-14"' tests/mutants.json` prints `1`.
- [ ] 5.2 **HALT CHECK** `0137-the-server` is merged: `ui/src/api.test.ts` exists for the mutants of `ui/src/api.ts`; if it does not, the plan is wrong.
  Verify: `git grep -c -h -F "from './test/wire.json'" -- ui/src` prints `1`.
- [ ] 5.3 Append each entry of [mutants.json](mutants.json) to `tests/mutants.json`, keys and order unchanged, indented as the file is; each `find` of `ui/src/cancel.ts` is character for character the line phase 4 wrote. The last entry opens with `"finding": "VT-18c"`.
  Verify: `git grep -c -h -F '"finding": "VT-18c"' tests/mutants.json` prints `1`.
- [ ] 5.4 Run the replay. A line that names a survivor goes to 5.5.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.
- [ ] 5.5 For each `survivor` line 5.4 printed, add in the file its entry names a test red with the mutant in place and green without it; only where no input tells the mutant from the line, give the entry `equivalent` with the reason, proven by reading the line. Never delete an entry. Where 5.4 printed none, this task holds.
  Verify: `uv run python -m tools.mutate --edits tests/mutants.json` exits `0`.
