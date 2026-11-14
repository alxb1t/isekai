# One vitest file — tasks

Phases: the wrapper takes a file, a root config refuses the wrong start, the documents name the command. Decisions are in [design](design.md).

## Progress

- [x] 1 — The arguments · moderate
- [ ] 2 — The guard · hard
- [ ] 3 — The documents · moderate

## 1 — The arguments

- [x] 1.1 In `tools/npm_ui.py`, give `run` a last parameter `args: Sequence[str] = ()`. Empty runs `["npm", "run", script]`; else `["npm", "run", script, "--", *args]`. Reword its docstring to say a script's arguments follow `--` ([D1](design.md#d1)).
  Verify: `grep -n -F 'args' tools/npm_ui.py` prints the parameter and the command's line.
- [x] 1.2 In `tools/test_ui.py`, add `in_ui(args: Sequence[str]) -> list[str]`, which removes a leading `ui/` from each argument, with its docstring example ([D2](design.md#d2)).
  Verify: `grep -n -F 'in_ui(' tools/test_ui.py` prints its definition.
- [x] 1.3 In `tools/test_ui.py`, give `main` a second parameter `args: Sequence[str] = ()` that passes `in_ui(args)` to `npm_ui.run`, and make the `__main__` block call `main(args=sys.argv[1:])`.
  Verify: `grep -n -F 'sys.argv[1:]' tools/test_ui.py` prints the block's line.
- [x] 1.4 In the module docstring of `tools/test_ui.py`, add the one-file command `uv run python -m tools.test_ui ui/src/<name>.test.ts` under the whole-suite one.
  Verify: `grep -n -F 'tools.test_ui ui/src' tools/test_ui.py` prints the docstring's line.
- [x] 1.5 In `tests/test_test_ui.py`, add `test_a_file_is_run_in_ui_after_the_double_dash` with `spec_exempt`, in the style of its neighbour: `main(root, ["ui/src/cancel.test.ts", "-t", "a name"])` and `main(root, ["src/cancel.test.ts"])` run `["npm", "run", "test", "--", "src/cancel.test.ts", "-t", "a name"]` and `["npm", "run", "test", "--", "src/cancel.test.ts"]` in `root / "ui"`. Leave `test_the_tests_run_in_ui_and_return_their_code` as it is: it holds that no argument runs as today.
  Verify: `uv run pytest tests/test_test_ui.py` passes.
- [x] 1.6 Run one file through the wrapper from the root, then a path that matches no file. Before this phase the wrapper ignores both and runs the whole suite, so the second check is the one that fails first.
  Verify: `uv run python -m tools.test_ui ui/src/cancel.test.ts` exits 0.
  Verify: `uv run python -m tools.test_ui ui/src/no-such-file.test.ts` exits 1.

## 2 — The guard

- [ ] 2.1 Add `vitest.config.mjs` at the repository root, with the text of [D4](design.md#d4) word for word.
  Verify: `grep -n -F 'tools.test_ui' vitest.config.mjs` prints the refusal's line.
- [ ] 2.2 **HALT CHECK** In `tests/test_test_ui.py`, add `test_vitest_beside_the_root_config_refuses_and_writes_nothing` with `spec_exempt`, as [D4](design.md#d4)'s table says: it skips when `refusal()` names a missing toolchain. If it cannot pass as written, the plan is wrong: [D5](design.md#d5) drops the guard.
  Verify: `uv run pytest tests/test_test_ui.py -k beside_the_root_config` passes.
- [ ] 2.3 Start vitest at the root the way a worker does. It refuses, naming the command.
  Verify: `npm --prefix ui exec -- vitest run ui/src/cancel.test.ts` exits 1.
- [ ] 2.4 Check that the start of 2.3 wrote no root `node_modules/`. This holds before 2.1 too: it fails only if 2.3 ran with no guard, so it proves the guard stopped vitest before it wrote.
  Verify: `test -e node_modules` exits 1.
- [ ] 2.5 Run the whole suite through the wrapper: the root config leaves `ui/`'s run alone. This holds before 2.1 too, and proves the guard does not leak into `ui/`.
  Verify: `uv run python -m tools.test_ui` exits 0.

## 3 — The documents

- [ ] 3.1 In `CONTRIBUTING.md`, add the paragraph of [D6](design.md#d6) after the gate's paragraph in *The evidence a change carries*.
  Verify: `grep -n -F 'tools.test_ui ui/src' CONTRIBUTING.md` prints the paragraph's line.
- [ ] 3.2 In `AGENTS.md`, change the gate line to the *after* of [D6](design.md#d6).
  Verify: `grep -n -F 'tools.test_ui ui/src' AGENTS.md` prints the gate line.
