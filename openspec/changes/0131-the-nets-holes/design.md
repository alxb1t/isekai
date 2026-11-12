# The net's holes — design

Each silent patch is made loud, a guard holds every patch to a name its module reads, and `tools/mutate.py` says which mutants a set of tests kills. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The refactor that follows moves code between modules and removes patched globals. The net has a hole in each phase:

```
phase 6  no blind patch   a patch whose stand-in no assertion shows was reached, and a patch of a name nothing reads
phase 7  the pre-flight   no way to ask whether the tests notice a line, short of an audit's scripts and a coverage database
```

The change is built after `0130-the-record` releases, which follows `0129-the-refactors-rails`. It builds on `tests/test_ratchets.py` and its patch scan from `0129`, and shares `tests/test_ui_api.py` and `tests/test_ui_jobs.py` with `0130`. A task here names a function or a string, never a line, because both move lines.

## Goals / Non-Goals

Goals:

- A tripwire that no test shows can fire has a twin that fires it; a stand-in for a host or a seam records its calls, and a test reads them.
- A patch of a name that nothing in the repository reads is red.
- A person asks `uv run python -m tools.mutate <path:lines> --tests <files>` and reads which mutants survive.

Non-Goals:

- No product file moves: no `.py` under `isekai/` or `evaluation/` changes.
- No requirement, scenario, format version or decision of `docs/decisions.md` is added or amended.
- No patch is removed and no test is deleted or merged.
- No dependency: the runner is the standard library and the `pytest` the project has.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A silent patch keeps its patch and gains the proof that it is reached: a sentinel, a twin that fires the tripwire, or a record of calls the test reads | the patch is right; what is missing is the evidence that the product goes through it | removing the patch, which lets the suite reach the operator's machine |
| [D2](#d2) | A twin of a tripwire is the same patch over an input that reaches it, expecting the raise | a tripwire no test fires is a promise nobody checked | a unit test of the product path alone, which does not hold the patch's name |
| [D3](#d3) | A guard holds each patch that resolves to a module of `isekai`, `evaluation` or `tools` to a name the repository reads | a patch of a name nothing reads changes nothing, and passes whatever the product does | a count of patches, which `0129`'s ratchet already holds |
| [D4](#d4) | The guard shares one walk with the patch ratchet: `resolved_patches` returns each patch and `patched_modules` is built on it | walks of the same calls, kept apart, drift | a second walk in the guard |
| [D5](#d5) | The runner is `tools/mutate.py`, the standard library alone, run as `python -m tools.mutate` | no new package is wanted, and a test reaches a tool, never the reverse | a pytest plugin, a coverage database |
| [D6](#d6) | A mutant is one edit on one line of a function body, by one of the operators of the table, and a run applies each alone | the audit's sample was drawn the same way | a mutant over several lines, which no reader can judge |
| [D7](#d7) | The runner works in a copy of the tracked files, runs the named tests unmutated first, and refuses when they fail | a copy that lacks an ignored file would read as a kill | mutating the checkout, which a stopped run leaves broken |
| [D8](#d8) | A run exits 0 with no survivor, 1 with one and 2 when it refuses; a mutant that cannot load or that hangs is reported and is no survivor | an equivalent mutant is a person's call, a hang is noticed by a test, and a syntax error says nothing about the tests | counting a timeout a survivor |
| [D9](#d9) | `CONTRIBUTING.md` says when to run it, in one paragraph after the paragraph on measuring | a tool nobody is told to run goes unused | a line in `AGENTS.md`, which holds rules and not method |
| [D10](#d10) | The first phase rates `moderate` and the second `hard`; the build runs on Sonnet 5.5 high and is converged on Codex checkers | the first is small tests and a scan in small functions; the second is new logic | — |

### D1

Each of the silent patches below is read at the base. The remedy goes in the test named.

| patch | test | what the test misses | remedy |
|---|---|---|---|
| `MODEL_RECORDS` of `isekai.boundary.ollama`, in the autouse `_no_machine_records` of `tests/conftest.py` | `tests/test_caption.py` | no test shows a call reaches the empty directory and not the operator's | a sentinel: with the autouse fixture alone, `ollama.verified_build(READER)` refuses, and the refusal names `ollama.MODEL_RECORDS` |
| `_verified_build` as a tripwire | `test_a_completed_caption_reads_no_model_record` | the caption is complete, so the reader is never asked | a twin: the same patch, a caption not yet made, the raise expected |
| `_verified_build` as a tripwire | `test_composing_a_wiring_contacts_no_host_and_looks_up_no_binary` of `tests/test_pipeline_cli.py` | the reader is built and never called | a twin: the same patch, the wiring's reader called, the raise expected |
| `load_manifest` and `resolve` of `isekai.boundary.provision` | `test_importing_the_boundary_opens_no_file_and_computes_no_digest` of `tests/test_wd14.py` | nothing shows the re-imported module reaches provisioning at all | a twin: the same patches and re-import, then `verified_paths()`, the raise expected |
| `FileResponse` of `isekai.interface.ui.app` | `test_a_cross_site_request_without_origin_is_refused` of `tests/test_ui_api.py` | `read == []` holds whatever `FileResponse` is | a twin: the same patch, a same-origin request, `read` holding the photograph |
| `OPENER` of `isekai.boundary.ollama` | `test_prepare_is_refused_with_the_readers_message_and_starts_nothing` of `tests/test_ui_jobs.py` | a host that refuses gives the same refusal | `Closed.open` records its calls, and the test asserts one |
| `root` of the library and `ensure_built`, in `tests/test_ui.py` | `test_serve_returns_130_for_keyboard_interrupt` | the real library and bundle would serve the same exit | each stand-in records its call, and the test asserts each was asked once |
| `CHUNK` of `isekai.shared.chain` | `test_chain_spline_chunks_a_large_grid_without_changing_it` of `tests/test_chain.py` | a chunk that never splits gives the same answer | the kernel is wrapped by a counter, and the test asserts it ran once per chunk |
| `_clean` and `write_atomically` of `isekai.pipeline.importing` | `test_the_same_bytes_are_skipped_and_a_taken_name_is_renamed` of `tests/test_importing.py` | the barrier and the slow write may never run | both record their calls, and the test asserts each file was cleaned and written, and the barrier was not broken |

### D2

A twin carries `spec_exempt("structural: twin of <the guard's name>")`, in the form the exemption check holds. The tripwire of the twin raises `AssertionError` with its own sentence, and the twin expects that sentence, so a raise from any other cause is red.

```
guard:  patch + an input that never reaches it    →  passes whatever the product does
twin:   the same patch + an input that reaches it →  the sentence is raised
```

### D3

A patch is a call `x.setattr(target, "name", value)`, or `x.setattr("dotted.path", value)`, as the patch scan of `0129` reads one, its target resolved to a module of the packages of `PATCH_PACKAGES`: `isekai`, `evaluation` and `tools`. A target that resolves to no module — an instance, a class, a loop variable, a standard-library module — is not scanned.

A patch **names a name its module reads** when the name is read in a way of this table:

| read | where | example |
|---|---|---|
| a load of the bare name | anywhere in the module's own source, in any scope | `MODEL_RECORDS or _home_records()` in `ollama.py` |
| an attribute load through the module | in any file under `isekai/`, `evaluation/` or `tools/`, the module reached by an import as the patch's target is | `provision.resolve(...)` in `wd14.py` |
| an import of the name from the module | in any file under those, at any depth | `from isekai.boundary.provision import VOCABULARY_MANIFEST_PATH` inside a function |

An import resolves as the patch scan resolves one: absolute, since the repository's product code holds no relative import. A store is not a read, and a read in a test is not one: the test is the patch. A name read only in a function that no longer runs the patched path still counts; the guard cannot see that, and says so in its docstring.

```
tests/test_x.py   setattr(ollama, "MODEL_RECORDS", …)  ──▶ isekai.boundary.ollama . MODEL_RECORDS
                                                              │ read?  Name load in ollama.py  ✔
tests/test_y.py   setattr(wd14, "gone", …)             ──▶ isekai.boundary.wd14 . gone
                                                              │ read?  nowhere                  ✘  red
```

### D4

`tests/test_ratchets.py` holds `patched_modules(root)` from `0129`. Its walk is split into `resolved_patches(root, packages)`, which threads `packages` through the resolution of a target and returns each patch as `(path, line, module, name)`, the line taken from the call. `patched_modules` is built on it with `PACKAGES`, keeps its filter on the names a module binds at its top level, and keeps its output and its tests. `PATCH_PACKAGES` is `PACKAGES` and `tools`. `names_read(root)` returns, for each module of `PATCH_PACKAGES`, the names read in the ways of [D3](#d3), in a single pass over the product files. `unread_patches(root)` returns `<path>:<line> patches <module>.<name>, which nothing reads` for each patch whose name is not in `names_read`.

The guard asserts `unread_patches(REPO_ROOT) == []`, and that `resolved_patches(REPO_ROOT, PATCH_PACKAGES)` is not empty, so a scan that reads no test cannot pass.

### D5

```
uv run python -m tools.mutate <path>:<lo>[-<hi>] … (--tests <file-or-node-id> … | --all) [--timeout <seconds>]
```

| part | holds |
|---|---|
| `<path>:<lo>-<hi>` | a tracked file and the lines whose mutants are tried; `<path>:<lo>` is the one line. At least one; a file that is not tracked, or a range with no mutant, is a refusal |
| `--tests` | the tests that run for each mutant, as pytest takes them: files or node ids |
| `--all` | the suite but the browser's: `tests/` with `--ignore=tests/e2e`. One of `--tests` and `--all`, never both |
| `--timeout` | the seconds a mutant's run may take before it is ended; 300 when absent |

`main(argv=None, *, root=REPO_ROOT)` reads `sys.argv[1:]` when `argv` is absent, and takes the repository's root, so a test runs it over a small repository of its own. `tools/mutate.py` imports the standard library alone and nothing of `isekai`.

### D6

`sites(text, lo, hi)` returns each mutant on the lines `lo` to `hi`: only inside a function body, docstrings left alone, and only a node that starts and ends on one line. It applies one operator to one node and keeps the rest of the line as it was.

| operator | node | the edit |
|---|---|---|
| `cmp` | a comparison with one operator | `==` ↔ `!=`, `<` → `>=`, `<=` → `>`, `>` → `<=`, `>=` → `<`, `in` ↔ `not in`, `is` ↔ `is not` |
| `bool` | a boolean operation with a left and a right value | `and` ↔ `or` |
| `not` | a `not` | the `not ` removed |
| `const` | a `True`, a `False` or a whole number | the other boolean; `n` → `(n + 1)`, parenthesised so the neighbours keep their grouping |
| `raise` | a `raise` statement | `pass` |
| `ret` | a `return` of a value that is not `None` | `return None` |
| `call` | a statement that is one call | `pass` |
| `arith` | a `+`, `-`, `*` or `//` with no string operand | `+` ↔ `-`, `*` ↔ `//` |

A node's columns are byte offsets of the line's UTF-8, so each edit works on the line as bytes. A mutant is `Mutant(path, line, operator, old, new)`, `old` and `new` the whole line. A node that nested functions share is listed without a repeat.

### D7

`copy_tree(root, into)` copies each file `git ls-files -z` lists under `root` that exists, and links each of `LINKED` that exists as a directory of `root`: `models`, `ui/node_modules` and `ui/dist`, which no git index holds and the tests read.

The runner runs the chosen tests unmutated in the copy, before any mutant, with `PYTHONDONTWRITEBYTECODE=1` so a same-size mutant is never read from a stale bytecode file. A baseline that does not exit 0 is a refusal that prints the last lines of its output, for a copy missing a file reads as a kill.

Each mutant is written into the copy's file, the tests run, and the original text is written back, whatever the run did.

### D8

A mutant's run is `sys.executable -m pytest -x -q -p no:cacheprovider <tests>` with the copy as the working directory.

| pytest exit | verdict |
|---|---|
| 0 | `survived` |
| 1 | `killed` |
| any other, or a mutant `ast.parse` refuses | `invalid` |
| none within `--timeout` | `timeout` |

Each verdict prints as `<verdict> <path>:<line> <operator>: <old> -> <new>` when it is reached, with `old` and `new` stripped. The last line is `mutate: <k> killed, <s> survived, <i> invalid, <t> timeout`, and each survivor follows it as `survivor <path>:<line> <operator>`. The exit is 1 when `s` is not 0, 2 for a refusal, else 0.

### D9

The paragraph added to `CONTRIBUTING.md`, after the paragraph that opens *A change is measured as well as gated*:

```
**A move is pre-flighted.** A change that moves or rewrites lines of `isekai/` or `evaluation/` runs
`uv run python -m tools.mutate <path:lines> --tests <files>` over those lines, before the move and over the same lines after
it, on the tests that cover them. A survivor is killed by a test, or the change says why it is equivalent. It is not in the gate:
a run takes minutes.
```

### D10

Phase 6 rates `moderate`: small tests to place, and a scan in small functions over a walk that exists. Phase 7 rates `hard`: new logic, a runner of subprocesses and text edits. Each phase ends on a green `make gate`, and the build runs on Sonnet 5.5 high.

## Tests

Counts are those of `uv run pytest --collect-only -qq` over the files below, at the base, and the same command prints them after. Each case of a parametrized test counts as a test. `0129` creates `tests/test_ratchets.py` and `0130` adds a test to `tests/test_ui_jobs.py`; the counts below are the base's, and the added column is this change's.

| file | tests before | tests added |
|---|---|---|
| `tests/test_caption.py` | 52 | 2 |
| `tests/test_pipeline_cli.py` | 77 | 1 |
| `tests/test_wd14.py` | 24 | 1 |
| `tests/test_ui_api.py` | 114 | 1 |
| `tests/test_ui_jobs.py` | 33 | 0 |
| `tests/test_ui.py` | 21 | 0 |
| `tests/test_chain.py` | 24 | 0 |
| `tests/test_importing.py` | 29 | 0 |
| `tests/test_ratchets.py` | 0 at the base | 3 |
| `tests/test_mutate.py` | 0, the file is created | 20 |

The tests added are the ones the tasks name. The patches of the Ollama host, the library's root and bundle, the chunked kernel and the importer gain an assertion in the test they sit in, and add no test. `tests/test_ratchets.py` gains the guard, its twin and a test of the reads. `tests/test_mutate.py` holds each operator as a case and a case of `cmp` after non-ASCII text, the line range, the function body, the multi-line statement, the copy, the baseline, the survivor, the clean run, the invalid mutant, the hang and the command of `--all` and `--tests`.

Read and not edited: `tests/conftest.py`, whose autouse fixture the first sentinel proves.

Added with no count of their own: `calc.py` and `tests/test_calc.py`, written into the small repository the `small_repo` fixture of `tests/test_mutate.py` builds under `tmp_path_factory`, so `--collect-only` never sees them.

Each new test carries one `spec_exempt`, in the form the exemption check holds: a guard `structural: <the rule it holds>`, a twin `structural: twin of <the guard's name>`, and a test of a function `structural: <what the function does>`.

| layer | added | removed | command |
|---|---|---|---|
| unit and integration | the sum of the column above | 0 | `uv run pytest --collect-only -qq` over the files above |
| end-to-end | 0 | 0 | `uv run pytest --collect-only -qq tests/e2e` |

- No end-to-end test is added (`T1`): each twin is a unit test at the lowest layer that can fail, and the runner's run over a small repository is an integration test of subprocesses. A test that takes long is timed before it is kept.
- No test is deleted or merged, so there is no table of what carries each one's assertions (`T5`).
- The twin of each tripwire is a unit test of it, never a browser test (`T6`).

## Dependencies

None.

## Risks / Trade-offs

- A twin of a tripwire reaches the product by a path the original test avoids, and a stage may turn an unexpected exception into a record. A twin that cannot fire its tripwire is a halt, never a looser expectation.
- The guard counts a read anywhere in a module, so a patch of a name kept alive by a dead branch passes. The audit found none; the guard's docstring says what it cannot see.
- A patch that `0129` or `0130` adds before this change is built may name a name nothing reads. The guard's first run is a halt check: a patch it finds is a silent patch the plan did not read.
- A mutant that no test notices may be equivalent, and the runner cannot tell. It reports; a person judges, and the change says why in its design.
- A baseline that is green in the copy proves the copy has what the named tests read. `--all` may fail its baseline on a test that needs the repository's git history; the refusal says so and no mutant is tried.
- The copy of the tracked files is made for each run. The checkout is never mutated, so a run stopped by the person leaves nothing to restore.

## Verdict

Ready to build, in the phases of [tasks](tasks.md). No decision of `docs/decisions.md` is added or amended, and no requirement is touched.
