# The wire, rendering — design

This change declares the tattoos', place and rendering answers in `shapes.py` and holds them by the record and by cases that ask the server. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

[D63](../../../docs/decisions.md#d63--the-wire-is-declared-in-shapespy-and-held-by-tests) put each JSON answer of the UI server in `isekai/interface/ui/shapes.py`, keyed in `ANSWERS` as `tests/record/routes.json` keys its route. `tests/test_ui_shapes.py` holds each row against the shape the record holds for it. The hub, staging, images, vocabulary and reviewing tables are declared.

The tattoos', place and rendering tables are not declared. The record holds a success for most of their routes and none for prepare, render, the running sessions and a session; it holds stop and propose as a refusal alone. A row of `ANSWERS` for those fails the shipped case, whose assertions do not change.

```
 shapes.py   ANSWERS      ──▶ recorded success  ◀── tests/record/routes.json   held by test_ui_shapes.py
             UNRECORDED   ──▶ a TestClient asks ◀── a fixture beside each case  held by one case each
```

## Goals / Non-Goals

Goals: every JSON route of the tattoos', place and rendering tables has a declaration, and a test holds it. `shapes.py` stays at or under `FILE_LINES`. No answer's bytes change.

Non-goals: a handler, a route table, a record entry, `app.py`, `jobs.py` and `ui/src` are not touched. The refusals, the stream's events and the tests' imports from `app.py` are the next version's.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | the answers with no recorded success are rows of `UNRECORDED`, a second table in `shapes.py` whose keys are disjoint from `ANSWERS` | the shipped case asserts each key of `ANSWERS` is a recorded entry that the declaration fits; a new record entry and a changed assertion are out | rows in `ANSWERS`; a union row, which the walker refuses |
| [D2](#d2) | no handler's annotation, no `response_model`, no route row changes | a declared annotation moves every JSON answer to pydantic's serialiser; unannotated, no byte can change | annotating the handlers |
| [D3](#d3) | each row of `UNRECORDED` is held by one case that asks a `TestClient` and walks `shape` of the body with `faults`; the job's answers come through a `Jobs` subclass passed as `make_jobs` | a duck-typed stand-in would hold the stand-in's answer, and a patch of `Jobs` is a ratchet row | a monkeypatch; a real child for each |
| [D4](#d4) | the served session is its own `TypedDict`, `ServedSession`, with `outcome: str \| None`; a test holds its keys, required keys and every other field's type equal to `SessionRecord`'s; the running sessions' answer subclasses `SessionRecord` and adds `collection` | `SessionRecord.outcome` is `str`, and the server sends `null` for a record no process holds | reusing `SessionRecord` as is; a subclass that redeclares `outcome` |
| [D5](#d5) | a value set with a name is imported: `tattoos.Kind`, `jobs.Kind`, `proposal.Side`; the job's state and the billing volume's state, which have none, are `str` | a restated copy is a second fact; the walker reads a `Literal`'s type names, never its values, so an inline `Literal` is a claim no test holds | an inline `Literal` for each |
| [D6](#d6) | what the record samples empty is declared from the builder's code and held by no test | a list with no element and a map with no key are shapes the walker never sees | a test of what the record samples empty |
| [D7](#d7) | a pair, a point and a size are `list[...]`; the job's `progress`, `collections` and `session` are `NotRequired`; a number an answer echoes from its request is declared as the builder types it | the walker reads no tuple, and a key a job may lack must be optional | `tuple` |
| [D8](#d8) | the *Imported by* tables are derived in the phase that first imports a module: phase 1 for `tattoos.py` and `proposal.py`, phase 2 for `artifacts.py` | each import turns `tests/test_docs.py` red until the tables are derived, and a phase ends green | deriving in the last phase |
| [D9](#d9) | one case reads the routes of the tattoos', place and rendering tables, leaves out each the record holds as a media type, and holds each to a row in exactly one of `ANSWERS` and `UNRECORDED`; the shipped case's tables stay as they are | widening those tables would demand rows for stop and propose, and a row of `ANSWERS` for either fails the shipped case | widening the shipped case's tables |
| [D10](#d10) | D64 records the second table and what holds it, and D63's *Accepts* line is amended to what remains | a decision in force is edited where it lives, in `docs/decisions.md` | none |

### D1

`UNRECORDED: dict[str, Any]` is keyed as `ANSWERS` is, `"<METHOD> <path template>"`. Its keys are disjoint from `ANSWERS`' keys, and a case in phase 3 holds that ([D9](#d9)).

### D2

The change adds no import to a handler and reads no declaration from one. D63 already says a handler keeps its annotation.

### D3

Each case builds an app with `create_app`, asks the route, and asserts `faults(UNRECORDED[key], shape(answer.json()), "") == []`. `shape` is `tests.record.shape`; `faults` is `tests.test_ui_shapes.faults`.

The answers of prepare, render and stop need a job in its slot and no thread. A subclass of `Jobs` overrides `_occupy` to put the job in its slot and start nothing, and the app takes it as `make_jobs`. If `ty` rejects the override, the cases of prepare, render and stop reach the job through a real child, as `tests/test_ui_jobs.py`'s `_held_client` does.

### D4

`ServedSession` restates `SessionRecord`'s fields in its order, each field's type the record's own object (`artifacts.SchemaBlock`, `artifacts.SessionPlan`, `artifacts.SessionImage`), and `outcome: str | None`. The test compares `get_type_hints`, `__required_keys__` and `__optional_keys__` of the two, and asserts the one difference is `outcome`.

`RunningSession(SessionRecord)` adds `collection: str`. The route lists only a record whose `outcome` is `running`, so `str` holds there.

### D5

The value sets imported from below the layer are `tattoos.Kind` and `proposal.Side`; `jobs.Kind` is in the same layer. `importing.State` and the file's state belong to the next version. Propose's `arm` is `proposal.Side | None`, a named set, so it is imported.

### D6

Each is named in [What the record samples empty](#what-the-record-samples-empty).

### D7

`Tattoo.size`, `Tattoo.downscaled_from`, a point of an outline and a pair of a proposal are `list[int]` or `list[float]` as the builder types them. A job's `progress` is present for every prepare and no render; `collections` and `session` only for a render.

### D8

`uv run python -m tools.derive_imported_by` writes the tables. `make derive` also runs the fetched-file deriver, which needs the network, so no task runs it.

### D9

The routes are the `ROUTES` tuples of `routes/tattoos.py`, `routes/place.py` and `routes/rendering.py`, each a `Route(method, path, handler)`. The key is `f"{route.method} {route.path}"`. A route is left out when its record entry holds a `media_type`: the tattoo's design, the ink view and the preview.

### D10

D64 is the next free decision. D63's *Accepts* line says "the tattoos', place and rendering tables are declared by the next version"; after this change it names the refusals, the stream's events and the tests' imports.

## The declarations

Class names are the build's to keep. A field is `name type`; `X | None` is nullable; `NR` is `NotRequired`. A class is one `TypedDict` with a one-line docstring, as the file's others are.

Phase 1 — tattoos and place:

| class | answers | fields |
|---|---|---|
| `Tattoo` | `POST /api/tattoos`, `POST /api/c/{collection}/tattoos` | `name str` · `kind tattoos.Kind` · `size list[int]` · `kept str` · `outlined bool` · `downscaled_from list[int] \| None` · `cut_from str \| None` |
| `OutlinedTattoo(Tattoo)` | `GET /api/tattoos/{name}` | `outline Outline` |
| `TattooLimits` | `limits` of the list | the ints `long_side` `outline_min` `outline_max` `floor_stage1` `floor_stage2` `floor_direct` `preview_floor` `preview_margin` `preview_wait_ms` `pair_radius` `region_min`; the floats `depth_min` `depth_max` `photo_depth` `image_depth` |
| `Stage1` | `GET` and `PUT /api/tattoos/{name}/stage1/{digest}` | `pairs list[list[list[float]]]` · `not_on_photo bool` |
| `Tattoos` | `GET /api/tattoos` | `tattoos list[Tattoo]` · `limits TattooLimits` · `stage1 dict[str, Stage1]` |
| `Outline` | `PUT /api/tattoos/{name}/outline` | `points list[list[float]]` · `closed bool` · `white float` · `neutral bool` · `depth float` |
| `BakeQueued` | `POST /api/c/{collection}/tattoos/{name}/bake` | `edit int` |
| `Proposed` | `POST /api/c/{collection}/place/propose`, in `UNRECORDED` | `arm proposal.Side \| None` · `pairs list[list[list[float]]]` |

`DELETE /api/tattoos/{name}` answers `Empty`, which the file already declares.

The rows of `ANSWERS` for phase 1, as written in the file:

```
    "GET /api/tattoos": Tattoos,
    f"GET {TATTOO}": OutlinedTattoo,
    f"DELETE {TATTOO}": Empty,
    "POST /api/tattoos": Tattoo,
    f"POST {COLLECTION}/tattoos": Tattoo,
    f"PUT {TATTOO}/outline": Outline,
    f"GET {STAGE1}": Stage1,
    f"PUT {STAGE1}": Stage1,
    f"POST {COLLECTION}/tattoos/{{name}}/bake": BakeQueued,
```

`TATTOO` is `"/api/tattoos/{name}"` and `STAGE1` is `"/api/tattoos/{name}/stage1/{digest}"`, constants beside the file's others. The row of `UNRECORDED` is `f"POST {COLLECTION}/place/propose": Proposed`.

Phase 2 — rendering:

| class | answers | fields |
|---|---|---|
| `RenderOffer` | `GET /api/c/{collection}/render` | `disabled str \| None` · `images int` · `others int` · `bakes int` · `other_bakes int` · `refused str \| None` |
| `QuotedSource` | in `QuotedFlow` | `name str` · `digest str` · `run str` · `version int \| None` · `images int` |
| `QuotedFlow` | in `QuotedRow` | `flow str` · `images int` · `sources list[QuotedSource]` |
| `QuotedBake` | in `QuotedRow` | `flow str` · `name str` · `digest str` · `run str` · `version int` · `seed str` · `k int` |
| `QuotedRow` | in `Quote` | `collection str` · `images int` · `flows list[QuotedFlow]` · `bakes list[QuotedBake]` · `refused str \| None` |
| `QuoteEstimate` | in `Quote` | `seconds float` · `limit_s int` · `boot_s float` · `teardown_s float` |
| `QuotePrice` | in `Quote` | `about float` · `at_most float` · `keep_open float` |
| `Quote` | `POST /api/render/quote` | `collections list[QuotedRow]` · `estimate QuoteEstimate` · `price QuotePrice` · `ceiling_s int` · `disabled str \| None` |
| `BillingVolume` | in `Billing` | `state str` · `ends str \| None` |
| `Billing` | in `BillingChecked` | `pod bool` · `volume BillingVolume \| None` |
| `BillingChecked` | `POST /api/billing/check` | `billing Billing` |
| `JobStage` | in `JobProgress` | `stage str` · `done int` · `of int` |
| `JobProgress` | in `Job` | `started str` · `stages list[JobStage]` |
| `JobSession` | in `Job` | `id str` · `started str` · `limit int` · `of int` · `ended str \| None` · `steps dict[str, str]` · `images list[artifacts.SessionImage]` |
| `Job` | in `JobStarted` | `kind jobs.Kind` · `collection str` · `state str` · `flow str \| None` · `stage str \| None` · `message str \| None` · `NR progress JobProgress` · `NR collections list[str]` · `NR session JobSession` |
| `JobStarted` | `POST /api/c/{collection}/prepare`, `POST /api/render`, `POST /api/jobs/{kind}/stop` | `job Job` |
| `ServedSession` | `GET /api/c/{collection}/sessions/{name}` | the fields of `SessionRecord`, `outcome str \| None` ([D4](#d4)) |
| `RunningSession(SessionRecord)` | in `RunningSessions` | `collection str` |
| `RunningSessions` | `GET /api/sessions/running` | `sessions list[RunningSession]` |

The rows of `ANSWERS` for phase 2 are `f"GET {COLLECTION}/render": RenderOffer`, `"POST /api/render/quote": Quote` and `"POST /api/billing/check": BillingChecked`. The rows of `UNRECORDED` are `f"POST {COLLECTION}/prepare": JobStarted`, `"POST /api/jobs/{kind}/stop": JobStarted`, `"POST /api/render": JobStarted`, `"GET /api/sessions/running": RunningSessions` and `f"GET {COLLECTION}/sessions/{{name}}": ServedSession`.

## What the record samples empty

Declared from the builder's code, held by no test ([D6](#d6)):

| answer | field | declared from |
|---|---|---|
| `GET /api/tattoos` | `stage1`'s values, `cut_from`, `downscaled_from` | `isekai/interface/ui/routes/tattoos.py` `read_tattoos`, `isekai/pipeline/tattoos.py` `Tattoo` |
| `GET /api/tattoos/{name}` | `outline.points`, `cut_from`, `downscaled_from` | `Outline` and `Tattoo` of `isekai/pipeline/tattoos.py` |
| `GET .../stage1/{digest}` | `pairs` | `Stage1` of `isekai/pipeline/tattoos.py` |
| `GET /api/c/{collection}/render` | `refused` as `null`, `disabled` beyond `str` | `read_render_offer` of `isekai/interface/ui/routes/rendering.py` |
| `POST /api/render/quote` | `QuotedRow`, `QuotedFlow`, `QuotedSource`, `QuotedBake`, `disabled` beyond `str` | `_quote` and `_quoted_row` of `isekai/interface/ui/routes/rendering.py` |
| `POST /api/billing/check` | `volume` | `read` of `isekai/interface/ui/billing.py` |
| `JobSession.images` | its items | `Jobs.render` of `isekai/interface/ui/jobs.py` and the progress line |

## Tests

These tests are added, none removed or merged. Each is a `TestClient` case or a unit case of the declarations, and none boots a browser (T1: the lowest layer that can fail). Each carries `spec_exempt("structural: …")`, because no requirement fits and a `spec` marker beside it is a fault.

| layer | file | test | phase |
|---|---|---|---|
| integration | `tests/test_ui_propose.py` | `test_the_propose_answer_fits_its_declaration` | 1 |
| unit | `tests/test_ui_shapes.py` | `test_the_served_session_is_the_record_with_a_nullable_outcome` | 2 |
| integration | `tests/test_ui_jobs.py` | `test_the_prepare_answer_fits_its_declaration`, `test_the_stop_answer_fits_its_declaration`, `test_the_render_answer_fits_its_declaration` | 2 |
| integration | `tests/test_ui_api.py` | `test_the_running_sessions_answer_fits_its_declaration`, `test_a_served_session_fits_its_declaration_running_and_stale` | 2 |
| unit | `tests/test_ui_shapes.py` | `test_every_json_route_of_the_three_tables_has_a_row_in_one_table` | 3 |

The record is read by the cases and changed by none. The tests of those four files number what `uv run pytest tests/test_ui_shapes.py tests/test_ui_propose.py tests/test_ui_jobs.py tests/test_ui_api.py --collect-only -q` prints as `205 tests collected` at the base, `206` after phase 1, `212` after phase 2 and `213` after phase 3. The end-to-end runs added: none.

T2 (extend before adding): each case sits in the module whose fixture reaches its state, and a case there could not carry a `spec` key, so it is a new test. A case does not extend the test that reaches the same state, because that test binds a scenario.

| test | fixture it reuses |
|---|---|
| the propose case | `client`, `photographed`, `_body` and `_ask` of `tests/test_ui_propose.py` |
| the prepare and stop cases | `_collection` and `bare_wiring`, through `_held_client` given a `make_jobs` keyword that defaults to `Jobs` |
| the render case | `_quoting` given the same keyword, with `_approved` and a RunPod key in the session's environment |
| the running sessions and session cases | `client`, `made` and `Record` of `tests/test_ui_api.py` |

The job cases add `_Idle(Jobs)`, which overrides `_occupy` to set `slot.job` and `slot.stopping` and start no thread. Stop works on that slot, because `_interrupt` skips a missing child.

## Dependencies

None.

## Risks / Trade-offs

- **A float a pair carries may be an `int`.** The walker reads the first element's type name. The case drives the arms of `LEFT` as floats; if the shape reads `int`, declare the coordinate as the builder types it and say so here.
- **`ty` may reject the `_occupy` override.** The fallback is in [D3](#d3).
- **A sample the record leaves empty hides a wrong declaration.** [D6](#d6) names each; the page's types, derived next, will meet them.
- **`shapes.py` imports `jobs.py`, which imports other `ui` modules.** None imports a web framework; phase 2 starts with a **HALT CHECK** of that, because the file's docstring says it imports none.
- **Size.** `shapes.py` is measured at the base below; the ratchet is the limit.

| measure | command | at the base |
|---|---|---|
| lines of `shapes.py` | `wc -l isekai/interface/ui/shapes.py` | `343` |
| the ratchet's ceiling | `git grep -n "^FILE_LINES" -- tests/test_ratchets.py` | `800` |

## Verdict

Feasible. Every file and symbol this design names exists at the base: the tattoos', place and rendering route modules, `jobs.py`, `billing.py`, `artifacts.py`, `tests/record.py`'s `shape`, and the shapes, propose, jobs and api test modules. The one name added outside `shapes.py` and the tests is D64.
