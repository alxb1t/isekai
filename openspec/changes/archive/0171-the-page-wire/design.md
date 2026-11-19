# The page wire — design

`ui/src/types.ts` re-exports the types `ui/src/wire.ts` derives, under the page's names, and keeps the page's own. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`types.ts` is a hand-written copy of the server's answers, and most of the page's files import it. `wire.ts` is derived from `isekai/interface/ui/shapes.py` by `tools/derive_wire.py`, and `tests/test_derive_wire.py` holds the committed file equal to what the tool writes ([D67](../../../docs/decisions.md#d67--the-pages-wire-is-derived-from-shapespy-and-a-test-re-derives-it)). No page file reads `wire.ts` yet, and `vue-tsc` reads it alone (`docs/decisions.md:668`).

These types of `types.ts` differ from the wire's:

| page type | how it differs from the wire |
|---|---|
| `SessionRecord` | lacks `schema`, narrows `outcome` |
| `RunningSession` | holds the id, the start and the collections, the wire's holds a whole record and `collection` |
| `Billing` | narrows the volume's state to `'open' \| 'band'` |
| `QuoteSource` | lacks `images` |
| `CellEvent` | its stage is never `null`, its state is narrowed |
| `TattooList` | its `stage1` is optional |

Every other type the page shares with the wire is the wire's field for field, or narrows a pair to the page's `Point` and `Pair`. The page's names differ from Python's for some of them: `Stage` is `LibraryStage`, `JobSlot` is `Job`, `SessionRecord` is `ServedSession`.

```
shapes.py ──derive──▶ wire.ts ◀──re-export── types.ts ◀──import── the page's files
 (Python)             (derived)              (the page's names)
```

## Goals / Non-Goals

- **Goal:** `types.ts` is the one file that imports `wire.ts`, and holds a re-export, an overlay or a page-only type, nothing else.
- **Goal:** behaviour is unchanged. The typecheck is the guard, because vitest runs in node with no component mounted.
- **Non-goal:** `wire.ts`, any file under `isekai/`, `tools/` or `tests/`, a vitest case, the stream's typing. See [the proposal](proposal.md#not-in-this-change).

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `types.ts` re-exports each wire type under the page's name, one `export type` a line, and no other page file imports `wire.ts` | many files import `types.ts`; one file to read the wire keeps every import line as it is | importing `wire.ts` from each file; renaming the page's vocabulary to Python's |
| [D2](#d2) | a type the wire holds field for field is re-exported plain; a type `types.ts` keeps that names a re-exported type imports it from `./wire` too | a re-export binds no name in its own file | writing the type again beside the re-export |
| [D3](#d3) | where the page is narrower than Python on a field Python holds as `str`, the page takes the wire's wider type with no overlay | every site only compares the value; a narrowed copy is the drift this removes | an overlay that narrows `outcome`, the volume's state or the cell event's state |
| [D4](#d4) | `RunningSession` is the wire's full type, and `SessionRecord` is the wire's `ServedSession` | the page's name means the server's answer | a `Pick` of some fields of the running session |
| [D5](#d5) | `QuoteSource` is the wire's `QuotedSource` without `images`, written in `types.ts` | `thumbs.ts` passes it a quoted source and a quoted bake alike, and a bake has no `images` | re-exporting `QuotedSource`, which a bake does not satisfy |
| [D6](#d6) | `Tattoo`, `Outline`, `Stage1`, `Proposal` and `TattooList` are overlays, each an `extends Omit<…>` of the wire's type that narrows a pair to `Point` and `Pair`; `TattooList`'s `stage1` is required | JSON carries a list and the walker has no tuple form; re-exported plain, `TattooList` would hand the picker's `card` lists for pairs | a tuple in Python; a plain re-export |
| [D7](#d7) | the collection store keeps a cell event's stage only when it is set, and deletes the key otherwise | the wire's stage may be `null`, every reader tests truthiness, so behaviour is unchanged | a new vitest case; no scenario covers a cell event |
| [D8](#d8) | the doc comments of the re-exported types go with them; two that state a rule of the page move to the site that applies it | `wire.ts` has none and `shapes.py`'s docstrings hold the wire's meaning | keeping each comment beside its re-export |
| [D9](#d9) | the typed `listen`, the snapshot's type, `KINDS`, the stream's casts and `api.ts`'s casts stay as they are, and so do the page's own types | the page's stream is a later version; a store's structure changes there | typing the stream here |
| [D10](#d10) | no decision is added, and D67's *Accepts* line is amended in `docs/decisions.md` | the rule stands; the line said no page file reads `wire.ts` | a new decision |

### D1

One line a type, in the order of the phases:

```ts
export type { FlowCount } from './wire'
export type { LibraryStage as Stage } from './wire'
```

A wire class named otherwise keeps the page's name through `as`. The wire's own `SessionRecord` is not re-exported: the page's `SessionRecord` is `ServedSession` ([D4](#d4)). The map, by phase:

| phase | page name ← wire name |
|---|---|
| phase 1 · library | `FlowCount`, `LibraryRow`, `LibraryInfo`, `Stage` ← `LibraryStage` |
| phase 1 · hub | `HubCell`, `HubSource`, `HubInfo`, `Assigned` |
| phase 1 · review | `Budget`, `ScoredTag`, `OfferedTag`, `FieldCandidates`, `Renders`, `InputDetail`, `Revision`, `Drafted`, `VocabEntry` ← `TagMatch`, `TagMatches`, `InputStatus` ← `ReviewStatus`, `DraftedImage`, `RefusedImage`, `DraftRefused` |
| phase 1 · staging | `StagedState` ← `ImportingState`, `FileState`, `Committed` |
| phase 2 · jobs | `SessionImage`, `RenderSession` ← `JobSession`, `JobKind` ← `JobsKind`, `JobSlot` ← `Job`, `StageCount` ← `JobStage` |
| phase 2 · quotes | `QuoteBake` ← `QuotedBake`, `QuotedCollection` ← `QuotedRow`, `Quote`, `RenderOffer` |
| phase 2 · renders | `RenderDetail`, `Bake`, `Baked` ← `BakeQueued` |
| phase 2 · tattoos and compare | `TattooLimits`, `CompareSide`, `Comparison` |
| phase 4 · the types that differ | `Billing`, `CellEvent`, `SessionRecord` ← `ServedSession`, `RunningSession` |

### D2

`JobSlots` stays a one-line alias of the page, `Record<JobsKind, Job | null>`, importing both names. A type that fails to fit field for field is not patched in `wire.ts`, which the tool writes: it becomes an overlay of the wire's type or a plain re-export of the wider one. The typecheck says which.

### D3

The fields are a session's `outcome`, the billing volume's `state` and a cell event's `state`. `live.ts` and `Billing.vue` compare the volume's state with `'band'` and `'open'`, and the collection store compares the cell event's state with `'start'`, `'refused'` and `'done'`. A comparison with a literal type-checks against `str`.

### D4

The `RunningSession` fixtures gain the fields the wire's record requires and they lack: `schema`, `ended`, `limit`, `asked`, `steps`, `images`, `outcome` and `message`. The `SessionRecord` fixtures gain `schema`.

No assertion changes. The `schema` value is `{ name: 'session', version: 1 }`, which `SESSION_FILE` declares at `isekai/foundation/artifacts.py:499`.

### D5

`QuoteBake` is the wire's `QuotedBake`, which holds `name`, `digest`, `run` and a `version` that is a number, so it is a `QuoteSource` as `thumbs.ts` needs.

### D6

The overlays keep the page's present field types. `Tattoo`'s `size` and `downscaled_from` stay `[number, number]`, `Outline`'s `points` are `Point[]`, and `Stage1`'s and `Proposal`'s `pairs` are `Pair[]`.

`TattooList` is an overlay over the page's `Tattoo` and `Stage1`. Nothing found builds a list without `stage1`; the typecheck holds that.

### D7

```
before   if (event.state === 'start') running.value[here] = event.stage
         else delete running.value[here]
after    if (event.state === 'start' && event.stage) running.value[here] = event.stage
         else delete running.value[here]
```

The `data as CellEvent` cast on the line above stays ([D9](#d9)).

### D8

A comment that states what a type means goes, because `shapes.py` holds it. A comment that states what the page does with a value moves to the site that does it. These two are kept:

| comment | moves to |
|---|---|
| `wd14` is `null` where its artifact is absent, never a failure, and the panel is not drawn | a line above `scored` in `ui/src/components/SourcePanel.vue` |
| `band` is the window volume past its end or unanswered | a line above `alerting` in `ui/src/stores/live.ts` |

The comments of the types the page keeps — `Point`, `Pair`, `ImageRef`, `TakenOut`, `RunningRender`, `Preview`, `InkView`, `StagedFile`, `MarkKind`, `CollectionInput` and `JobSlots` — stay with them.

### D9

The page keeps `MarkKind`, `CollectionInput`, `StagedFile`, `ImageRef`, `Point`, `Pair`, `TakenOut`, `RunningRender`, `JobSlots`, `Preview` and `InkView`. They name no wire class, or a page's reading of one.

### D10

D67's *Accepts* line says the page reads the file from `the-page-wire`, so until then no page file imports it. After this change `types.ts` imports it, and the line says so. D67's *Made by* gains `0171`, as D66's lists each version that touched it.

## Tests

This change adds no test and removes none. The typecheck, `uv run python -m tools.typecheck_ui`, holds the page against the wire, and the vitest suite holds behaviour as it is.

| layer | added | removed | command that counts |
|---|---|---|---|
| pytest | none | none | `git diff --stat main -- tests` prints nothing |
| vitest | none | none | `git grep -c -E "^(spec\|test\|it)\(" -- ui/src` prints the same lines at the base and at the head |
| end-to-end | none | none | `git diff --stat main -- tests/e2e` prints nothing |

No test is deleted or merged, so there is no table of what carries its assertions. The fixtures that gain fields keep every assertion of their cases. The cell event's guard is held by the typecheck alone, as no scenario covers a cell event.

## Acceptance

The build passes these, each as it is written:

- `make gate` exits 0, `openspec validate 0171-the-page-wire --strict` passes and `uv run python -m tools.typecheck_ui` exits 0, at every phase.
- `uv run python -m tools.test_ui` passes with no existing test's assertion changed and no case added.
- `uv run pytest tests/test_derive_wire.py tests/test_ratchets.py tests/test_spec_bindings.py tests/test_docs.py` passes.
- `git grep -l "/wire'" -- ui/src` prints one line, `ui/src/types.ts`.
- `git grep -n -F "'open' | 'band'" -- ui/src/types.ts`, `git grep -n -F "'start' | 'done' | 'refused'" -- ui/src/types.ts`, `git grep -n -F "stage1?:" -- ui/src/types.ts` and `git grep -n -F "app.py" -- ui/src/types.ts` print nothing.
- `wc -l ui/src/types.ts` prints a number no greater than 250.
- `uv run python -m tools.derive_wire` exits 0, and after it `git diff --exit-code -- ui/src/wire.ts` exits 0.
- `git grep -n -F "data as CellEvent" -- ui/src/stores/collection.ts` prints one line, as at the base.
- No file under `isekai/`, `tools/`, `tests/` or `tests/record/` changes.

## Dependencies

None.

## Risks / Trade-offs

- A re-export binds no local name, so a type left in `types.ts` that names a re-exported one fails the typecheck until it imports it ([D2](#d2)). The typecheck names the line.
- A type the plan calls field for field may differ in a field the plan did not read. The phase then makes an overlay or takes the wire's type, never an edit of `wire.ts`.
- The cell event's guard is held by the typecheck alone. A reader that tested `stage` for `null` and not for truthiness would change; none was found.
- The typecheck reads every page file against the new types, though no import line of a page file changes.

## Verdict

Ready to build. The wire is derived and held, the page's names are mapped type by type, and each phase ends on a green typecheck and gate.
