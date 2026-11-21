# The page track — design

`RUNNING` in `ui/src/cells.ts` is keyed by a union of the verbs Prepare runs, `wordOf` and `segmentClass` narrow the `string` they are given by one guard, and vitest cases hold the track before the union lands. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

The hub cell's track is the tables `SEGMENTS`, `DONE` and `RUNNING` and the functions `wordOf` and `segmentClass`, in `ui/src/cells.ts`, moved there from `Hub.vue` by `0151-the-hub-rules` with no case.

```
SEGMENTS   ['assigned', 'tag', 'caption', 'sheet', 'approved', 'rendered']
DONE       Stage → how many segments a stage has done      (a draft shares the sheet's)
RUNNING    verb  → { segment, word }                       (keyed by string today)
wordOf(cell, running)              → the running word, "rendered ×n", or the stage
segmentClass(cell, running, index) → 'hub__segment--running' | 'hub__segment--done' | ''
```

`running` is the store's `Record<string, string>` entry for a cell, set from a cell event's `stage`, which [D66](../../../docs/decisions.md#d66--the-refusals-are-classes-and-the-streams-events-have-a-table-of-their-own) accepts as a `str`. `Hub.vue` passes that string to both functions, so their parameter stays `string | undefined`. The server sends a stage while a Prepare runs: the verbs `tag`, `caption` and `sheet`.

No vitest case reads any of those names. The browser tests under `tests/e2e/` reach the track through the page, and CI runs them after the merge.

## Goals / Non-Goals

- Goal: every word, segment and class the track gives stays as the base gives it, an unknown running stage included.
- Goal: `RUNNING` names the verbs it holds, and a case holds each table and each function.
- Non-goal: a wire field, `ui/src/wire.ts`, `ui/src/views/Hub.vue`, any server file, the placement's `ui/src/stages.ts`, or a changed assertion.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `PrepareVerb` in `cells.ts` is `'tag' \| 'caption' \| 'sheet'`; `RUNNING` is `Record<PrepareVerb, { segment: number; word: string }>` | the table holds the verbs Prepare runs and the type then says so; a verb added later must have a segment and a word | a union from the wire; `keyof typeof RUNNING` |
| [D2](#d2) | One guard, `isPrepareVerb(name: string): name is PrepareVerb`, tests an own key of `RUNNING`; `wordOf` and `segmentClass` keep `string \| undefined` and narrow by it | the store holds strings and `Hub.vue` stays; `in` would read `toString` as a verb | a narrowed parameter, which `Hub.vue` fails to typecheck against; a cast |
| [D3](#d3) | The cases are written first and pass on the code as it stands, bound to scenarios that exist | behaviour unchanged is the promise, and no case holds it today | the union first and the cases after |
| [D4](#d4) | `SEGMENTS` and `DONE` stay as they are | `DONE` is already keyed by `Stage`, a union; `SEGMENTS` is `as const` | a table derived from `SEGMENTS` |
| [D5](#d5) | `ui/src/wire.ts` and `ui/src/views/Hub.vue` do not change | a union from the wire reopens D66's *Accepts*, and the guard makes `Hub.vue`'s call type | a wire field for the stage |

### D1

```ts
export type PrepareVerb = 'tag' | 'caption' | 'sheet'
export const RUNNING: Record<PrepareVerb, { segment: number; word: string }> = { …same three rows… }
```

The rows, their segments and their words are not edited. A case holds that each verb's segment names the verb in `SEGMENTS`: `SEGMENTS[RUNNING[verb].segment] === verb`.

### D2

```ts
const isPrepareVerb = (name: string): name is PrepareVerb => Object.hasOwn(RUNNING, name)
```

`ui/tsconfig.json` targets `ES2022`, so `Object.hasOwn` types. `wordOf` and `segmentClass` read as before:

| call | before | after |
|---|---|---|
| `wordOf(cell, 'tag')` | `RUNNING['tag']?.word` → `tagging…` | `isPrepareVerb` → `RUNNING['tag'].word` → `tagging…` |
| `wordOf(cell, 'review')` | `RUNNING['review']?.word` is `undefined` → `review…` | not a verb → `review…` |
| `wordOf(cell, 'toString')` | `RUNNING['toString']?.word` is `undefined` → `toString…` | not an own key → `toString…` |
| `wordOf(cell, undefined)` or `''` | the cell's own word | the cell's own word |
| `segmentClass(cell, 'caption', 2)` | `hub__segment--running` | `hub__segment--running` |
| `segmentClass(cell, 'review', i)` | falls to the done test | falls to the done test |

A running mark beats a done mark on its own segment, and a stage the table lacks marks no segment.

### D3

| group | holds | bound to |
|---|---|---|
| the track | `SEGMENTS` in order; `DONE` per stage, a draft sharing the sheet's segment; `segmentClass` of each stage with nothing running, `wordOf` of a stage and of a cell rendered twice | `ui:hub:a-cells-stage-comes-from-its-run` |
| the running stage | `RUNNING`'s rows; each verb's segment names it in `SEGMENTS`; `wordOf` and `segmentClass` while a verb runs, the running mark beating the done mark; a stage the table lacks, `toString` among them; an empty `running` | `ui:events:a-stages-report-reaches-the-stream` |

A vitest case binds through `spec(` alone, so each binds a scenario the living spec holds; the key's own scenario is server-side, and the cases are the page's reading of the stage it names.

### D4

`SEGMENTS` stays `as const`, and `DONE` stays `Record<Stage, number>`: its keys are already a union. Neither is edited.

### D5

`ui/src/wire.ts` and `ui/src/views/Hub.vue` do not change. A stage from the wire as a union reopens [D66](../../../docs/decisions.md#d66--the-refusals-are-classes-and-the-streams-events-have-a-table-of-their-own)'s *Accepts*; the guard narrows what `Hub.vue` already passes.

## Tests

Adds the vitest cases of the table below at the unit layer, in `ui/src/cells.test.ts`; none end-to-end and none in a browser. Removes no test, so there is no table of removed tests; no existing assertion changes.

| layer | file | added | binds |
|---|---|---|---|
| unit | `ui/src/cells.test.ts` | the track's tables and functions with nothing running | `ui:hub:a-cells-stage-comes-from-its-run` |
| unit | `ui/src/cells.test.ts` | the running stage's table and functions | `ui:events:a-stages-report-reaches-the-stream` |

- The cases are counted by `git grep -c -e "^spec(" -- ui/src/cells.test.ts`, before and after.
- A case builds cells from `EMPTY_CELL` and calls the functions; none mounts a view, so none is slow.
- A case that passes before the union and after it is the proof of equality; a case for a stage the table lacks is the one a guard of `in` would fail.

End-to-end runs added: none; `git grep -n -e "tests/e2e" -- openspec/changes/0189-the-page-track/tasks.md` prints nothing.

## Dependencies

None.

## Risks / Trade-offs

- A `PrepareVerb` that drifts from the server's stages shows only as a running stage the table lacks: it reads `<stage>…` with no running segment, as it does today. The guard keeps that path.
- `ty` and the page's typecheck are separate; `uv run python -m tools.typecheck_ui` is the page's, and it holds `Hub.vue` compiling against the unchanged signature.
- The changelog entry of each phase is `mf-build`'s own step, so no task here writes one; the brief's phase of documents held the changelog alone and is not a phase.

## Verdict

Ready to build in the phases of [tasks](tasks.md): hold the track by cases, then type `RUNNING` by the union and narrow `wordOf` and `segmentClass` by one guard.
