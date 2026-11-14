---
bump: patch
version: 0.86.17
---

# One vitest file

`tools.test_ui` runs one browser test file from the repository root, and a root config refuses every other way to start vitest.

Reading map: [design](design.md) holds the decisions, the guard's text and the tests, [tasks](tasks.md) holds the phases: the arguments, the guard, the documents.

## Why

A worker has no `cd`, so each invents a command for one vitest file. The commonest, `npm --prefix ui exec -- vitest run <file>`, starts vitest at the repository's root. That writes a root `node_modules/` and skips `ui/`'s config, and the next station finds a dirty tree.

`tools.test_ui` takes no arguments today, and no document names a command for one file.

## What Changes

- `tools.test_ui` passes its arguments to `npm run test --` in `ui/`. A leading `ui/` on an argument is dropped. With no argument it runs as it does today.
- A root `vitest.config.mjs` only refuses, naming that command. A test starts vitest beside a copy of it, outside the tree.
- `CONTRIBUTING.md` holds the rule, and `AGENTS.md`'s gate line names the command.

No requirement changes: the change is `skip_specs`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- `tools/npm_ui.py`, `tools/test_ui.py`, `tests/test_test_ui.py`.
- A new file at the root, `vitest.config.mjs`. The image's recipe copies named files alone, so no image changes.
- `CONTRIBUTING.md`, `AGENTS.md`.
- `ui/` is run, never edited: the checks run vitest there.

## Not in this change

- `tools.typecheck_ui` stays whole: `vue-tsc` given a file ignores the project's config, so a one-file check would not be the gate's ([D3](design.md#d3)).
- The gate's `Makefile` lines: the gate still runs the whole suite.
- The replay's own vitest run in `tools/mutate.py`: it already drops a leading `ui/` and runs in the copy's `ui/`.
