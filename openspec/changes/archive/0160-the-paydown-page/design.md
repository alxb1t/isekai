# The paydown, the page — design

Each late completion of the page becomes a unit its component calls, and a case holds the unit with a deferred answer. Verdict: ready to build, in the phases of [tasks](tasks.md).

## Context

Vitest runs in `node` with no DOM and mounts no component, so a case reaches only what a component calls. The cards are fixed in the source and no case reaches the fix:

| card | the fix in the source | what holds it today |
|---|---|---|
| `0143·S1` | `latest()` in `ui/src/views/RenderLarge.vue`, begun in `deleted()`, dropped on unmount | `ui/src/views/RenderLarge.test.ts` repeats the logic beside the view |
| `0142·S1` | `reporting(run, told)` in `ui/src/confirm.ts`, called by `ui/src/components/TattooPicker.vue` | `ui/src/confirm.test.ts` holds the helper alone |
| `0142·S2` | the `gone` flag and `inkUrl(image, gone)` in `ui/src/components/CutImage.vue` | `ui/src/tattoos.test.ts` calls `inkUrl` with a constant |

Deleting a render hears of its success through `ConfirmDialog.vue`'s `done`, which the dialog sends after `await props.run()` and never once it is dismissed: `@done="deleted"` in `RenderLarge.vue` is the path `0142·S1` closed for tattoos. It is traced, not run.

## Goals / Non-Goals

- Goals: each completion a function or composable its component calls; one case each, bound to a scenario, giving it a deferred answer in an effect scope whose stop is the leaving; one vitest edit each in `tests/mutants.json`.
- Non-Goals: mounting a component; a browser test; a template's binding of a unit (the design names each, below); an edit to an archived change; a card raised after the base; the dialog's `done` event, which stays in `ConfirmDialog.vue`.

## Decisions

