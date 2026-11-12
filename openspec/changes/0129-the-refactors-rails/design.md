# The refactor's rails — design

The gate learns what the refactor leans on: a stage may be a package, size and patches are ratcheted, the importer tables are derived, and the frozen files and the documents say what holds. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The refactor that follows moves code between files, and the gate must say when it moves it wrong. What the gate does not hold today, by phase:

```
phase 4  the stage rule        a package under pipeline/ trips the guard on its own modules
phase 5  the ratchets          no rule on a file's or a function's size, or on what a test patches
phase 6  the importer tables   hand-kept in six READMEs; short; one route list beside them
phase 7  the frozen files      no agent document names the files the pod image freezes; the docs say what is no longer so
```

The change is built after `0128-the-guards-hold` releases. The two share `tests/test_layers.py`, `tests/test_infra.py`, `tests/test_docs.py`, `docs/` and `CHANGELOG.md`, on disjoint lines: `0128` rewords exemption reasons there, this change adds tests and edits documents. A task here names a function or a string, never a line, because `0128` moves lines.

## Goals / Non-Goals

Goals:

- A stage that is a package passes the layer guard, and a stage importing another still fails it.
- A file, a function, a parameter list, a `ui/src` file and a module's patched names each have a ceiling, with their offenders listed once.
- Each README's importer table is written by a tool from the graph the layer guards read, and a test re-derives it.
- An agent reading `AGENTS.md` learns which files the image freezes, and a red image record says how to move one.

Non-Goals:

