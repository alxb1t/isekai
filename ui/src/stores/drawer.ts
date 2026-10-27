import { defineStore, storeToRefs } from 'pinia'
import { computed, ref, watch } from 'vue'
import { hub as readHub, session as readSession } from '../api'
import { type Shown, same } from '../sessions'
import type { SessionRecord } from '../types'
import { collectionsOf, useLiveStore } from './live'

/* The render drawer's state, the app's rather than the open collection's: the
   running render, else the last one this app saw end, until a reload or the
   next render starts. */
export const useDrawerStore = defineStore('drawer', () => {
  const live = useLiveStore()
  const { jobs, activeRender, activeSessions } = storeToRefs(live)
  const open = ref(false)
  const shown = ref<Shown | null>(null)
  /* Each collection's record of the shown session, by name, read again as its render moves. */
  const records = ref<Record<string, SessionRecord> | null>(null)
  /* The first collection's record: the steps, limit and outcome every record shares. */
  const record = computed(() => {
    const first = shown.value?.collections[0]
    return (first !== undefined && records.value?.[first]) || null
  })
  /* Each photograph's source name, by collection and then digest, from each hub. */
  const photographs = ref<Record<string, Record<string, string>>>({})
  /* The newest records read; an answer to an older read is dropped. */
  let asked = 0

  /* A read from a watcher or a click: its refusal leaves the last record shown. */
  const quietly = (read: Promise<void>) => void read.catch(() => undefined)

  /* Name each photograph from `collection`'s hub, once; a refused read leaves the
     run's own photographs to draw. */
  async function name(collection: string): Promise<void> {
    try {
      const found = await readHub(collection)
      if (!shown.value?.collections.includes(collection)) return
      photographs.value = {
        ...photographs.value,
        [collection]: Object.fromEntries(
          found.sources.flatMap((one) => (one.digest ? [[one.digest, one.name]] : [])),
        ),
      }
    } catch {
      // The run's own photograph stands in for its source.
    }
  }

  /** Read every record of the shown session again; a refusal is thrown to the caller. */
  async function refresh(): Promise<void> {
    const held = shown.value
    if (!held) return
    const mine = ++asked
    const found = await Promise.all(held.collections.map((one) => readSession(one, held.id)))
    if (mine === asked && same(shown.value, held))
      records.value = Object.fromEntries(held.collections.map((one, at) => [one, found[at]]))
  }

  /** Show session `id` of `collections`, reading each record; a refusal is thrown to the caller. */
  function show(collections: string[], id: string): Promise<void> {
    const next = { id, collections }
    if (!same(shown.value, next)) {
      shown.value = next
      records.value = null
      photographs.value = Object.fromEntries(
        Object.entries(photographs.value).filter(([one]) => collections.includes(one)),
      )
      for (const one of collections) if (!(one in photographs.value)) void name(one)
    }
    return refresh()
  }

  /** Open the drawer on session `id` of `collections`. */
  function openOn(collections: string[], id: string): void {
    quietly(show(collections, id))
    open.value = true
  }

  /* A new render replaces the shown one; an ended one stays. */
  watch(activeRender, (held) => {
    if (held && !same(shown.value, held)) quietly(show(held.collections, held.id))
  })
  /* Every move of the render slot's session, including its volume steps; a session
     the slot has just taken was read as it was shown. */
  watch(
    () => jobs.value.render,
    (slot, before) => {
      if (!slot?.session || before?.session?.id !== slot.session.id) return
      if (same(shown.value, { id: slot.session.id, collections: collectionsOf(slot) }))
        quietly(refresh())
    },
  )
  /* Disk polling brings a terminal render's records up to date, and reads them once
     more after its liveness is gone. */
  watch(activeSessions, (found) => {
    const held = shown.value
    if (
      held &&
      (record.value?.outcome === 'running' || found.some((one) => one.id === held.id))
    )
      quietly(refresh())
  })

  return {
    open,
    shown,
    records,
    record,
    photographs,
    show,
    refresh,
    openOn,
    toggle: () => (open.value = !open.value),
    close: () => (open.value = false),
  }
})
