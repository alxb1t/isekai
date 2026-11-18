# The sheet's history — design

The sheet's undo and redo become pure functions over one immutable state in `ui/src/edits.ts`, pinned by a case written first on today's `useSheet`. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

`ui/src/composables/useSheet.ts` holds the draft's fields, its history, the receipt rules and the save queue in one closure. The history is private stacks, `done` and `undone`, cleared by `open`, and the functions `apply`, `record`, `commit`, `remove`, `undo` and `redo`. Only `ui/src/views/Review.vue` calls `useSheet`, through `commit`, `remove`, `undo` and `redo`; `ui/src/composables/useReviewActions.ts` takes its type.

| what | where | today |
|---|---|---|
| an edit | `Edit`: `field`, the tags `before`, the tags `after` | recorded by `record`, popped by `undo` and `redo` |
| a commit | `commit(field, tag, replacing)` | replaces the chip at `replacing` when it is in range, else adds the tag unless it is there |
| a removal | `remove(field, index)` | nothing when `index` is out of range |
| undo and redo | `undo()`, `redo()` | nothing on an empty stack; each is saved like an edit |
| the pairs' and the polygon's histories | `ui/src/pairs.ts`, `ui/src/polygon.ts` | plain modules whose `undone` and `redone` return the state they were given when there is nothing to take back |

No case drives `undo`, `redo` or `remove`, and each `commit` in `ui/src/composables/useSheet.test.ts` replaces nothing. No scenario names the sheet's undo. Vitest runs in `node` and mounts no component, so the composable itself is what a case reaches.

The mutants that name `useSheet.ts` sit in `write`, in `open`'s refusal and in `DEBOUNCE`, none in the history. A mutant is found by its text, which must occur once, so every line they name stays as it is.

## Goals / Non-Goals

