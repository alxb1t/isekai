import { defineStore, storeToRefs } from 'pinia'
import { computed, ref, watch, type Ref } from 'vue'
import { hub as readHub, renderOffer, renders as readRenders } from '../api'
import type { CellEvent, HubCell, HubInfo, JobSlot, RenderOffer, RendersInfo } from '../types'
import { type Snapshot, useLiveStore } from './live'

const NO_OFFER: RenderOffer = { disabled: null, images: 0, refused: null }

/* A cell's key in the maps of refusals and running stages. */
export function at(name: string, flow: string): string {
  return `${name}|${flow}`
}

/* The open batch, one copy for every screen of it: its hub, the stages running
   in its cells and their refusals, its renders once a screen reads them, and its
   Render offer and dialog, which has no URL of its own
   (design spec §1 rule 8). */
export const useBatchStore = defineStore('batch', () => {
  const live = useLiveStore()
  const { jobs, billing, renderRunning, activeRender } = storeToRefs(live)
  const name = ref<string | null>(null)
  const hub = ref<HubInfo | null>(null)
  /* The stage running in a cell, by `source|flow`, from the job's reports. */
  const running = ref<Record<string, string>>({})
  /* Each cell's refusal from a tick or from the job, by `source|flow`. */
  const refusals = ref<Record<string, string>>({})
  const renders = ref<RendersInfo | null>(null)
  const offer = ref<RenderOffer>({ ...NO_OFFER })
  const dialog = ref(false)
  /* Each grid's focus, by its spot's name, written on every move: Esc from a
     large view, the Back button and a tab switch all come back to it. */
  const focus = ref<{ hub: string | null; renders: string | null }>({ hub: null, renders: null })
  /* A render session running for this batch, not another's. */
  const rendering = computed(() => renderRunning.value && activeRender.value?.batch === name.value)
  /* A Prepare running for this batch, not another's. */
  const preparing = computed(
    () => jobs.value.prepare?.state === 'running' && jobs.value.prepare.batch === name.value,
  )
  /* The newest offer request; an answer to an older one is dropped. */
  let asked = 0

  /* Hold `batch`, or none off a batch's screens; another batch starts from nothing. */
  function open(batch: string | null): void {
    if (name.value === batch) return
    name.value = batch
    hub.value = null
    running.value = {}
    refusals.value = {}
    renders.value = null
    offer.value = { ...NO_OFFER }
    dialog.value = false
    focus.value = { hub: null, renders: null }
    asked += 1
  }

  /* Read the held batch with `read` into `into`, unless another batch is held by then. */
  async function reload<T>(read: (batch: string) => Promise<T>, into: Ref<T | null>): Promise<T> {
    const batch = name.value ?? ''
    const found = await read(batch)
    if (name.value === batch) into.value = found
    return found
  }

  /** Read the hub again; a refusal is thrown to the caller, who decides where it shows. */
  const reloadHub = () => reload(readHub, hub)
  /** Read the renders again; a refusal is thrown to the caller. */
  const reloadRenders = () => reload(readRenders, renders)

  /* Read the offer again. One that cannot be read is refused, so its reason shows. */
  async function check(): Promise<void> {
    const mine = ++asked
    const batch = name.value ?? ''
    let found: RenderOffer
    try {
      found = await renderOffer(batch)
    } catch (reason) {
      const message = (reason as Error).message
      found = { disabled: message, images: offer.value.images, refused: message }
    }
    if (mine === asked) offer.value = found
  }

  function openDialog(): void {
    if (offer.value.images > 0 && offer.value.disabled === null) dialog.value = true
  }

  function closeDialog(): void {
    dialog.value = false
    void check()
  }

  /* Put `found` on its source's cell. */
  function apply(source: string, flow: string, found: HubCell): void {
    const held = hub.value?.sources.find((one) => one.name === source)
    if (held) held.cells = { ...held.cells, [flow]: found }
  }

  live.listen('snapshot', (data) => {
    const found = (data as Snapshot).hub
    if (found && found.batch === name.value) hub.value = found
  })
  live.listen('cell', (data) => {
    const event = data as CellEvent
    const here = at(event.source, event.flow)
    apply(event.source, event.flow, event.cell)
    if (event.state === 'start') running.value[here] = event.stage
    else delete running.value[here]
    if (event.state === 'refused' && event.message) refusals.value[here] = event.message
    else if (event.state === 'done') delete refusals.value[here]
  })

  /* Whether a slot's job started or ended, while a batch is open; null otherwise. */
  function moved(slot: JobSlot | null, before: JobSlot | null): 'started' | 'ended' | null {
    const was = before?.state === 'running'
    if (was === (slot?.state === 'running') || name.value === null) return null
    return was ? 'ended' : 'started'
  }
  /* A job that ends changes the cells and the images. */
  function ended(): void {
    void reloadHub().catch(() => undefined)
    if (renders.value) void reloadRenders().catch(() => undefined)
  }
  /* A Prepare's end changes the offer and clears the cells its reports marked running. */
  watch(() => jobs.value.prepare, (slot, before) => {
    if (moved(slot, before) !== 'ended') return
    running.value = {}
    void check()
    ended()
  })
  /* A render that starts or ends changes the offer: it holds Render back. */
  watch(() => jobs.value.render, (slot, before) => {
    const move = moved(slot, before)
    if (move === null) return
    void check()
    if (move === 'ended') ended()
  })
  watch(
    () => billing.value?.pod,
    () => {
      if (name.value !== null) void check()
    },
  )

  return {
    name,
    hub,
    running,
    refusals,
    renders,
    offer,
    dialog,
    focus,
    rendering,
    preparing,
    open,
    reloadHub,
    reloadRenders,
    check,
    openDialog,
    closeDialog,
    apply,
  }
})
