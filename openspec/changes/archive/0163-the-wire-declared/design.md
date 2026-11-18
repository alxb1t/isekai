# The wire declared — design

The answers of the hub, staging, images, vocabulary and reviewing tables are declared as `TypedDict`s in one new module and held against the record by one new test; no handler, route or record entry changes. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Every route but the catch-alls is a row of a `ROUTES` table, added to the app by `register` in `isekai/interface/ui/routes/table.py`. No handler declares its answer: each is annotated `dict[str, Any]`, and `post_draft` `object`.

`tests/record/routes.json` holds, for each recorded route, a status and either a shape or a media type. A shape is keys and type names: `"str"`, `"int"`, `"float"`, `"bool"`, `"null"`, a list by its first element, an empty list or map as nothing (`shape` in `tests/record.py`). `recorded("routes")` reads it, keyed `"<METHOD> <path template>"`.

```
 routes/<table>.py  ROUTES ──▶ "GET /api/library"        ◀── the record's key
                                      │
 shapes.py          ANSWERS  ─────────┘──▶ LibraryInfo    ◀── a TypedDict
                                      │
 tests/test_ui_shapes.py  faults(LibraryInfo, record["GET /api/library"]["shape"]) == []
```

The page's `ui/src/types.ts` is written by hand. This change declares the server's side for the hub, staging, images, vocabulary and reviewing tables. A later version declares the rest and derives the page's types from `shapes.py`.

FastAPI infers a response model from a handler's return annotation, validates the answer against it and serialises it with pydantic. A handler left unannotated is serialised as it is today, so a declaration kept in `shapes.py` and never attached to a handler moves no byte ([D2](#d2)).

## Goals / Non-Goals

Goals:
- Each JSON answer of the hub, staging, images, vocabulary and reviewing tables has a declaration and a row in `ANSWERS`, each recorded with its success.
- A test holds each declaration against the record, and shows it refuses a wrong one.

