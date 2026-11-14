# The verbs move — design

`cli.py` hands each verb to a package as one row, and keeps the parser's assembly and the dispatch. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`isekai/interface/cli.py` holds every verb's arguments in `build_parser` and every verb's run in the branches of `dispatch`. The record `tests/record/verbs.json` pins each verb's arguments in order, so a move that changes one is red. The rows of the size ratchet name the file, and the tests patch `cli.RUNS_ROOT` and `cli.wiring`, which `_migrate` and `main` read.

| measure | command | prints |
|---|---|---|
| lines of the file | `wc -l isekai/interface/cli.py` | `1593` |
| ratchet keys naming the file | `grep -c "isekai/interface/cli.py" tests/test_ratchets.py` | `4` |
| mutants naming the file | `grep -c '"path": "isekai/interface/cli.py"' tests/mutants.json` | `6` |

## Goals / Non-Goals

- Goal: each verb is declared once, as a row in the module of its family, and `cli.py` assembles and dispatches.
- Goal: no existing test's assertion changes, nothing under `tests/record/` changes, and the image-frozen files stay byte-identical.
- Goal: the ratchet rows of the file and of `build_parser` go, and a decision says why.
- Non-goal: `_per_item`, the flow stages' second chain, the command builder, help text, a new verb or flag. See the proposal.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | The verbs live in the package `isekai/interface/verbs/`, entered by its front door | a `cli/` package would shadow `cli.py` and rename every ratchet key and importer | a `cli/` package; flat modules beside `cli.py` |
| [D2](#d2) | A verb is a `Verb` row: name, summary, arguments, run | a verb's name, arguments and run sit in one place, and the record proves the arguments | a table of names beside the functions |
| [D3](#d3) | `render`, `prepare` and `migrate` are bound in `cli.py` | their runs need `_dispatch_argv`, `_per_item` and the patched `RUNS_ROOT` and `wiring`, and no module of the package imports `cli.py` | a lazy import of `cli.py` from the package |
| [D4](#d4) | The pinned names keep their spelling; every other name that crosses a module is public | the record pins the type and action names, and a name that crosses a module is public | renaming nothing; renaming the pinned names |
| [D5](#d5) | Each moving phase is pre-flighted before and after, on the tests that reach its lines | a move is held by the suite, and the suite is measured first | one run for the whole move |
| [D6](#d6) | The moved mutants take their new path, with their text unchanged | an entry is addressed by path and exact text | rewriting the entries |
| [D7](#d7) | A ratchet row goes in the phase whose move ends its offence | a row that no longer offends is red | removing both rows in the last phase only |
| [D8](#d8) | A decision says a verb is declared once, and the documents it makes false are amended | the documents of a move are amended in its own diff | amending later |
| [D9](#d9) | The change has no spec delta | no requirement is touched | a requirement written to satisfy the validator |

### D1

The package holds these modules, and no others.

| module | holds |
|---|---|
| `isekai/interface/verbs/__init__.py` | the front door: imports and `__all__` |
| `isekai/interface/verbs/common.py` | `Verb`, the argument types, the reporter, the shared helpers |
| `isekai/interface/verbs/library.py` | `import`, `compare` and `ui` |
| `isekai/interface/verbs/drafts.py` | `draft` and `discard` |
| `isekai/interface/verbs/edits.py` | `ink` and `edit`, with `--pending`'s run |
| `isekai/interface/verbs/session.py` | `render`'s arguments |
| `isekai/interface/verbs/prepare.py` | `prepare` |
| `isekai/interface/verbs/generate.py` | `generate` |
| `isekai/interface/verbs/stages.py` | the arguments of `assign`, `caption`, `tag`, `sheet`, `review`, `approve` and `show` |

A module imports its siblings by their own module name and never the front door. `cli.py` imports names from the front door alone. A name the front door exports is never a module's name, compared without case: the import graph reads `from isekai.interface.verbs import generate` as an import of the module `generate`, past the door, and a case-insensitive disk resolves `GENERATE.py` to `generate.py`.

The package stays on the entry point's `-S` graph: every module imports the standard library and `isekai` alone at module scope. The lazy `isekai.interface.ui` imports stay inside `run_ui` and `run_discard`, where they are today.

Imports follow the code. A module imports what it reads, and `cli.py` drops what it no longer reads, as `uv run ruff check .` reports. A local of a moved function keeps its name, so a public name never collides with one: `named` and `cells` would, and are renamed in [D4](#d4).

### D2

```
@dataclass(frozen=True)
class Verb:
    name: str
    summary: str
    arguments: Callable[[argparse.ArgumentParser], None]
    run: Callable[[argparse.Namespace, Wiring], int] | None = None
```

`arguments` adds the verb's arguments to its parser in the order `build_parser` runs its statements for that verb today, top to bottom with the loops unrolled; the record proves the order. `run` is `None` for the verbs `dispatch`'s tail runs, which are the flow-stage verbs and `generate`.

Each verb's `arguments` is a function `<verb>_arguments` of its family's module, for example `import_arguments`. In the last phase `dispatch` looks the verb's row up in `ROWS` and, when it has a run, answers with the line `return row.run(args, wired)` inside its `try`, so a refusal prints as it does today.

`summary` is the text `VERBS` holds for the verb, and arrives in the last phase. Until then `VERBS` stays in `cli.py` and a row has no summary.

Until the last phase `cli.py` keeps a tuple `_MOVED` of the rows moved so far. `build_parser` calls `moved.arguments(made[moved.name])` for each, and `dispatch` returns `moved.run(args, wired)` for a verb a moved row names that has a run. The last phase replaces both with the tuple `ROWS`, which holds every verb's row in `VERBS`' order, and deletes `_MOVED`.

`_MOVED`, and later `ROWS` and the `VERBS` derived from it, are defined after the handlers `cli.py` binds, `_migrate` among them. A bound run is a `def` in `cli.py` that calls the family's function with the extra argument, so no name is read before it exists. `VERBS` stays a module name of `cli.py` and a `tuple[tuple[str, str], ...]` of `(row.name, row.summary)`, the shape the tests and `build_parser` unpack today. When a verb's row moves, its name leaves every loop of `build_parser` that named it, and joins the exclusion tuple of the first loop when it is not in it, so no argument is added twice.

A row constant is the verb's name in capitals and `_ROW`: `IMPORT_ROW`, `COMPARE_ROW`, `UI_ROW`, `DRAFT_ROW`, `DISCARD_ROW`, `INK_ROW`, `EDIT_ROW`, `RENDER_ROW`, `PREPARE_ROW`, `GENERATE_ROW`, `ASSIGN_ROW`, `CAPTION_ROW`, `TAG_ROW`, `SHEET_ROW`, `REVIEW_ROW`, `APPROVE_ROW` and `SHOW_ROW`. The suffix keeps `PREPARE_ROW` from reading as the module `prepare` on a disk that ignores case.

### D3

A row whose run needs what only `cli.py` holds is bound there, by `dataclasses.replace(<row>, run=…)`. The family module holds the handler with that part as a parameter.

| verb | the family module holds | `cli.py` binds |
|---|---|---|
| `render` | the arguments, `RENDER_ROW` with no run | `run_session(args, wired, _dispatch_argv)` |
| `prepare` | `run_prepare(args, wired, per_item)`, the arguments, `PREPARE_ROW` with no run | `run_prepare` with `_per_item` |
| `migrate` | nothing | `_migrate` and its arguments, whole |

`_migrate` stays whole because `tests/test_migrate.py` patches `cli.RUNS_ROOT` and `cli.wiring`, and a patch of a new module is refused by the patch ratchet. `_per_item`, `_assign`, `_existing_run`, `_seam`, `_flows_for`, `_refuse_bad_source`, `_named_a_flow`, `_Verb`, `_WRITES`, `VERBS`, `build_parser`, `dispatch`, `_dispatch_argv` and `main` stay in `cli.py`.

### D4

The names the record and the tests pin keep their spelling: `_seed`, `_session_id`, `_depth`, `_Targets` and the inner `parse` of `_positive`. They are imported inside the package; `cli.py` imports them through the door only while its own `build_parser` blocks still name them. `cli.py` keeps `_flows_for` and `_dispatch_argv` under their names, because tests import them from `isekai.interface.cli`.

Every other name that crosses a module is public:

| before | after | module |
|---|---|---|
| the reporter class, `_say` | `Reporter`, `say` | `common.py` |
| `_once`, `_run_for`, `_named`, the tracked-file check, the cell parser | `once`, `run_for`, `run_or_photo`, `require_tracked`, `parse_cells` | `common.py` |
| `_import`, the staged-line helper | `run_import`, `staged_line` | `library.py` |
| the `write_page` branch of `dispatch` | `run_compare` | `library.py` |
| `_ui` | `run_ui` | `library.py` |
| `_draft`, `_discard` | `run_draft`, `run_discard` | `drafts.py` |
| `_ink`, `_edit`, `_pending` | `run_ink`, `run_edit`, `run_pending` | `edits.py` |
| `_prepare` | `run_prepare` | `prepare.py` |
| the generate handler | `generate_batch` | `generate.py` |
| a verb's blocks of `build_parser` | `<verb>_arguments`, as [D2](#d2) says | the verb's family module |

The handler a row's run is takes `(args, wired)` and returns the exit status, so a run has one shape. `run_draft` and `run_discard` read `args.target`, `args.images` and `args.image` in their first lines, where `dispatch` passes them today, and their bodies are otherwise verbatim. `run_prepare` also takes `per_item`, and `generate_batch` keeps the `(args, wired, targets, flows)` of the handler it replaces, because `dispatch`'s tail calls it.

The shared argument helpers are added to `common.py` when a family first needs them: `photographs` adds `photos` and `--runs`, `required_flow` and `hidden_flow` add `--flow`, and `progress_flag` and `new_version_flag` add the flags of those names, each with the text it has today.

### D5

A moving phase opens with `uv run python -m tools.mutate <path:lo-hi> … --tests <files>` over the lines it moves, and closes with the same run over the new module. The lines are read at the phase's start from `grep -n -E '^(def|class) ' isekai/interface/cli.py`, as each function's first line to the line before the next definition; a family's blocks of `build_parser` are ranges of that function. A new module is staged with `git add` before its run, because the tool reads tracked files.

The opening runs of phases 2 and 3 are checked by the tests' baseline alone, because no range holds once phase 1 has shifted the file; the closing run covers the same mutants on the new module, so a survivor the opening misses fails there.

A survivor is killed by a new step in an existing test that reaches `dispatch` or `main` and binds the scenario that already requires the behaviour. A survivor no test can kill is equivalent only when this decision names it, and one it does not name halts the build as a plan problem. A closing run leaves out the line of a named survivor, and no other line.

| module | line | mutant | equivalent because |
|---|---|---|---|
| `isekai/interface/verbs/drafts.py` | 36 | `zip(located, answers, strict=True)` → `strict=False` | `refuse_image_drafts` returns `refuse_drafts`' list, which holds one answer per selected image on every path, so `located` and `answers` never differ in length; only a patch of `refuse_image_drafts` could make them, and the patch ratchet refuses one |

| family | tests that reach it |
|---|---|
| the shared module | `tests/test_pipeline_cli.py`, `tests/test_progress.py`, `tests/test_assign.py`, `tests/test_render.py`, `tests/test_ink.py` |
| `library.py` | `tests/test_importing.py`, `tests/test_compare.py`, `tests/test_pipeline_cli.py`, `tests/test_record.py` |
| `drafts.py` | `tests/test_pipeline_cli.py`, `tests/test_review.py`, `tests/test_edit_session.py`, `tests/test_record.py` |
| `edits.py` | `tests/test_ink.py`, `tests/test_edit.py`, `tests/test_edit_session.py`, `tests/test_record.py` |
| `session.py` | `tests/test_render.py`, `tests/test_pipeline_cli.py`, `tests/test_record.py` |
| `prepare.py` | `tests/test_pipeline_cli.py`, `tests/test_resume.py`, `tests/test_record.py` |
| `generate.py` | `tests/test_generate.py`, `tests/test_resume.py`, `tests/test_record.py` |

The record is in each family's list because it alone pins the arguments' defaults, choices and order, which are the statements those blocks hold.

### D6

These entries of `tests/mutants.json` change their `path` and nothing else.

| finding | now | after |
|---|---|---|
| `CL-10` | `isekai/interface/cli.py` | `isekai/interface/verbs/common.py` |
| `PA-4` | `isekai/interface/cli.py` | `isekai/interface/verbs/generate.py` |
| `PB-6`, `PB-16` | `isekai/interface/cli.py` | `isekai/interface/verbs/edits.py` |

`CL-7` and `PB-2b` stay in `cli.py`. The line `dest="verb", metavar="verb", required=True, parser_class=_Verb` stays byte for byte in `build_parser`, and `definition=flows[name],` in `_per_item`. The replay `uv run python -m tools.mutate --edits tests/mutants.json` proves each.

### D7

A listed offender may grow, and a row whose offender no longer offends is red until it is removed. The rows of the file and of `build_parser` go in the phase whose move takes the offender under its ceiling, and both are gone when the last phase ends. The rows of `_per_item` and its `work` stay.

When `tests/test_ratchets.py` names `no longer offends` for the file's row or `build_parser`'s, the phase removes that row and lowers the matching `*_ROWS` count. Any other fault of the ratchets halts the build. Every new module and function stays under the ceilings, with no listed row of its own.

### D8

`docs/decisions.md` gains `D58 · A verb is declared once, in its family's module`, after D56. It says a verb is one row of its family's module and `cli.py` assembles and dispatches, and it accepts that `render`, `prepare` and `migrate` are bound in `cli.py` until `_per_item` leaves it.

The documents the move makes false are amended in the last phase, and so is each docstring and comment, in `cli.py` and in the package, that names a moved definition by its old name, such as `_ui`, `_pending` and `_run_for`:

| document | what changes |
|---|---|
| `isekai/interface/cli.py` | the module docstring names the package and says what stays |
| `isekai/interface/README.md` | the files table, the lazy-import note and the sibling note |
| `ARCHITECTURE.md` | the `interface` bullet |
| `isekai/README.md` | the interface row of the layer table and the line naming the sub-packages' front doors |
| `docs/modules.md` | the lazy edge, the verbs' pieces, the graph and the component notes |
| `docs/principles.md` | the known breaks that name `_once` and `_discard` |

The layer READMEs' `## Imported by` tables are re-derived at the end of every phase by `uv run python -m tools.derive_imported_by`.

### D9

No requirement changes: the verbs, their arguments, their lines and their exit codes are the same. The change carries `skip_specs: true` and an empty `specs/`. No format version moves, no flow is re-pinned, and `config/models.json`, `isekai/boundary/provision.py` and `isekai/boundary/pod_start.py` stay byte-identical.

## Tests

This change adds no test and removes none, and adds no end-to-end run. A survivor of a pre-flight adds a step to an existing test, per [D5](#d5).

| measure | command | holds |
|---|---|---|
| tests added or removed | `git diff --name-status 0176ee35 -- tests` | `M` lines only, no `A` and no `D` |

The record `tests/record/verbs.json` is the one reader of the pinned names `_seed`, `_session_id`, `_depth` and `_Targets`, and it stays byte-identical. The helpers of other test files that share a spelling with a moved name read nothing from `cli.py`.

It edits the `cli.py` rows of `tests/test_ratchets.py` and their counts, and the paths of the moved entries of `tests/mutants.json`. The proofs it keeps green are `tests/test_record.py`, `tests/test_layers.py`, `tests/test_docs.py`, `tests/test_migrate.py` and `tests/test_pipeline_cli.py`, whose `-S` guard holds the entry point's import graph.

## Dependencies

None.

## Risks / Trade-offs

- A patch of a moved name could pass silently once the reading code moves. The pre-flight is the measure, and the patch ratchet fails on a stranded patch.
- The front door of the first phase re-exports the argument types for `cli.py`'s own blocks. The last of them leaves with the last block that names it.
- An argument added in another order passes every test but the record, which is why `tests/test_record.py` ends every phase.
- The rows of `render`, `prepare` and `migrate` carry a run bound in `cli.py` until `_per_item` leaves it. [D3](#d3) records this, and [D8](#d8) accepts it in the decision.

## Verdict

Feasible. Every fact the plan reads was placed at `HEAD`, and each move is held by the record, the layer guards, the ratchets, the docs tests and the pre-flights.