| id | decision | because | rejected |
|---|---|---|---|
| [D1](#d1) | `useDeletion({ reload, open })` in `composables/useDeletion.ts` owns what follows a deletion, and `latest` moves into it | the view then calls the unit a case can reach; the guard is dropped by the scope's end | keeping `latest` in the view's plain script block and importing it from a view |
| [D2](#d2) | `useDeletion` returns `through(remove)`: the deletion reports through its own request, and the dialog's `done` is unbound | a dismissed dialog is gone when the request settles; the tattoo's removal is fixed so | re-emitting `done` from the dialog before the request ends |
| [D3](#d3) | `useRemoval({ remove, removed })` in `composables/useRemoval.ts` owns the picker's question and its report | the picker calls the unit whose `run` is the card's own request | a case on `reporting` alone, which the picker's call never reaches |
| [D4](#d4) | `useCutInk(read)` in `composables/useCutInk.ts` owns a cut card's loader; the scope's end is the card's leaving | the loader's `gone` flag is state a case can only drive through the unit | testing `inkUrl` with a constant |
| [D5](#d5) | Each case runs in an `effectScope`, stopped as the leaving, with a promise the case settles by hand | the cards' Status notes ask for a red run that reaches the delayed completion | a case that never stops the scope |
| [D6](#d6) | Vitest edits `PG-1` to `PG-4` close the file; each disables one guard in a product file | a red run kept nowhere is the cards' own complaint; the edits at the end merge with no conflict beside the tests version's | a red run noted in a commit body |
| [D7](#d7) | `ui/src/views/RenderLarge.test.ts` changes its import line alone | `latest` moves; its case's expectations stay byte for byte | a re-export from the view kept for the test |

### D1

The file holds `latest`, moved whole from `RenderLarge.vue`'s plain script block, and the unit:

```ts
import { onScopeDispose } from 'vue'

export function latest(): { begin: () => () => boolean; drop: () => void } {
  // the body of RenderLarge.vue's `latest`, unchanged
}

/** Return what follows a deletion: `deleted` reads the Hub again, then opens it unless the scope has ended. */
export function useDeletion(after: { reload: () => Promise<unknown>; open: () => void }) {
  const leaving = latest()
  onScopeDispose(leaving.drop)
  async function deleted(): Promise<void> {
    const still = leaving.begin()
    await after.reload().catch(() => undefined)
    if (still()) after.open()
  }
  return { deleted }
}
```

`RenderLarge.vue` calls it, in place of its `leaving`, `onUnmounted` and `deleted`:

```ts
const { deleted } = useDeletion({
  reload: () => store.reloadHub(),
  open: () => void router.push(hubCell.value),
})
```

A refused read opens the Hub all the same, as today: the `catch` stands. A component's scope stops on unmount, so `onScopeDispose` is `onUnmounted` for the view.

### D2

`useDeletion` gains `through`, and returns `{ deleted, through }`:

```ts
  const through = <T>(remove: () => Promise<T>): (() => Promise<T>) =>
    reporting(remove, () => void deleted())
```

with `import { reporting } from '../confirm'`. A success calls `deleted()` from the request itself; a refusal calls nothing and is thrown on, for the dialog to show. `RenderLarge.vue` takes `through` in place of `deleted`, and the dialog reads:

```
    <ConfirmDialog
      v-if="deleting"
      marker="delete"
      :title="deletion.title"
      :name="deletion.name"
      :run="through(() => deleteRender(place))"
      @close="deleting = false"
    />
```

`through` builds a new `run` at each render of the template. The dialog reads `props.run` once, when *Yes* is pressed, so the request that was pressed is the one that reports.

What no case reaches: that the template passes `through(...)` as `:run` and binds no `@done`. `git grep -n -F "@done" -- ui/src/views/RenderLarge.vue` printing nothing is the check, and the recorded trace of this dialog and `0142·S1`'s run on the same dialog stand as the evidence.

### D3

```ts
import { computed, ref } from 'vue'
import { removal, reporting } from '../confirm'

/** Return the tattoo *Remove* was pressed on, and the question asked about it. */
export function useRemoval(page: {
  remove: (name: string) => Promise<unknown>
  removed: (name: string) => void
}) {
  const asking = ref<string | null>(null)
  const question = computed(() => {
    const name = asking.value
    return name === null
      ? null
      : {
          ...removal(name),
          run: reporting(() => page.remove(name), () => removed(name)),
        }
  })

  /* The picker is told of a removal by its own request, not through the dialog: a dialog dismissed
     while the request ran is gone when it settles, and the tattoo is still removed. */
  function removed(name: string): void {
    if (asking.value === name) asking.value = null
    page.removed(name)
  }

  return { asking, question }
}
```

`TattooPicker.vue` calls it, in place of its `asking`, `question` and `removed`:

```ts
const { asking, question } = useRemoval({
  remove: (name) => removeTattoo(props.place.digest, name),
  removed: (name) => emit('removed', name),
})
```

and drops `removal` and `reporting` from its `'../confirm'` import, which leaves the line with nothing. Its template reads `asking` and `question` as it does today.

### D4

```ts
import { onScopeDispose, ref } from 'vue'
import { inkUrl } from '../tattoos'
import type { Outline } from '../types'

/** What a cut's card reads: its held outline, and the ink view the server draws for it. */
export interface CutRead {
  outline: () => Promise<Outline>
  ink: (outline: Outline, signal: AbortSignal) => Promise<{ image: Blob }>
}

export function useCutInk(read: CutRead) {
  const outline = ref<Outline | null>(null)
  const ink = ref<string | null>(null)

  /* Leaving the card ends the ink request, and an answer that still lands makes no URL. */
  const asking = new AbortController()
  let gone = false

  async function load(): Promise<void> {
    try {
      const held = await read.outline()
      outline.value = held
      if (!held.closed) return
      const made = await read.ink(held, asking.signal)
      ink.value = inkUrl(made.image, () => gone)
    } catch {
      // The card keeps what it shows: the crop, or the whole photograph.
    }
  }

  onScopeDispose(() => {
    gone = true
    asking.abort()
    if (ink.value) URL.revokeObjectURL(ink.value)
  })

  return { outline, ink, load }
}
```

`CutImage.vue` calls it, and `onMounted` starts it:

```ts
const { outline, ink, load } = useCutInk({
  outline: async () => (await tattooNamed(props.place.digest, props.tattoo.name)).outline,
  ink: (held, signal) => inkView(props.place.collection, props.tattoo.name, held, props.place, signal),
})
onMounted(load)
```

It drops its own `outline`, `ink`, `asking`, `gone`, `onMounted` body and `onUnmounted`, and the imports nothing then reads: `onUnmounted`, `ref`, `inkUrl` and the `Outline` type. `crop` and `style` read `outline` as they do.

### D5

Each case runs the unit inside `effectScope().run(...)` and stops the scope to leave. The answer is a promise the case settles by hand, in the order the card names: leave first, answer after. A second half of each case holds the other order, so a guard that is always on is red too.

| case file | key | the order it holds |
|---|---|---|
| `useDeletion.test.ts` | `ui:delete-render:a-reload-that-lands-after-leaving-moves-nothing` | `deleted()` begun, scope stopped, read answered then refused: nothing opens; scope kept: it opens once, answered or refused |
| `useDeletion.test.ts` | `ui:delete-render:a-dismissed-dialog-still-opens-the-hub` | `through(remove)()` begun with no dialog to carry the word, then answered: the Hub opens once; refused: it does not, and the refusal is thrown |
| `useRemoval.test.ts` | `ui:picker:a-dismissed-removal-still-lists-the-rest` | `asking` set, `question.value.run()` begun, `asking` cleared, then answered: `removed` is told the name once; refused: not told |
| `useCutInk.test.ts` | `ui:picker:a-crop-that-lands-after-leaving-is-dropped` | `load()` begun on a closed outline, scope stopped, ink answered: no object URL, `ink` null; scope kept: the URL is made, and revoked when the scope stops |

`useCutInk.test.ts` spies `URL.createObjectURL` and `URL.revokeObjectURL`, as `tattoos.test.ts` does, and restores them. A stub of `read.ink` ignores its signal, so the answer lands as it does when the abort is late.

### D6

These entries follow `VT-18c` in `tests/mutants.json`, in this order. Each `find` occurs once in its file.

```json
  {
    "finding": "PG-1",
    "runner": "vitest",
    "path": "ui/src/composables/useDeletion.ts",
    "find": "  onScopeDispose(leaving.drop)\n",
    "replace": "",
    "tests": ["ui/src/composables/useDeletion.test.ts"],
    "why": "a reload that lands after the view is left opens the Hub"
  },
  {
    "finding": "PG-2",
    "runner": "vitest",
    "path": "ui/src/composables/useDeletion.ts",
    "find": "    reporting(remove, () => void deleted())\n",
    "replace": "    remove\n",
    "tests": ["ui/src/composables/useDeletion.test.ts"],
    "why": "a deletion whose dialog is dismissed never opens the Hub"
  },
  {
    "finding": "PG-3",
    "runner": "vitest",
    "path": "ui/src/composables/useRemoval.ts",
    "find": "run: reporting(() => page.remove(name), () => removed(name)),",
    "replace": "run: () => page.remove(name),",
    "tests": ["ui/src/composables/useRemoval.test.ts"],
    "why": "a removal whose dialog is dismissed leaves the tattoo on the picker"
  },
  {
    "finding": "PG-4",
    "runner": "vitest",
    "path": "ui/src/composables/useCutInk.ts",
    "find": "ink.value = inkUrl(made.image, () => gone)",
    "replace": "ink.value = inkUrl(made.image, () => false)",
    "tests": ["ui/src/composables/useCutInk.test.ts"],
    "why": "an ink view that lands after the card is left leaks its object URL"
  }
```

`make mutants` replays the whole file and fails on a survivor. Each edit is red by its case and by nothing else; the case seen red is the red run each card asks for.

### D7

`RenderLarge.test.ts` imports `latest` from `./RenderLarge.vue`. The plain script block leaves the view, so its one import line becomes `import { latest } from '../composables/useDeletion'`. The case's body and its expectations are not touched.

The case stays bound to `ui:delete-render:the-hub-opens-without-the-deleted-render`: no case is deleted or merged.

No decision in force is added or overturned, so `docs/decisions.md` is not edited: D55 to D62 hold for the server and the layout, and nothing here sets a rule they state.

## Tests

The change adds vitest cases and removes none; it adds no end-to-end run and no pytest test.

| layer | added | removed | the command |
|---|---|---|---|
| vitest, unit | the cases of `ui/src/composables/useDeletion.test.ts`, `useRemoval.test.ts` and `useCutInk.test.ts` | none | `git grep -c -h -E "^spec\(" -- ui/src/composables/useDeletion.test.ts` prints `2`; the other two each print `1` |
| end-to-end | none | none | `git grep -c -h -F "useDeletion" -- tests/e2e` prints nothing |
| pytest | none | none | `git diff --stat main -- tests` names `tests/mutants.json` alone |

Each case is a unit case at the lowest layer a node run reaches ([T1](../../../CODING_STANDARDS.md)); a scenario only a browser shows stays e2e, and these four are `unit`. No existing case is deleted, merged or has an assertion changed, so there is no mapping table; `RenderLarge.test.ts` changes its import line alone ([D7](#d7)).

## Dependencies

None.

## Risks / Trade-offs

- **A refusal after a dismissal is shown nowhere.** The dialog that would show it is gone, as for a tattoo's removal today; the deletion's own thrown error is the dialog's to show while it stays.
- **The template's binding is untested.** A case cannot see that `RenderLarge.vue` passes `through(...)` as `:run`, that `TattooPicker.vue` reads `question.run`, or that `CutImage.vue` calls `onMounted(load)`. The greps of the tasks are the check, and a reviewer reads the calls.
- **Cases read the views' source.** `ui/src/nokeys.test.ts` and `ui/src/offer.test.ts` read `RenderLarge.vue` and `TattooPicker.vue` raw; the strings they match (`useKeys(`, the place button and its command, no `keydown`) are not on a moved line, and no composable here declares a key.
- **`onScopeDispose` and `onUnmounted` differ in when they run.** A component's scope stops as it unmounts, before its post-render hooks; neither runs before the next tick, and each guard only has to hold by then.
- **The loader's catch is wide.** `load` swallows every error, as `CutImage.vue` does, so a failed ink request keeps the crop.

## Verdict

Feasible. The fixes are in the source and each unit is a move of settled lines; the work is a place a case can reach, and a red run that does.