Non-Goals:
- A handler's annotation, `response_model`, a route's row, a record entry, any file under `ui/src`.
- The tattoos', place and rendering tables, a refusal's shape and the stream's events.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the declarations are stdlib `TypedDict`s in `isekai/interface/ui/shapes.py`, `ANSWERS` keyed as the record is | a key the record already holds needs no second spelling; a `TypedDict` adds no package | pydantic models: it is locked only as FastAPI's dependency and imported nowhere |
| [D2](#d2) | no handler is annotated and no route passes `response_model`; the declarations are held by tests | an annotation makes FastAPI validate and serialise by the declared type, which can move a float's bytes or turn a missing key into a 500 | `response_model=None` in `register`: it moves every answer from pydantic's serialiser to `json.dumps` |
| [D3](#d3) | a value set already declared by name is imported, never restated; a set written inline in the code is written inline here and named in this design | a restated copy is a second fact that a test must hold equal | restating `Status` in `shapes.py` |
| [D4](#d4) | the walker is a pure function in the test file, proven first on small declarations of the test's own | a check that cannot fail proves nothing; the refusing cases show it can | testing the walker only through the real declarations |
| [D5](#d5) | the case over the tables reads each `ROUTES` table by import; it starts on the hub, staging and vocabulary tables and the images and reviewing tables join it | the tables are the one list of routes a resource declares, and a route added to a table with a recorded shape fails the case until it has a row | a route list written in the test |
| [D6](#d6) | what the record samples empty is declared from the builder's code, named here, and held by no test | the record cannot see an empty list or map; a test of it would need a second record | adding record entries: nothing under `tests/record/` changes |
| [D7](#d7) | the *Imported by* tables are derived in phase 2, not phase 4 | `shapes.py` imports `pipeline/review.py` in phase 2, which turns `tests/test_docs.py` red until the tables are derived | deriving in the last phase: phase 2 would end red |
| [D8](#d8) | D63 records the wire's home; the page's version adds its own id to it | a decision in force is edited where it lives | a decision per version |

### D1

`shapes.py` holds one `TypedDict` per answer and per nested object, a one-line docstring each (ruff `D` asks one of every public class), and `ANSWERS: dict[str, Any]`. A key is written `f"<METHOD> {PATH}"`, the path a module constant, as `tests/record.py` writes `REVIEW` and `RENDER`.

The module imports no web framework, so the layer's entry point and its tests read it whether or not a server is installed. It stays under the file-length ratchet, which no row may be added to.

A required key is a plain field. A key a builder may leave out is `NotRequired`; none of the answers below has one.

### D2

Nothing attaches a declaration to a handler. The annotations of these tables' handlers, `register` in `routes/table.py` and every route's row stay as they are, so no answer's bytes can move, and the acceptance holds `git grep -n response_model -- isekai` to nothing.

D63 records the rule, so a later version that annotates a handler reads why it must also pass `response_model=None`.

### D3

Of these tables' answers only one value set is declared by name: `review.Status`, which `HubCell.status` imports. These sets are written inline in the code and inline here:

| set | where the code writes it | where it is declared here |
|---|---|---|
| `"baked"`, `"queued"`, `"damaged"` | `Bake.state` of `isekai/interface/ui/library.py` | `Bake.state` |
| `"revision"`, `"re-roll"` | `Version.kind` of `isekai/interface/ui/library.py` | `RenderDetail.kind` |
| `"waiting"` | `Reader.put` of `isekai/pipeline/importing.py` | `Uploaded.state` |

`importing.State` is not the upload's state: it names a file the reader has finished with, and the put answers before it has.

### D4

`faults(declared, sampled, at)` returns a line for each way a recorded shape disagrees with a declaration, and `[]` when it fits.

| declared | the sampled shape fits when |
|---|---|
| a `TypedDict` | it is a map, each key is declared, each required key is present and each value fits its field |
| `dict[str, X]` | it is a map and each value fits `X`; `{}` fits |
| `list[X]` | it is `[]` or a list of one that fits `X` |
| `X \| None` | it is `"null"`, or fits `X` |
| `Literal[…]` | it is the type name of a value of the set, `"str"` for a set of strings |
| `str`, `int`, `float`, `bool` | it is that name |

A line reads `<at>: <what>`, `at` the path from the answer's root, e.g. `sources[0].cells.*.stage: "int" is not a str`. The walker cannot see key order, a list's later elements or what an empty list or map would hold ([D6](#d6)).

The refusing cases are: a key the declaration lacks, a required key the sample lacks, and a leaf of the wrong name. Each runs on a declaration the test writes, so the walker is proven before `shapes.py` exists.

### D5

The case reads `ROUTES` from `isekai.interface.ui.routes.hub`, `.staging` and `.vocabulary` in phase 2, and `.images` and `.reviewing` in phase 3. `tests/` is outside the front-door scope of `tests/test_layers.py`, so a test may import them.

The cases check that:
- every `ANSWERS` key is a recorded entry with a shape, and its declaration fits that shape;
- every route of these tables whose recorded entry has a shape has a row in `ANSWERS`.


A route recorded as a media type, a file, has no row. The routes of the other tables have no row yet.

### D6

Parts the record samples as `[]` or `{}`, or only as `"null"`, are declared from the builder:

| answer | part | declared as | from |
|---|---|---|---|
| `HubSource` | `carries` | `list[str]` | `Source.carries` is `tuple[str, ...]`, `_hub` lists it |
| `Assigned` | `refused` | `dict[str, str]` | `post_assign` fills `refused: dict[str, str]` |
| `Committed` | `skipped`, `left_out` | `list[str]` | `Committed` of `importing.py` holds tuples of names, `post_commit` lists them |
| `Approval` | `warnings` | `list[str]` | `approve` returns `tuple[Path \| None, list[str]]` |
| `RenderDetail` | `fields` | `dict[str, list[str]]` | `_filled` returns the fields that hold a tag |
| `RenderDetail` | `seeds` | `list[str]` | `_decimal` of the version's seeds |
| `Renders` | `seeds` | `list[str]` | `_renders_out` writes each seed as a decimal string |
| `InputDetail` | `fields` values | `list[str]` | `_fields` refuses a value that is no list of tags |
| `InputDetail` | `revision`, `drafted`, `caption`, `caption_command`, `cancel`, `draft`, `approved`, `saved`, `approved_at` | the type or `None` | the `None` branches of `read_input` |
| `HubCell` | `refusal`, `short`, `newest`, `status` | the type or `None` | `Cell` of `library.py` |
| `CompareSide` | `left` of the photograph's compare | `CompareSide \| None` | `read_compare_photo` answers `None` |
| `DraftedImage` | `draft`, `waiting` | `str \| None` | `post_draft` writes `None` and fills one |

### D7

Phase 2 runs `uv run python -m tools.derive_imported_by`. The row of `review.py` in `isekai/pipeline/README.md` gains `interface/ui/shapes.py`. `make derive` also runs the fetched-file deriver, which needs the network, so the task runs only the importers' tool.

### D8

D63 is the next free decision. Its text, in the shape of D62, is a bold rule and then bullets.

The rule, in bold: **each JSON answer of the UI server is a `TypedDict` in `isekai/interface/ui/shapes.py`; `ANSWERS` maps `"<METHOD> <path template>"`, as `tests/record/routes.json` keys it, to the answer's declaration; `tests/test_ui_shapes.py` holds each against its recorded shape; a handler keeps its annotation and no route passes `response_model`.**

- **Why:** the page's types were written by hand beside the server and drifted; one declaration in Python is a fact a test can hold the server to. FastAPI would validate and serialise an answer by a declared type, so a declaration stays apart from the handlers.
- **Accepts:** the tattoos', place and rendering tables are declared by the next version, and the page's types are derived from the declarations after it. Reopen when a handler is annotated with a declared type.
- **Made by:** `0163`.

## Declarations

One class per row; a field is `name: type`, `T | None` a `T` or `None`. Each class is a `TypedDict` with a one-line docstring.

| class | fields | built at |
|---|---|---|
| `FlowCount` | `flow: str`, `approved: int`, `rendered: int`, `of: int` | `FlowCount` of `library.py` |
| `LibraryRow` | `name: str`, `collection: bool`, `sources: int`, `thumbs: list[str]`, `flows: list[FlowCount]`, `without_flow: int`, `newest: float \| None`, `kind: str \| None` | `Row` of `library.py`, by `asdict` |
| `LibraryInfo` | `rows: list[LibraryRow]` | `HubRoutes.read_library` |
| `CellImage` | `version: int`, `seed: str` | `_cell_out` in `routes/common.py` |
| `HubCell` | `stage: str \| None`, `renders: int`, `refusal: str \| None`, `status: Status \| None`, `newest: CellImage \| None`, `short: int \| None`, `images: list[CellImage]` | `_cell_out` |
| `HubSource` | `name: str`, `digest: str \| None`, `width: int \| None`, `height: int \| None`, `cells: dict[str, HubCell]`, `carries: list[str]` | `_hub` |
| `HubInfo` | `collection: str`, `flows: list[str]`, `sources: list[HubSource]` | `_hub`, `HubRoutes.read_hub` |
| `Assigned` | `cells: dict[str, HubCell]`, `refused: dict[str, str]` | `HubRoutes.post_assign` |
| `Opened` | `id: str` | `StagingRoutes.post_staging` |
| `Uploaded` | `upload: str`, `file: str`, `state: Literal["waiting"]` | `Reader.put` |
| `Empty` | no field | `delete_staged` and `delete_staging` |
| `Committed` | `collection: str`, `written: list[str]`, `skipped: list[str]`, `left_out: list[str]` | `StagingRoutes.post_commit` |
| `TagMatch` | `tag: str`, `posts: int`, `rare: bool` | `VocabularyRoutes.read_tags` |
| `TagMatches` | `matches: list[TagMatch]`, `total: int` | `read_tags` |
| `OfferedTag` | `tag: str`, `posts: int` | `_Shared.candidates` of `surface.py` |
| `FieldCandidates` | `fields: dict[str, list[OfferedTag]]` | `_Shared.candidates` |
| `Renders` | `count: int`, `seeds: list[str]` | `_renders_out` |
| `Bake` | `k: int`, `placed_on: int \| None`, `baked_at: float \| None`, `edit: str \| None`, `state: Literal["baked", "queued", "damaged"]`, `reason: str \| None` | `Bake` of `library.py`, by `asdict` |
| `SourceImages` | `flow: str`, `images: list[CellImage]` | `_images_out` in `routes/images.py` |
| `RenderDetail` | `flow: str`, `version: int`, `seed: str`, `fields: dict[str, list[str]]`, `approved_at: float \| None`, `came_from: int \| None`, `kind: Literal["revision", "re-roll"] \| None`, `count: int \| None`, `seeds: list[str]`, `damaged: str \| None`, `bakes: list[Bake]`, `compare: int \| None`, `targets: list[str]`, `source: list[SourceImages]` | `ImageRoutes.read_render` |
| `CompareSide` | `flow: str`, `version: int`, `approved_at: float \| None`, `renders: Renders`, `tokens: int`, `seed: str` | `_side` and `read_compare` |
| `Comparison` | `left: CompareSide \| None`, `right: CompareSide` | `read_compare`, `read_compare_photo` |
| `Deleted` | `deleted: bool` | `ImageRoutes.delete_render` |
| `Budget` | `total: int`, `per_field: dict[str, int]`, `overhead: int`, `window: int` | `_budget` in `routes/reviewing.py` |
| `ScoredTag` | `tag: str`, `confidence: float` | `_wd14` |
| `Revision` | `version: int`, `seed: str \| None`, `fields: dict[str, list[str]]` | `_revision` |
| `Drafted` | `fields: dict[str, list[str]]`, `version: int` | `_drafted` |
| `InputDetail` | `id: str`, `run: str`, `flow: str`, `schema: list[str]`, `vocabulary: int`, `width: int`, `height: int`, `caption: str \| None`, `caption_command: str \| None`, `wd14: list[ScoredTag] \| None`, `tags: list[OfferedTag] \| None`, `fields: dict[str, list[str]]`, `renders: Renders`, `revision: Revision \| None`, `drafted: Drafted \| None`, `readonly: bool`, `draft: str \| None`, `approved: str \| None`, `saved: float \| None`, `approved_at: float \| None`, `cancel: str \| None`, `budget: Budget` | `ReviewRoutes.read_input` |
| `DraftSaved` | `draft: str`, `saved: float`, `budget: Budget` | `ReviewRoutes.put_draft` |
| `Approval` | `approved: str \| None`, `warnings: list[str]`, `at: float \| None` | `ReviewRoutes.post_approve` |
| `Cancellation` | `back: str \| None`, `cancelled: bool` | `ReviewRoutes.post_cancel` |
| `Discarded` | `discarded: str` | `ReviewRoutes.post_discard` |
| `DraftedImage` | `digest: str`, `flow: str`, `version: int`, `seed: str`, `draft: str \| None`, `waiting: str \| None` | `ReviewRoutes.post_draft` |
| `Drafts` | `drafts: list[DraftedImage]` | `post_draft`'s answer of `200` |

`ANSWERS` keys, in the order of the tables:

| table | key | declaration |
|---|---|---|
| hub | `GET /api/library` | `LibraryInfo` |
| hub | `GET /api/c/{collection}/hub` | `HubInfo` |
| hub | `POST /api/c/{collection}/assign` | `Assigned` |
| staging | `POST /api/staging` | `Opened` |
| staging | `PUT /api/staging/{staged}/files/{name}` | `Uploaded` |
| staging | `DELETE /api/staging/{staged}/files/{name}` | `Empty` |
| staging | `DELETE /api/staging/{staged}` | `Empty` |
| staging | `POST /api/staging/{staged}/commit` | `Committed` |
| vocabulary | `GET /api/tags` | `TagMatches` |
| vocabulary | `GET /api/fields` | `FieldCandidates` |
| images | `GET /api/c/{collection}/renders/{digest}/{flow}/{version}/{seed}` | `RenderDetail` |
| images | the same path with `/compare/{other_flow}/{other_version}/{other_seed}` | `Comparison` |
| images | the same path with `/compare/photo` | `Comparison` |
| images | the same path with `/edit/{k}` | `Bake` |
| images | `DELETE` of the render's path | `Deleted` |
| reviewing | `GET /api/c/{collection}/review/{digest}/{flow}` | `InputDetail` |
| reviewing | `PUT` of the same path with `/draft` | `DraftSaved` |
| reviewing | `POST` of the same path with `/approve` | `Approval` |
| reviewing | `POST` of the same path with `/cancel` | `Cancellation` |
| reviewing | `POST` of the same path with `/discard` | `Discarded` |
| reviewing | `POST /api/c/{collection}/draft` | `Drafts` |

The draft route's `409` answer, `{refusal, images}`, has no row: the record holds its `200` alone.

## Tests

Added, all unit, all in `tests/test_ui_shapes.py`; removed: none.

| test | layer | binds |
|---|---|---|
| `test_the_walker_accepts_what_a_declaration_allows` | unit | `spec_exempt("structural: …")` |
| `test_the_walker_refuses_an_undeclared_key`, `…_a_missing_required_key`, `…_a_wrong_leaf` | unit | `spec_exempt("structural: twin of test_the_walker_accepts_what_a_declaration_allows")` |
| `test_every_answer_fits_the_record` | unit | `spec_exempt("structural: …")` |
| `test_every_recorded_shape_of_the_tables_has_a_row` | unit | `spec_exempt("structural: …")` |

`uv run pytest tests/test_ui_shapes.py --collect-only -q` prints `6 tests collected` after phase 3, and `4 tests collected` after phase 1. No end-to-end test is added: no browser engine shows what a key set holds (T1). The record's own test already runs the pass; this test reads the committed file through `recorded("routes")` and runs none.

The refusing cases are the twins of the accepting case, at the lowest layer (T6). The change deletes and merges no test, so there is no table of removed tests.

## Dependencies

None.

## Risks / Trade-offs

- **A declaration the record cannot check.** [D6](#d6) names each; a builder's later edit can leave one stale and no test says so. The version that derives the page's types reads these, and the page's typecheck is the next check.
- **A class per nested object grows `shapes.py`.** At this size it is well under the ratchet's limit; the next version adds the rest and the ratchet is the limit.
- **A key a builder adds later.** The case fails on the sampled key the declaration lacks, so the declaration is edited with the builder.
- **The walker is strict on `float`.** A float field a builder fills with a whole number would sample `"int"` and fail; none of these answers does.

## Verdict

Feasible. Every file and symbol this design names exists at the base, apart from the files it adds: `isekai/interface/ui/shapes.py` and `tests/test_ui_shapes.py`.