- No product file moves: no `.py` under `isekai/` or `evaluation/` changes, and the image-frozen `Dockerfile` stays.
- No requirement, scenario or format version moves. D55 and D56 are added to `docs/decisions.md`; no decision in force is amended.
- No offender is fixed: a listed file stays long until the refactor version that splits it removes its row.
- No test is deleted or merged.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | A stage is the first segment under `isekai.pipeline`; a stage's modules import each other, and no stage imports another's, its front door included | `stage_imports` flags a package's own modules today, so a stage cannot grow into a package | naming each package in the guard, which a new package breaks |
| [D2](#d2) | The stage rule is written in the component principle and recorded as D55 of `docs/decisions.md` | no document defines a stage; a rule the gate holds is read before it is broken | a comment in the guard alone |
| [D3](#d3) | A ratchet is a table of listed offenders and a row ceiling: an unlisted offender is red, a row whose offender stopped offending is red, a row count off its ceiling is red; a listed offender may grow | a refactor that is queued but not built must not halt the next route or screen; a removed row must not come back | a number per row held equal, which a feature halts; a shrink-only number |
| [D4](#d4) | The ceilings are 800 lines for a file under `isekai/`, 100 for a function, 6 positional parameters, 600 lines for a file under `ui/src/`, and no patch of a module's own names | each leaves the offenders a list a reader can hold | a ceiling at today's largest, which lists nothing |
| [D5](#d5) | The patch scan reads each `setattr` call of `tests/`, resolves its target to a module of `isekai` or `evaluation`, and counts it when that module binds the name at its top level | the audit found about a hundred tests reaching code by patching globals | a text search, which cannot tell a module's name from a local one |
| [D6](#d6) | The tables are written from the scans by the build, and D56 records the rule | a table written by hand is a copy that starts wrong | a table of the audit's numbers |
| [D7](#d7) | The graph functions of `tests/test_layers.py` move to `tools/import_graph.py`, and the test imports them | the house's direction is tests to tools, and the module imports pytest at its top | a deriver that imports a test module |
| [D8](#d8) | `tools/derive_imported_by.py` writes the inside and the outside column of each *Imported by* table, from that graph, and no test | a list of names written by hand goes stale; the tests column is every test that imports a file | writing the inside column alone, which leaves a copy of the graph |
| [D9](#d9) | A test re-derives each table and expects the same bytes, a guard names every README that holds a table, and `make derive` runs the tool | a derived file is a copy a test holds ([principles](../../../docs/principles.md#configuration-is-declared-never-computed-and-declared-once)) | a check run by hand |
| [D10](#d10) | The route list of the `ui/app.py` row of `isekai/interface/README.md` goes | it lists a fraction of the routes and is edited with each | a derived route list, which waits for the refactor's route declarations |
| [D11](#d11) | `AGENTS.md` names the files the image freezes, a test holds the list equal to the files `config/image.json` records, and the record's failure says the recipe | no agent document names them, and a red record prints a bare path | a pointer to `docs/pins.md` alone |
| [D12](#d12) | *Known breaks* name what the audit found and the page left out | a break the page omits reads as a rule that holds | counting them: a count goes stale |
| [D13](#d13) | The stale claims in documents and `tools/manifest.py` are corrected as the table of [D13](#d13) says | each is a sentence a reader acts on | leaving them to the version that moves the code |
| [D14](#d14) | The phases rate `moderate`; the build runs on Sonnet 5.5 high and is converged on Codex checkers | guard logic in small functions, each with its twin, and prose to place | — |

### D1

`stage_imports(root)` gives each dotted module its **stage**: the segment after `isekai.pipeline.`, and none for `isekai.pipeline` itself. An edge is a fault when importer and imported both have a stage and the stages differ.

```
isekai.pipeline.review            stage review
isekai.pipeline.review.drafts     stage review
isekai.pipeline.generate          stage generate

review.drafts → review             passes
generate      → review (front door) fault
review.drafts → generate          fault
```

Twins join the module twin: a package importing its own modules passes, and a package importing another stage, and a module importing a package's front door, are caught.

### D2

The component principle of `docs/principles.md` gains a sentence after *a package earns its place when the contract needs more than one file*: **In `pipeline/`, a stage is the first segment under `isekai.pipeline` — one module, or one package. A package's modules import each other; no stage imports another, and a package's front door is as much another stage's as any of its modules is.** It links D55. D55 sits under *Code and environment* in `docs/decisions.md`, after D48:

```
### D55 · A stage may be a package

**A stage is the first segment under `isekai.pipeline`: one module, or one package whose `__init__.py` is its front door. The modules of a stage import each other; no stage imports another, its front door included.**

- **Why:** the layer guard read a stage as any file under `pipeline/`, so a stage that grew past one file would have tripped it on its own modules, and its private maths went down into `shared/` instead.
- **Made by:** `0129`.
```

### D3

`ratchet_faults(measured, listed, rows)` takes the offenders a scan finds, the keys of the table, and the table's row ceiling. It returns a sorted list of faults: `unlisted <key>`, `no longer offends <key>` and `rows <n> listed, ceiling <m>`. A table row is `key: the measure when it was listed`; the measure is a record for the reader and no test reads it.

| a table | its row ceiling | its key |
|---|---|---|
| `LONG_FILES` | `FILE_ROWS` | `isekai/interface/ui/app.py` |
| `LONG_FUNCTIONS` | `FUNCTION_ROWS` | `isekai/interface/ui/app.py::create_app` |
| `WIDE_FUNCTIONS` | `WIDE_ROWS` | `isekai/pipeline/review.py::_write_draft` |
| `BIG_UI_FILES` | `UI_ROWS` | `ui/src/views/Review.vue` |
| `PATCHED_MODULES` | `PATCHED_ROWS` | `isekai.interface.wiring` |

A row ceiling equals its table's length, so a removed row lowers it in the same commit and a new row raises it past what review allows.

### D4

| rule | scope | measure | offends when |
|---|---|---|---|
| `long_files` | `isekai/**/*.py` | `len(text.splitlines())` | more than `FILE_LINES` = 800 |
| `long_functions` | the same | `end_lineno - lineno + 1` of the `def`, decorators out; methods and nested functions each, named `Class.method` and `outer.inner` | more than `FUNCTION_LINES` = 100 |
| `wide_functions` | the same | `posonlyargs` and `args`, a leading `self` or `cls` dropped; `*args` and keyword-only parameters not counted | more than `POSITIONAL` = 6 |
| `big_ui_files` | `ui/src/**` `.vue`, `.ts` and `.css`, a name ending `.test.ts` out | `len(text.splitlines())` | more than `UI_FILE_LINES` = 600 |
| `patched_modules` | `tests/**/*.py`, each `setattr` call | see [D5](#d5) | one or more patches |

A scan that reads no file lists no offender, so every row would read *no longer offends* and the guard is red: a scan cannot pass blind.

### D5

A call `x.setattr(target, "name", value)` with a string second argument, or `x.setattr("dotted.path", value)`, is a patch.

A target is a dotted chain of names and attributes, such as `library` or `ui.library` or `isekai.interface.ui.library`. Its first name resolves through the imports of the whole file, function bodies included: `import isekai.x as a`, `import isekai.x.y`, `from isekai import x`, or `from isekai.x import y` where `isekai.x.y` is a module. Each attribute extends the dotted path, and the chain counts when the path is a module of `isekai` or `evaluation`. A dotted string target counts the same way, its last segment the name.

The patch counts when that module binds the name at its top level: a `def`, a `class`, an assignment or an import.

A target that does not resolve — an instance, a loop variable, a standard-library module reached through an isekai module, a class — counts for no module. The table is keyed by the module's dotted name, over the packages `isekai` and `evaluation`.

### D6

Each table is the scan's output at the build: a task prints it, and the task writes its rows. D56 of `docs/decisions.md` names the ceilings and the rule that a row is removed, never added:

```
### D56 · Size and patches are held by ratchets

**`tests/test_ratchets.py` holds a ceiling for the lines of a file under `isekai/`, the lines of a function, a function's positional parameters, the lines of a file under `ui/src/` and the patches of a module's own names. An offender past its ceiling is a listed row of its table; one unlisted is red, and a row whose offender no longer offends is red until it is removed. A listed offender may grow; a row is removed by the version that removes the offender, and none is added.**

- **Why:** the gate held no rule of size or shape, so the largest files and the most-patched modules grew with every feature. A ceiling on the unlisted stops a new one; leaving a listed offender free to grow keeps the next route or screen from halting on a refactor that is queued and not yet built.
- **Accepts:** a listed offender grows unchecked until its row goes. Reopen when a refactor version leaves a row standing past its work.
- **Made by:** `0129`.
```

### D7

`tools/import_graph.py` holds `PACKAGES`, `Edge`, and the functions, public and stdlib only: `module_name(root, path)`, `is_module(root, name)`, `sources(root, scope)`, `imports(root, path)` and `edges(root, scope)`, the last cached. Their bodies are those of `_module_name`, `_is_module`, `_sources`, `_imports` and `_edges` in `tests/test_layers.py`.

The layer rules stay in the test, which imports the graph from the tool, so a test reaches a tool and a tool never reaches a test. The readers of the moved names are all in `tests/test_layers.py`, per the cut notes.

### D8

`derive(root, readme)` returns a README's text with its `## Imported by` section rewritten: the lines between the heading and the table's header row become the note below, the header row stays as it stands, and each row keeps its first cell while the deriver writes the other two.

```
**Derived.** `uv run python -m tools.derive_imported_by` writes this table from the import graph of `tools/import_graph.py`, the one the layer guards read, and a test re-derives it. It names importers in `isekai/`, `evaluation/` and `tools/`, never a test.
```

`edges` names modules by dotted name. The deriver maps a dotted name to its file, `isekai.interface.ui` to `ui/__init__.py`, and a package row's importers are written the same way.

| cell | holds | written as |
|---|---|---|
| the row's file | a module `name.py`, or a package `name/` | read, never written; a row naming no module is refused |
| inside | the importers whose top-level package is the README's own (`isekai` or `evaluation`) | the path under the README's own directory when it is there, else under the package; `—` when none |
| outside | the importers in the other of `isekai`, `evaluation` and `tools` | the path from the repository root; `—` when none |

A package row has as importers the modules outside the package that import it or anything under it. A module is not its own importer.

Cells list importers sorted by full path, each in backticks, joined by `, `. The README list is `TABLES`: the layer READMEs of `isekai/` and the README of `evaluation/`.

The graph is read over `isekai`, `evaluation` and `tools`; `tests/` is never scanned, which is why no test is named. A cell that held prose — `pod_start.py`'s *for the hold its limit's floor is above; the image runs it as a file* — loses it to the table; the sentence moves to a note under the boundary table.

### D9

`tests/test_docs.py` holds each table in `TABLES` against `derive`, one parametrized case a README, and a guard asserts that every `README.md` under `isekai/` and `evaluation/` with an `## Imported by` heading is in `TABLES`. Twins build a tree under `tmp_path`: a stale cell re-derives to a different text, and a row naming no module is refused. The `derive` recipe of `Makefile` runs the tool before `drift`, so `make derive` writes every derived file.

### D10

The `ui/app.py` row of `isekai/interface/README.md` lists endpoints. It becomes what the module is: the endpoints, and the only module in the package that imports FastAPI or uvicorn. The routes are `create_app`'s, which the refactor declares.

### D11

The guardrail is one bullet of `AGENTS.md`'s *Guardrails*: the files `config/image.json` records — `Dockerfile`, `image/pyproject.toml`, `image/uv.lock`, `image/.python-version`, `config/models.json`, `isekai/boundary/provision.py` and `isekai/boundary/pod_start.py` — are frozen into the pod image; an edit turns `tests/test_infra.py` red until the record is re-derived, and the image holds it only after a rebuild and a metered proof; the recipe is [`docs/pins.md`](../../../docs/pins.md). A test holds the list: every key of the record's `files` is named in backticks in `AGENTS.md`, with a twin over a text that leaves one out. `record_failure(faults)` builds the message the record's test prints, naming each file and `uv run python -m tools.image_record`, `docs/pins.md` and its *Re-pinning* recipe, and a test holds the message.

### D12

Each entry below is a sentence of `docs/principles.md`. The evidence is read at the cut, in the cut notes.

| principle | the entry, added to its *Known breaks* or *Not yet held* |
|---|---|
| A component is a contract | The break is widened to: `boundary/ollama.py`'s `MODEL_RECORDS` is a module global the suite patches, not a parameter, so two roots in one process means patching global state; so is every name of a module `PATCHED_MODULES` of `tests/test_ratchets.py` lists |
| Only a front end composes | `interface/cli.py`'s `_refuse_bad_source` decides that a flow is not its own source, the review stage's rule. `interface/wiring.py`'s `proposer_of` turns a placement model's digest mismatch into a refusal, as `load_vocabulary` does for the vocabulary. The discard of a render is spelled twice, `interface/cli.py`'s `_discard` and `interface/ui/app.py`'s `delete_render`, and the two differ: the app drops each edit image's thumbnails, the CLI the render's alone |
| A failure refuses one input, never the batch | A new *Known breaks*: `pipeline/edit.py` records no failure for a failed sampling and keeps no retry budget; the request stays pending, so a later session samples it again, and the refusal names the discard |
| Everything that shapes an output is pinned | *Not yet held* also for the edit's checkpoint and ControlNet, which `edits/tattoo-wai/edit.json` names by file name with no digest, as a flow pins each |

### D13

Before → after, each in the file named. A row's *before* is the text at the cut.

| file | before | after |
|---|---|---|
| `ARCHITECTURE.md`, `docs/principles.md` | `shared` — what the stages share: the vocabulary, the field map, image headers. | … image headers, and the placement's maths: the ink, the tattoo, the chain and the proposal's geometry. |
| the same | `foundation` — the run directory, the flow and the refusal. | … the refusal, and what rides with them: the artifacts' contract, the edit registry, the caption config, the migration and the command text a refusal prints. |
| `docs/principles.md` | `boundary` — … Ollama, the ComfyUI transport, the WD14 session, downloads. | … the WD14 session, the pose finder, the segmenter, the pod's start, downloads. |
| `docs/modules.md`, the lazy edges | `interface ──▶ boundary  wiring.py, inside load_vocabulary(); provision.py is on the entry point's graph through ollama.py` | `wiring.py`, inside `load_vocabulary()`, except `DigestMismatch`, which it imports at module scope; `provision.py` is on the entry point's graph through `ollama.py` and `wiring.py` |
| `docs/modules.md`, the delete | … `drop_thumbnails`, … `discard_render` and review's `withdraw`, as the CLI's `discard` calls them. | … the same three; the CLI's `discard` calls them too, but drops the render's thumbnails and not each edit image's. |
| `isekai/interface/README.md` | `ui/` is a sibling of `cli.py`, not a client of it. Both reach the pipeline the same way … so neither is privileged and neither goes through the other. | … neither is privileged. The CLI imports `isekai.interface.ui` inside the handlers of `ui`, `migrate` and `discard`, never at module scope, and the UI imports no CLI module. |
| `docs/pins.md` | *A model manifest.* … `tools/derive_manifest.py`, `tools/derive_vocabulary.py`, `tools/derive_reader.py`, `tools/derive_placement.py` … review the diff under `config/`. | the list gains `tools/derive_eval_manifest.py`, and the review adds `evaluation/eval_models.json`. |
| `tools/manifest.py` | One writer for all three derivers | One writer for every manifest deriver |

### D14

The phases rate `moderate`: scans and a deriver in small functions, each with its twin, and prose to place. The build runs on Sonnet 5.5 high whole, and each phase ends on a green `make check`.

## The ratchet offenders at the cut

What the scans of [D4](#d4) and [D5](#d5) find at the base, read at the cut by a throwaway script of the same rules. The build prints the same list from `tests/test_ratchets.py` before it writes a table, and a table written from another list is wrong.

| table | offenders at the cut |
|---|---|
| `LONG_FILES` | `isekai/foundation/run.py`, `isekai/interface/cli.py`, `isekai/interface/render.py`, `isekai/interface/ui/app.py`, `isekai/interface/ui/library.py`, `isekai/pipeline/importing.py`, `isekai/pipeline/review.py`, `isekai/pipeline/tattoos.py` |
| `LONG_FUNCTIONS` | `ollama.py::ask`, `flow.py::load_flow`, `cli.py::build_parser`, `cli.py::_per_item`, `cli.py::_per_item.work`, `render.py::_session`, `render.py::_rendered`, `ui/app.py::create_app`, `generate.py::render`, `review.py::approve` |
| `WIDE_FUNCTIONS` | `run.py::refusal_for`, `drafting.py::draft_across`, `render.py::Record.__init__`, `render.py::_session`, `render.py::_asked`, `render.py::_rendered`, `ui/app.py::create_app.read_compare`, `review.py::_write_draft`, `sheet.py::_from_tag_list`, `tattoos.py::save_outline`, `tattoos.py::ink_layer`, `tattoos.py::ink_view`, `tattoos.py::preview`, `tattoos.py::composite` |
| `BIG_UI_FILES` | `ui/src/app.css`, `ui/src/views/Hub.vue`, `ui/src/views/Review.vue` |
| `PATCHED_MODULES` | the modules of `isekai` and `evaluation` whose names a test patches: the scan prints them, and the tests `0127` and `0128` touch may move a row |

## Tests

Counts are those of `uv run pytest --collect-only -qq --ignore=tests/e2e` over the files below, at the base, and the same command prints them after. `0128` adds no test to the files below, so the counts hold at the build.

| file | tests before | tests added |
|---|---|---|
| `tests/test_layers.py` | 14 | 2 |
| `tests/test_ratchets.py` | 0 | 11 |
| `tests/test_docs.py` | 2 | 9 |
| `tests/test_infra.py` | 77 | 3 |

The tests added are the ones the tasks name. `tests/test_docs.py` counts each case of the re-derive test as a test, beside the guard that every table is derived and its twins. `tests/test_ratchets.py` holds a guard and a twin for each rule, and a test of `ratchet_faults`.

Each new test carries one `spec_exempt`, in the form `0128` checks: a guard `structural: <the rule it holds>`, a twin `structural: twin of <the guard's name>`, and a test of a function `structural: <what the function does>`. A twin names the guard it twins, never a reason of its own.

Edited with no test added: the tables of the six READMEs, the documents named in [D13](#d13), `AGENTS.md`, `docs/principles.md`, `docs/decisions.md`, `isekai/interface/README.md`, `tools/manifest.py` and the `derive` recipe of `Makefile`.

| layer | added | removed | command |
|---|---|---|---|
| unit and integration | the sum of the column above | 0 | the command above |
| end-to-end | 0 | 0 | `uv run pytest --collect-only -qq tests/e2e` |

No end-to-end test is added (`T1`): each guard is a unit test of a function over a tree, and each twin runs it over a `tmp_path` tree. No test is deleted or merged, so there is no table of what carries each one's assertions (`T5`). The twin of each new guard is a unit test of the guard, never a browser test (`T6`).

## Dependencies

None.

## Risks / Trade-offs

- A listed offender grows unchecked, by [D3](#d3). The row stays red-free until the refactor removes the offender, and a row ceiling stops a new row.
- The patch scan counts a patch of a name a module binds. A test that patches a standard-library module reached through an isekai module, or a class, is not counted: those targets do not resolve to a module of the repository.
- `0128` rewords exemption reasons in the files this change edits, and its form check holds each new reason to `structural: <rule>` or `structural: twin of <test>`. A task here names the form, and a test it names exists.
- The deriver drops the prose a cell carried. The one sentence of the boundary table that said something is moved into a note under it.
- The list in `AGENTS.md` is held to the record in one direction: a name in the record the page leaves out is red, and a name on the page the record dropped is a review matter.

## Verdict

Ready to build, in the phases of [tasks](tasks.md). D55 and D56 are added to `docs/decisions.md`; no requirement is touched.
