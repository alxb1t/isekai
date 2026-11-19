# The wire derived — design

`tools/derive_wire.py` reads `shapes.py` by `ast` and writes `ui/src/wire.ts`; a test re-derives it. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

[D63](../../../docs/decisions.md#d63--the-wire-is-declared-in-shapespy-and-held-by-tests), [D64](../../../docs/decisions.md#d64--the-answers-the-record-lacks-are-a-second-table-held-by-cases-that-ask-the-server) and [D66](../../../docs/decisions.md#d66--the-refusals-are-classes-and-the-streams-events-have-a-table-of-their-own) declare the server's answers in `isekai/interface/ui/shapes.py`: classes, the tables `ANSWERS`, `UNRECORDED` and `EVENTS`, and aliases and classes imported from other modules. The page's `ui/src/types.ts` is still written by hand. This version sits between `the-wire-states`, which named the value sets in Python, and `the-page-wire`, which makes the page read the derived file.

The principle in `docs/principles.md` says a derived file is held by a test that re-derives it and expects the same bytes. `tools/` may import nothing under `isekai/interface/ui/`, and any `isekai` import moves an *Imported by* table, so the tool imports no `isekai` module. `ui/src` files are held to 600 lines, a generated one too, and the page's ratchet table is empty, so no row may be added.

```
isekai/interface/ui/shapes.py ──ast──▶ tools/derive_wire.py ──▶ ui/src/wire.ts
   │ imports, followed by path              derive(root) → text        │
   ▼                                        main() writes the file     ▼
jobs.py library.py importing.py …                          tests/test_derive_wire.py
review.py tattoos.py proposal.py artifacts.py              re-derives it, byte for byte
```

## Goals / Non-Goals

- Goals: the tool and its grammar with a twin for each form; the file as the tool writes it, held byte for byte; the events map held to `EVENTS`; `make derive` runs the tool; the decision and the documents.
- Non-goals: the page reads nothing of it; no vitest case; no doc comment in the file; no file under `isekai/` changes; no row of the page's ratchet. See [proposal](proposal.md#not-in-this-change).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the tool reads `shapes.py` and the modules it imports by `ast` alone, and imports no `isekai` module | `tools/` may not import the UI package, and an import moves an *Imported by* table (Q188) | importing `shapes` and walking `get_type_hints`, as `tests/test_ui_shapes.py` does |
| [D2](#d2) | the grammar is the table below; a form outside it is refused naming the class and the field | the file is a copy, so a form it cannot write must stop the tool, not be guessed (Q188) | writing `unknown` for a form it does not know |
| [D3](#d3) | a class keeps Python's name; an imported alias is its module's name then its own; a name written twice is refused | Python has two `Kind`s and the page a `Kind` and a `Side` of its own (Q189) | Python's bare name for an alias |
| [D4](#d4) | the file is a header, the aliases, the foreign classes, `shapes.py`'s classes in source order, then `Events` | a reader finds a name where the order says, and a re-derive is the same bytes (Q191) | grouping by table |
| [D5](#d5) | one test file holds the grammar over trees of its own, the committed file, and the events' keys; each carries a `structural:` exemption | no requirement fits a tool, and a vitest case has no exempt form (Q186) | a scenario under the `ui` spec |
| [D6](#d6) | `make derive` runs the tool, and a decision records the rule | a derived file is re-derived with its siblings; a rule gets a decision | adding the tool to `make drift`, which fetches |

### D1

The tool imports the standard library alone. It follows `shapes.py`'s imports by path under the root it is given: `from isekai.interface.ui import jobs` names `isekai/interface/ui/jobs.py`, and `from isekai.pipeline.review import Status` names `Status` in `isekai/pipeline/review.py`. `derive(root)` reads `root / "isekai/interface/ui/shapes.py"`, so a test builds a small tree of its own.

### D2

Each row is a form `shapes.py` uses today. The tool reads the annotations of a class body and the bases of a class; every other module-level name is ignored but `EVENTS`.

| Python | `wire.ts` |
|---|---|
| `str`, `int`, `float`, `bool` | `string`, `number`, `number`, `boolean` |
| `T \| None`, and `None` alone | `T \| null`, and `null`; a union of arms that are not `None` is refused |
| `list[T]` | `T[]`, and `(A \| B)[]` when `T` is a union |
| `dict[str, T]` | `Record<string, T>` |
| `dict[A, T]`, `A` an alias | `Record<A, T>` |
| `NotRequired[T]` | `name?: T` |
| `Literal["a", "b"]` | `'a' \| 'b'` |
| a class of `shapes.py`, or `mod.Class` | the class's name |
| a name imported from a module, or `mod.Name`, an alias | the alias, named as [D3](#d3) says |
| `class X(Base)`, `Base` in the module or `mod.Base` | `interface X extends Base` |
| a class holding a docstring and no field | `type X = Record<string, never>` |

A literal word holding a quote or a backslash is refused. A class with a keyword (`total=False`), a field that is not a plain name, a functional `TypedDict`, an empty class with a base and an annotation that is a string are refused too.

The refusal is a `ValueError` reading `<Class>.<field>: <the source of the annotation> is no form of the wire`; a refusal of a class alone drops `.<field>`.

An alias is `Name = Literal[...]` at the top level of its module. Its items are words, or names of aliases of the same module: `importing.Upload` nests `State`, so `ImportingUpload` is `ImportingState | 'waiting' | 'converting' | 'refused'`.

### D3

| Python | `wire.ts` |
|---|---|
| a class of `shapes.py`, a class of `artifacts.py` | its own name: `SessionRecord`, `SchemaBlock`, `SessionImage`, `SessionPlan` |
| `Status` imported from `review` | `ReviewStatus` |
| `library.Stage`, `tattoos.Kind`, `proposal.Side`, `jobs.Kind`, `jobs.State`, `importing.Upload` | `LibraryStage`, `TattoosKind`, `ProposalSide`, `JobsKind`, `JobsState`, `ImportingUpload` |
| the alias `Upload` nests, `importing.State` | `ImportingState`, written under its own name and named in `ImportingUpload`'s union |

The rule is the module's name capitalised, then the alias's name. A class reached from another module is written once, and a name a second declaration would write is refused. The page's `Kind`, `Side` and `Stage` keep their names in `types.ts`; renaming them is out.

### D4

```
/* Written by `tools/derive_wire.py` from `isekai/interface/ui/shapes.py`. */

export type ImportingState = 'ready' | 'converted' | 'not cleaned' | 'skipped'
export type ImportingUpload = ImportingState | 'waiting' | 'converting' | 'refused'

export interface SchemaBlock {
  name: string
  version: number
}

export interface Events {
  snapshot: Snapshot
  job: Job
}
```

The aliases come sorted by their names, then the foreign classes sorted by theirs, then `shapes.py`'s classes in its order, then `Events`, one blank line between blocks. A field is one line with no doc comment. `Events` holds one line for each key of `EVENTS`, in its order, valued by the class the table names.

The file is held under 600 lines by the page's ratchet; the estimate is about 530, from the classes and fields counted below. A file past 600 is a re-plan that splits it by table, never a row in the ratchet.

### D5

Each case builds its tree under `tmp_path` with `_tree(root, files)`, `files` mapping a path relative to `root` to its text: `isekai/interface/ui/shapes.py` and the modules it imports, at the paths `from isekai.… import` names. A case asserts the text the tool writes for one form of [D2](#d2)'s table, or the refusal.

The committed-file case asserts `derive(REPO_ROOT)` equals `ui/src/wire.ts`. The events case reads the `Events` block of `ui/src/wire.ts` and asserts its keys equal `EVENTS`' keys, imported from `isekai.interface.ui.shapes`. A refusal case is parametrised over a union of arms that are not `None`, a tuple and a name that is no class or alias.

### D6

`make derive` runs `uv run python -m tools.derive_wire` after the importer tables, before `drift`. The acceptance runs the tool directly, because `drift` fetches from the network. A new decision, D67, records the rule and what the tool does not hold ([A7](../../../docs/decisions.md)).

## Tests

All new tests are unit tests of a stdlib tool over files, in `tests/test_derive_wire.py`; none is end-to-end, so no browser runs are added ([T1](../../../CONTRIBUTING.md)). No test is deleted or merged, so there is no mapping table. No assertion of an existing test changes.

| what | count | command |
|---|---|---|
| tests the change adds, unit | 16 | `grep -c -E "^def test_" tests/test_derive_wire.py` prints `16` |
| end-to-end runs the change adds | 0 | no browser test file is added or edited |
| classes of `shapes.py` the file writes | 68 | `git grep -c -E "^class " -- isekai/interface/ui/shapes.py` prints `isekai/interface/ui/shapes.py:68` |
| fields of `shapes.py` the file writes | 273 | `git grep -c -E "^    [a-z_0-9]+: " -- isekai/interface/ui/shapes.py` prints `isekai/interface/ui/shapes.py:273` |

The tests are the cases of [D5](#d5), each at the lowest layer that can fail for it, a call of `derive` over a small tree ([T1](../../../CONTRIBUTING.md)); each carries `@pytest.mark.spec_exempt("structural: …")`.

| test | proves |
|---|---|
| `test_the_leaves_and_none_are_written` | `str`, `int`, `float`, `bool` and `None` |
| `test_a_list_is_an_array` | `list[T]`, and a union inside it |
| `test_a_map_by_str_is_a_record_of_strings` | `dict[str, T]` |
| `test_a_map_by_an_alias_is_a_record_by_it` | `dict[A, T]` |
| `test_not_required_is_an_optional_field` | `NotRequired[T]` |
| `test_an_inline_literal_is_a_union_of_its_words` | `Literal[...]`, with `None` |
| `test_an_alias_imported_through_its_module_is_named_by_both` | `library.Stage` is `LibraryStage` |
| `test_an_alias_imported_by_its_own_name_is_named_by_its_module` | `Status` of `review` is `ReviewStatus` |
| `test_an_alias_that_nests_another_names_it` | `Upload` nests `State` |
| `test_a_base_in_the_module_is_extended` | `class X(Base)` of the module |
| `test_a_base_in_another_module_is_written_and_extended` | `mod.Base`, and the class its field names |
| `test_an_empty_class_is_a_record_of_nothing` | a class with a docstring alone |
| `test_the_events_map_follows_events` | `Events` in `EVENTS`' order |
| `test_a_form_outside_the_grammar_is_refused_naming_the_class_and_the_field` | the refusal's text |
| `tests/test_derive_wire.py::test_the_committed_wire_is_the_one_the_tool_writes` | `derive(REPO_ROOT)` equals `ui/src/wire.ts` |
| `test_the_events_keys_are_events_keys` | the file's `Events` keys equal `EVENTS`' |

The change moves no line of `isekai/` or `evaluation/`, so it has no mutation pre-flight ([CONTRIBUTING](../../../CONTRIBUTING.md)).

## Dependencies

None.

## Risks / Trade-offs

- A form `shapes.py` gains later that the grammar lacks fails the committed-file case with the tool's refusal; the author adds the form and its case. That is the cost of a copy held by a test.
- `ty` holds `shapes.py`'s Python; the tool holds the TypeScript it writes only as far as `vue-tsc` reads `wire.ts`, which no page file imports yet. `the-page-wire` is the first reader, so a type that is wrong but well-formed shows there.
- `wire.ts` is the first generated file under `ui/src`, held by the 600-line ratchet like any other. The size is estimated; the build measures it.

## Verdict

Feasible. Every form `shapes.py` uses is in the grammar, the tool needs no package, and no file under `isekai/` changes.