- Goals: the history a plain module with its own case; one case on today's code first; `useSheet` holding one state and saving only when it changed; behaviour unchanged.
- Non-Goals: the receipt rules, the save queue and `setRenders`; a chip's selection; any key's declaration; the queue's edited mark; an edit to `ui/src/views/Review.vue` or `tests/mutants.json`; a new mutant; a component mounted in vitest.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `ui/src/edits.ts` holds `Edits` — the fields, the edits `past` and the edits `future` — and `held`, `reloaded`, `committed`, `removed`, `undone` and `redone` over it | the pairs' and the polygon's histories are plain modules with this shape | a class, or a closure over stacks |
| [D2](#d2) | The state holds operations, not snapshots: an `Edit` is a field and its tags before and after | undo crosses every field and one commit, removal or replacement is one step, as today | a copy of the whole fields at each step |
| [D3](#d3) | Each function returns the state it was given when nothing changes | `useSheet` tells a changed state from an unchanged one by identity, as the pairs' history does | a boolean beside the state, or a compare of fields |
| [D4](#d4) | `useSheet` holds one `edits` and a function `take` that sets the fields, marks the draft dirty and schedules a save only when the state changed | an undo or a redo is saved like an edit, and an edit that changed nothing sends nothing | calling `schedule` from each member |
| [D5](#d5) | The pin is one case in `ui/src/composables/useSheet.test.ts` bound to `ui:save:an-edit-is-undone-and-redone`, green before a line moves | the composable is importable, so the case holds today's behaviour for the switch | a case written with the module |
| [D6](#d6) | `ui/src/edits.test.ts` holds one case bound to the same key, a block for each function and each edge | vitest has no exempt form, and the scenario covers the history | one key for each function, which a patch may not add |
| [D7](#d7) | `open` clears the history where it does today, with `held`, and the landing read replaces the fields with `reloaded`, which keeps the history | an edit made while a read is in flight keeps its step today, and a patch changes no behaviour | holding the sheet afresh at the landing |

### D1

```ts
/** One edit, recorded so it can be taken back. */
export interface Edit {
  field: string
  before: string[]
  after: string[]
}

/** The draft's fields, the edits done, and the edits undone that a redo brings back. */
export interface Edits {
  fields: Record<string, string[]>
  past: Edit[]
  future: Edit[]
}
```

Every function returns a new state and never writes to the one it was given, nor to an array it holds. The arrays are plain, not `readonly`, so `fields` assigns to `useSheet`'s `fields` ref as today.

```ts
/** Return a state holding `fields`, with nothing to undo or redo. */
export function held(fields: Record<string, string[]>): Edits {
  return { fields: { ...fields }, past: [], future: [] }
}

/** Return the state holding `fields` in place of its own, its history as it was. */
export function reloaded(state: Edits, fields: Record<string, string[]>): Edits {
  return { ...state, fields: { ...fields } }
}

function recorded(state: Edits, field: string, after: string[]): Edits {
  const before = [...(state.fields[field] ?? [])]
  return { fields: { ...state.fields, [field]: after }, past: [...state.past, { field, before, after }], future: [] }
}

/** Return the state with `tag` committed to `field`: it replaces the chip at `replacing`, else it is added unless it is there. */
export function committed(state: Edits, field: string, tag: string, replacing: number | null): Edits {
  const tags = [...(state.fields[field] ?? [])]
  if (replacing !== null && replacing >= 0 && replacing < tags.length) tags[replacing] = tag
  else if (!tags.includes(tag)) tags.push(tag)
  else return state
  return recorded(state, field, tags)
}

/** Return the state without the tag at `index` of `field`; unchanged when `index` is out of range. */
export function removed(state: Edits, field: string, index: number): Edits {
  const tags = [...(state.fields[field] ?? [])]
  if (index < 0 || index >= tags.length) return state
  tags.splice(index, 1)
  return recorded(state, field, tags)
}

/** Return the state as it was before its last edit, which `redone` brings back; unchanged with nothing to undo. */
export function undone(state: Edits): Edits {
  const edit = state.past.at(-1)
  if (!edit) return state
  return {
    fields: { ...state.fields, [edit.field]: edit.before },
    past: state.past.slice(0, -1),
    future: [...state.future, edit],
  }
}

/** Return the state as it was before its last undo; unchanged with nothing to redo. */
export function redone(state: Edits): Edits {
  const edit = state.future.at(-1)
  if (!edit) return state
  return {
    fields: { ...state.fields, [edit.field]: edit.after },
    past: [...state.past, edit],
    future: state.future.slice(0, -1),
  }
}
```

The file opens with the comment that `useSheet.ts` carries today in its docstring — *Undo is a stack of edit operations, not sheet snapshots…* — moved whole, naming the module. `useSheet`'s docstring keeps one sentence saying the history lives in `ui/src/edits.ts`.

### D2

`record`'s `before` is a copy of the field's tags before the edit, and `undo` writes it back as the field's tags, so an undone first edit of a field leaves the key holding `[]`, as today. An edit and its tags are never changed after they are recorded, so `fields` and a recorded `after` may hold the same array.

### D3

The edges the module keeps, each held by a block of the case of [D6](#d6):

| call | returns |
|---|---|
| `committed` with a tag already in the field and no chip to replace | the state it was given |
| `committed` with a `replacing` of the tag that chip already holds | a new state, the edit recorded: a replacement that changes nothing still records an edit, as today |
| `committed` with a `replacing` out of range, or negative | the add rule: the tag added, or the state given when it is there |
| `removed` with an `index` below 0 or past the last tag | the state it was given |
| `undone` with an empty `past`, `redone` with an empty `future` | the state it was given |
| `committed` or `removed` after an `undone` | a state with an empty `future`: a new edit ends the redo |

Neither `undone` nor `redone` marks the sheet in the queue as edited: `Review.vue` calls `queue.markEdited` from its own `commit`, `back` and `@remove` and not from `undo` or `redo`, and this change leaves that as it is.

### D4

`useSheet.ts` drops `interface Edit`, `done`, `undone`, `apply`, `record` and the bodies of `commit`, `remove`, `undo` and `redo`. It imports as it does from `'../api'`: `import { committed, held, redone, reloaded, removed, undone } from '../edits'` and `import type { Edits } from '../edits'`. It holds:

```ts
  let edits: Edits = held({})
```

in the place of `done` and `undone`, with the one function that every member calls:

```ts
  /* Take `next` as the sheet's state: an edit that changed nothing marks nothing and sends nothing. */
  function take(next: Edits): void {
    if (next === edits) return
    edits = next
    fields.value = next.fields
    dirty = true
    schedule()
  }

  function commit(field: string, tag: string, replacing: number | null): void {
    take(committed(edits, field, tag, replacing))
  }

  function remove(field: string, index: number): void {
    take(removed(edits, field, index))
  }

  function undo(): void {
    take(undone(edits))
  }

  function redo(): void {
    take(redone(edits))
  }
```

`commit`, `remove`, `undo` and `redo` stay function declarations in the same places, and the returned members are as today. `edits` is a plain `let`, not a ref: the page reads `fields`, which `take` and `open` keep equal to `edits.fields`.

### D5

The case opens a sheet with the fields `hair` and `eyes` and drives the history through the composable. `detail` in the test file holds `hair` alone, so the case builds its read as `{ ...detail('a', 10), fields: { hair: ['long hair'], eyes: ['blue eyes'] } }`.

| step | the draft the save carries | the save's receipt |
|---|---|---|
| `commit('hair', 'brown hair', null)` | `hair` of `long hair` and `brown hair`, `eyes` of `blue eyes` | 11 |
| `remove('eyes', 0)` | `eyes` empty | 12 |
| `undo()` | `eyes` of `blue eyes` | 13 |
| `undo()` | `hair` of `long hair` | 14 |
| `redo()` | `hair` of `long hair` and `brown hair` | 15 |

Each step calls `void sheet.flush()`, reads the `PUT`'s body from `calls`, and answers it through the file's `answer`. Then the sheet is opened again and answered with the same read: an `undo()` and a `redo()` change `fields` not at all, and `calls` holds nothing after the timers run. The case is written and green before any line of `useSheet.ts` moves; it sits at the file's end and changes no other case.

### D6

`ui/src/edits.test.ts` holds one `spec('ui:save:an-edit-is-undone-and-redone', …)`, a block for each function, each starting from its own `held` state ([T3](#tests)):

| block | asserts |
|---|---|
| `held` | the state holds a copy of its fields: a write to the object it was given leaves the state alone; `past` and `future` empty |
| `committed` | an add; a replacement at an index; a replacement of a chip by its own tag still records; an index out of range and a negative index add; a tag already there returns the state given; a new field starts at `before` empty |
| `removed` | a removal; an index below 0 and past the last tag return the state given |
| `undone` and `redone` | each restores the tags `before` and `after`; an empty `past` and an empty `future` return the state given; a commit after an undo empties `future`; the state each was given still holds its fields |
| `reloaded` | the fields are the new ones and `past` and `future` are as they were |

### D7

`open` calls `held(edits.fields)` where it clears the stacks today, at its start and before the read is awaited, so a read that fails still leaves the history clear. The landing read calls `edits = reloaded(edits, body.fields)` and `fields.value = edits.fields` where it sets `fields.value = { ...body.fields }` today.

```ts
    dirty = false
    loading.value = true
    edits = held(edits.fields)
```

```ts
    generation += 1
    detail.value = body
    edits = reloaded(edits, body.fields)
    fields.value = edits.fields
```

The failed read's `refusal.value = (reason as Error).message`, `loading.value = false` and `return`, and `const DEBOUNCE = 400`, stay as they are, for the mutants that name them. No decision in force is added or overturned, so `docs/decisions.md` is not edited.

## Tests

The change adds vitest cases and removes none; it adds no end-to-end run and no pytest test.

| layer | added | removed | the command |
|---|---|---|---|
| vitest, unit | the case of `ui/src/composables/useSheet.test.ts` and the case of `ui/src/edits.test.ts` | none | `git grep -c -h -F "ui:save:an-edit-is-undone-and-redone" -- ui/src/composables/useSheet.test.ts ui/src/edits.test.ts` prints `1` twice |
| end-to-end | none | none | `git grep -c -h -F "useSheet" -- tests/e2e` prints nothing |
| pytest | none | none | `git log --format=%h main..HEAD -- tests` prints nothing |

Both cases are unit cases at the lowest layer a node run reaches ([T1](#tests)); the new scenario is `unit`. No existing case is deleted, merged or has an assertion changed, so there is no mapping table.

## Dependencies

None.

## Risks / Trade-offs

- **The case reaches the composable, not the keys.** Vitest cannot mount `Review.vue`, so `Mod+Z` reaching `sheet.undo()` is read, not tested: `Review.vue` is not edited and the binding stands at its lines.
- **`fields` and `edits.fields` are separate objects.** `take` sets one from the other, and nothing else writes to `fields`, so they hold the same tags; a later writer would have to go through `take`.
- **`reloaded` keeps a history that `held` would clear.** It is today's behaviour for an edit made while a read is in flight; clearing it at the landing is a change for a version that fixes it.
- **The scenario is under a requirement whose prose does not name undo.** The requirement says an edit is saved, and an undo is an edit that is saved; a patch adds no requirement.

## Verdict

Feasible. The history is a move of settled lines into functions a case reaches without a save in flight, and the pin holds it first.
