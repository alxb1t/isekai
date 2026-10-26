import { defineStore, storeToRefs } from 'pinia'
import { ref, watch } from 'vue'
import { hub as readHub, session as readSession } from '../api'
import type { SessionRecord } from '../types'
import { useLiveStore } from './live'

/* The session a drawer shows: its batch and its record's id. */
interface Shown {
  batch: string
  id: string
}

/* The render drawer's state, the app's rather than the open batch's: the
   running render, else the last one this app saw end, until a reload or the
   next render starts. */
export const useDrawerStore = defineStore('drawer', () => {
  const live = useLiveStore()
  const { jobs, activeRender, activeSessions } = storeToRefs(live)
  const open = ref(false)
  const shown = ref<Shown | null>(null)
  /* The shown session's record, read again as its render moves. */
  const record = ref<SessionRecord | null>(null)
  /* Each photograph's source name, by its digest, from the shown batch's hub. */
  const photographs = ref<Record<string, string>>({})
  /* The newest record read; an answer to an older one is dropped. */
  let asked = 0

  const same = (one: Shown | null, other: Shown | null) =>
    one?.batch === other?.batch && one?.id === other?.id
  /* A read from a watcher or a click: its refusal leaves the last record shown. */
  const quietly = (read: Promise<void>) => void read.catch(() => undefined)

  /* Name each photograph from `batch`'s hub, once; a refused read leaves the
     run's own photographs to draw. */
  async function name(batch: string): Promise<void> {
    try {
      const found = await readHub(batch)
      if (shown.value?.batch !== batch) return
      photographs.value = Object.fromEntries(
        found.sources.flatMap((one) => (one.digest ? [[one.digest, one.name]] : [])),
      )
    } catch {
      // The run's own photograph stands in for its source.
    }
  }

  /** Read the shown session's record again; a refusal is thrown to the caller. */
  async function refresh(): Promise<void> {
    const held = shown.value
    if (!held) return
    const mine = ++asked
    const found = await readSession(held.batch, held.id)
    if (mine === asked && same(shown.value, held)) record.value = found
  }

  /** Show session `id` of `batch`, reading its record; a refusal is thrown to the caller. */
  function show(batch: string, id: string): Promise<void> {
    const next = { batch, id }
    if (!same(shown.value, next)) {
      const named = shown.value?.batch === batch
      shown.value = next
      record.value = null
      if (!named) {
        photographs.value = {}
        void name(batch)
      }
    }
    return refresh()
  }

  /** Open the drawer on session `id` of `batch`. */
  function openOn(batch: string, id: string): void {
    quietly(show(batch, id))
    open.value = true
  }

  /* A new render replaces the shown one; an ended one stays. */
  watch(activeRender, (held) => {
    if (held && !same(shown.value, held)) quietly(show(held.batch, held.id))
  })
  /* Every move of the render slot's session, including its volume steps; a session
     the slot has just taken was read as it was shown. */
  watch(
    () => jobs.value.render,
    (slot, before) => {
      if (!slot?.session || before?.session?.id !== slot.session.id) return
      if (same(shown.value, { batch: slot.batch, id: slot.session.id }))
        quietly(refresh())
    },
  )
  /* Disk polling brings a terminal render's record up to date, and reads it once
     more after its liveness is gone. */
  watch(activeSessions, (found) => {
    const held = shown.value
    if (
      held &&
      (record.value?.outcome === 'running' || found.some((one) => same(one, held)))
    )
      quietly(refresh())
  })

  return {
    open,
    shown,
    record,
    photographs,
    show,
    refresh,
    openOn,
    toggle: () => (open.value = !open.value),
    close: () => (open.value = false),
  }
})
