import { type InjectionKey, computed, ref, shallowRef } from 'vue'
import { type Place, saveStageOne, stageOne, tattooNamed } from '../api'
import { type Outlines, none as noOutlines } from '../outlines'
import { type Pairs, complete, held, none } from '../pairs'
import { type Asks, noAsks } from '../propose'
import { modeOf } from '../stages'
import type { Outline, Pair, Stage1, Tattoo } from '../types'

/* What the placement screen holds across its steps: the tattoo, the stage-1 pairs read for
   this photograph, the stage-1 pairs held, the pairs of stage 2 or the direct stage, the
   limb and the exclusions, and the asks for proposed pairs, keyed by tattoo and render so
   that a stage asks once, whichever tattoo the screen has since held. Stage 1
   is saved as it changes; the later stage, the outlines and the asks
   are held until a bake. `Place.vue` creates
   it and provides it, so a step change keeps what it holds. */

export type Named = Tattoo & { outline: Outline }

/* What it reads and writes, so a test passes its own. */
export interface Ports {
  read: (name: string) => Promise<Named>
  stageOne: (digest: string, name: string) => Promise<Stage1>
  save: (digest: string, name: string, stage: Stage1) => Promise<Stage1>
}

const serverPorts = (place: Place): Ports => ({
  read: (name) => tattooNamed(place.digest, name),
  stageOne,
  save: saveStageOne,
})

/* How long a change of the pairs waits for the next before it is saved, in ms. */
const SAVE_DELAY = 300

const sameAs = (a: readonly Pair[], b: readonly Pair[]): boolean =>
  JSON.stringify(a) === JSON.stringify(b)

export function usePlacing(place: Place, ports: Ports = serverPorts(place)) {
  const tattoo = shallowRef<Named | null>(null)
  const read = shallowRef<Stage1 | null>(null)
  const first = shallowRef<Pairs>(none)
  const notOnPhoto = ref(false)
  const second = shallowRef<Pairs>(none)
  const outlines = shallowRef<Outlines>(noOutlines)
  const proposalAsked = shallowRef<Asks>(noAsks)
  const status = ref('')
  const savedAt = shallowRef<Date | null>(null)
  const refusal = ref<string | null>(null)

  const mode = computed(() => (tattoo.value ? modeOf(tattoo.value.kind, notOnPhoto.value) : null))

  let loading: Promise<void> = Promise.resolve()
  let saving: Promise<void> = Promise.resolve()

  /** Read `name` and its pairs on this photograph, unless it is the tattoo already held:
      what a step change finds is what the last step left. */
  function load(name: string): Promise<void> {
    if (tattoo.value?.name === name) return loading
    loading = (async () => {
      try {
        const [named, stage] = await Promise.all([ports.read(name), ports.stageOne(place.digest, name)])
        tattoo.value = named
        read.value = stage
        first.value = held(stage.pairs)
        notOnPhoto.value = stage.not_on_photo
        second.value = none
        outlines.value = noOutlines
        savedAt.value = null
        refusal.value = null
      } catch (reason) {
        refusal.value = (reason as Error).message
      }
    })()
    return loading
  }

  /** Read the held tattoo again, for the outline the step before saved. */
  async function reload(): Promise<void> {
    const name = tattoo.value?.name
    if (name === undefined) return
    try {
      tattoo.value = await ports.read(name)
    } catch (reason) {
      refusal.value = (reason as Error).message
    }
  }

  let timer: ReturnType<typeof setTimeout> | undefined

  /* Send the complete stage-1 pairs and the flag as they stand, after the saves already on
     their way. */
  function flush(): void {
    clearTimeout(timer)
    timer = undefined
    const name = tattoo.value?.name
    if (name === undefined) return
    const stage: Stage1 = { pairs: complete(first.value), not_on_photo: notOnPhoto.value }
    saving = saving.then(async () => {
      try {
        read.value = await ports.save(place.digest, name, stage)
        savedAt.value = new Date()
        if (timer === undefined) status.value = 'saved'
      } catch (reason) {
        status.value = (reason as Error).message
      }
    })
  }

  /* A change is saved soon: a drag is many changes and one save. */
  function persist(): void {
    status.value = 'saving…'
    clearTimeout(timer)
    timer = setTimeout(flush, SAVE_DELAY)
  }

  /** Hold the stage-1 pairs `next`; a change of the complete pairs is saved at once.
      A lone point is held and never sent. */
  function editFirst(next: Pairs): void {
    if (next === first.value) return
    const before = complete(first.value)
    first.value = next
    if (!sameAs(before, complete(next))) persist()
  }

  /** Hold the pairs of stage 2 or the direct stage until the bake. */
  function editSecond(next: Pairs): void {
    second.value = next
  }

  /** Hold the limb and the exclusions `next` until the bake. */
  function editOutlines(next: Outlines): void {
    outlines.value = next
  }

  /** Choose or clear *not on this photo*, which keeps the stage-1 pairs; a cut has none. */
  function setNotOnPhoto(flag: boolean): void {
    if (tattoo.value === null || tattoo.value.kind === 'cut' || flag === notOnPhoto.value) return
    notOnPhoto.value = flag
    persist()
  }

  /** Drop the tattoo held, so the next `load` reads it and its pairs again. */
  function forget(): void {
    tattoo.value = null
  }

  /** Send any change waiting, and resolve once every save sent has been answered. */
  function settled(): Promise<void> {
    if (timer !== undefined) flush()
    return saving
  }

  /** Run `ask` once every save has been answered, so what it reads is never older than the file. */
  async function after<T>(ask: () => Promise<T>): Promise<T> {
    await settled()
    return ask()
  }

  return {
    place,
    tattoo,
    read,
    first,
    notOnPhoto,
    second,
    outlines,
    proposalAsked,
    mode,
    status,
    savedAt,
    refusal,
    load,
    reload,
    editFirst,
    editSecond,
    editOutlines,
    setNotOnPhoto,
    forget,
    settled,
    after,
  }
}

export type Placing = ReturnType<typeof usePlacing>

export const PLACING: InjectionKey<Placing> = Symbol('placing')
