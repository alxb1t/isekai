# One vitest file — design

One command runs one vitest file from the root, and a root config makes every other start refuse. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`tools.test_ui` runs `npm run test`, which is `vitest run`, in `ui/` ([tools/test_ui.py](../../../tools/test_ui.py), [tools/npm_ui.py](../../../tools/npm_ui.py)). It takes no argument. Vitest reads the config of its own root alone, and `ui/vitest.config.ts` is in `ui/`.

```
worker at the root, no cd
  npm --prefix ui exec -- vitest run <file>     starts at the root: root node_modules/, no ui config
  uv run python -m tools.test_ui ui/src/x.test.ts   (after) starts in ui/: ui's config, ui/src/x.test.ts → src/x.test.ts
```

The replay already runs vitest in the copy's `ui/` and drops a leading `ui/` (`runner_args` in [tools/mutate.py](../../../tools/mutate.py)). The image's recipe copies named files alone ([Dockerfile](../../../Dockerfile)), so a new root file changes no image.

## Goals / Non-Goals

- Goal: one command a worker can write with no `cd`, in the directory the gate starts in.
- Goal: the commonest wrong command refuses by name and writes nothing.
- Non-goal: a one-file typecheck ([D3](#d3)); a change to the gate's `Makefile`; a requirement.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `tools.test_ui` passes its arguments to `npm run test --` in `ui/`; a leading `ui/` on an argument is dropped; with no argument the command is `npm run test` as today | one command from the root, run where the config is; `ui/src/…` is what a worker at the root types | `npm --prefix ui exec`, which starts at the root; a `cd` the worker cannot run |
| [D2](#d2) | `tools/test_ui.py` holds its own `in_ui`; `tools/mutate.py` keeps its own `removeprefix` | the gate's wrapper stays small and imports no runner | importing `runner_args` from `tools.mutate`; moving it to `tools/npm_ui.py` and editing the runner |
| [D3](#d3) | `tools.typecheck_ui` stays whole | `vue-tsc` given a file ignores the project's config, so a one-file check would not be the gate's | a file argument for the typecheck |
| [D4](#d4) | a root `vitest.config.mjs` that only throws, naming the command; a test starts vitest beside a copy of it, outside the tree, and reads the refusal and that the folder holds the copy alone | converge and fix workers invent commands whatever a document says; vitest reads its root's config alone, so a start in `ui/` or with `--root ui` never sees the guard | a hook or a wrapper script a worker may skip |
| [D5](#d5) | if no test can show the guard, the guard is dropped and the change ships without it | the brief's rule: a guard nothing shows is a claim, not a guard | keeping an unproven guard |
| [D6](#d6) | `CONTRIBUTING.md` holds the rule; `AGENTS.md`'s gate line names the command | the cut reads the first, every worker loads the second | `README.md`; a comment in the `Makefile`, a gate file |

### D1

`npm_ui.run` gains a last parameter, `args`, empty by default. Empty runs `["npm", "run", script]`. Else it runs `["npm", "run", script, "--", *args]`. `tools.typecheck_ui` calls `run` without it and does not change.

`test_ui.main` gains `args` after `root` and passes `in_ui(args)`. The `__main__` block passes `sys.argv[1:]`.

```
uv run python -m tools.test_ui ui/src/cancel.test.ts -t "a name"
  → npm run test -- src/cancel.test.ts -t "a name"      in ui/
```

### D2

`in_ui(args)` returns each argument with a leading `ui/` removed. `["ui/src/a.test.ts", "-t", "x"]` → `["src/a.test.ts", "-t", "x"]`.

### D3

`Makefile`'s typecheck line is untouched, and so is `tools/typecheck_ui.py`.

### D4

The root file `vitest.config.mjs`, word for word:

```js
// vitest reads its root's config alone. Started at the repository's root it finds this file and stops,
// where it would write a root `node_modules/` and skip `ui/`'s config.
throw new Error(
  'vitest is not started at the repository root. Run one file with `uv run python -m tools.test_ui ui/src/<name>.test.ts`.',
)
```

The test copies the file into an empty folder under `tmp_path`, runs `ui/node_modules/.bin/vitest run` there and asserts:

| what | how |
|---|---|
| the start is refused | the exit code is not 0 |
| the refusal names the command | the output holds `python -m tools.test_ui` |
| nothing was written | the folder's entries are the copy alone |

The test skips when `tools.test_ui`'s `refusal` names a missing toolchain: the gate's own vitest run refuses first, and the replay's copy links no `ui/node_modules`.

### D5

The guard's first test is a **HALT CHECK**. Vite's config loader writes a temporary file beside the config, or in the nearest `node_modules/.vite-temp`, and removes it. If the folder is not clean when the process ends, or the refusal is not printed, the plan is wrong: the guard is dropped, with its test and its words in the documents.

### D6

`CONTRIBUTING.md` gains a paragraph after the gate's, in *The evidence a change carries*:

> **One browser test file** is `uv run python -m tools.test_ui ui/src/<name>.test.ts`, from the repository root. The wrapper runs vitest in `ui/`, where its config is, and drops a leading `ui/`. Never start vitest at the root: `npm --prefix ui exec -- vitest run <file>` does, writes a root `node_modules/` and skips `ui/`'s config. The root `vitest.config.mjs` refuses it.

`AGENTS.md`'s gate line, before → after:

```
before:  **The gate is `make gate`**, run from the repository root.
after:   **The gate is `make gate`**, run from the repository root. **One browser test file is
         `uv run python -m tools.test_ui ui/src/<name>.test.ts`**, from the same place; never start vitest at the root.
```

No decision of `docs/decisions.md` is added or overturned.

## Tests

Unit tests only, in `tests/test_test_ui.py`, each `spec_exempt`: no scenario changes, as the neighbours' reasons say. No end-to-end run is added, and no test is deleted or merged.

| layer | test added | reason ([T1](../../../CODING_STANDARDS.md)) |
|---|---|---|
| unit | arguments follow `--`, a leading `ui/` dropped, other arguments unchanged | the stand-in for `subprocess.run` is the lowest layer that can fail |
| unit | vitest started beside the root config's copy is refused, naming the command, and writes nothing | a real vitest process is the only way the guard shows |

`test_the_tests_run_in_ui_and_return_their_code` stays as it is: it holds that no argument runs as today. The existing tests of `tools.test_ui` stay green.

## Dependencies

None.

## Risks / Trade-offs

- The guard's test runs a real vitest process, slower than its neighbours, and needs `ui/node_modules/`. Where it is absent the test skips and the gate's own vitest run refuses.
- Vitest may leave its config loader's temporary file behind when it exits. The HALT CHECK in task 2.2 is where that shows ([D5](#d5)).
- A worker may still start vitest in a way the root config does not see, such as `--root ui`. That start reads `ui/`'s config and writes nothing at the root, so it is harmless.

## Verdict

Ready to build: tools and documents alone, the guard held by a real vitest run and dropped if that run cannot show it.
