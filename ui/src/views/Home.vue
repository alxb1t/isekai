<script setup lang="ts">
import { noun } from '../words'
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { library, sourceThumbAt } from '../api'
import ImportSheet from '../components/ImportSheet.vue'
import RefusalPage from '../components/RefusalPage.vue'
import type { LibraryRow } from '../types'

/* Home: every folder of the library, batches by their newest file first, the
   rest after them, inert (design spec J7·1). New batch opens the import sheet
   over it (J1); it sits in the library's header row, and on a first start under
   the privacy line (J1·1). */
const router = useRouter()
const rows = ref<LibraryRow[] | null>(null)
const batchCount = computed(() => rows.value?.filter((row) => row.batch).length ?? 0)
const refusal = ref<string | null>(null)
const list = ref<HTMLElement | null>(null)
const importing = ref(false)

function imported(batch: string): void {
  importing.value = false
  void router.push({ name: 'hub', params: { batch } })
}

/* ⌥N New batch. Matched on `event.code`: Option types a character on macOS. */
function onNew(event: KeyboardEvent): void {
  if (event.altKey && event.code === 'KeyN' && !importing.value) {
    event.preventDefault()
    importing.value = true
  }
}

/* Today's files read as a time, older ones as a date. */
function when(at: number | null): string {
  if (at === null) return ''
  const date = new Date(at * 1000)
  const today = new Date().toDateString() === date.toDateString()
  return today
    ? `today ${date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`
    : date.toISOString().slice(0, 10)
}

function open(row: LibraryRow): void {
  if (row.batch) void router.push({ name: 'hub', params: { batch: row.name } })
}

/* ↑↓ walk the batches, ↵ opens the focused one. */
function onKey(event: KeyboardEvent, row: LibraryRow): void {
  const cards = [...(list.value?.querySelectorAll<HTMLElement>('[data-batch]') ?? [])]
  const at = cards.indexOf(event.currentTarget as HTMLElement)
  if (event.key === 'Enter') open(row)
  else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    cards[Math.min(Math.max(at + (event.key === 'ArrowDown' ? 1 : -1), 0), cards.length - 1)]?.focus()
  }
}

onMounted(async () => {
  window.addEventListener('keydown', onNew)
  try {
    rows.value = (await library()).rows
  } catch (reason) {
    refusal.value = (reason as Error).message
    return
  }
  await nextTick()
  list.value?.querySelector<HTMLElement>('[data-batch]')?.focus()
})

onUnmounted(() => window.removeEventListener('keydown', onNew))
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="rows" class="home">
    <ImportSheet v-if="importing" @close="importing = false" @imported="imported" />
    <div v-if="rows.length === 0" class="home__empty">
      <p class="section-label">library · empty</p>
      <p>No batches yet.</p>
      <p>
        Sources are copied into ~/isekai/. A photograph leaves this Mac only to be rendered:
        metadata stripped, held only in the GPU pod's memory, and gone when the pod is.
      </p>
      <button class="btn btn-primary" type="button" @click="importing = true">
        New batch<span class="appbar__key">⌥N</span>
      </button>
    </div>
    <template v-else>
      <div class="home__head">
        <p class="section-label">
          library · {{ batchCount }} {{ noun(batchCount, 'batch', 'batches') }} · newest activity
          first
        </p>
        <button class="btn btn-primary" type="button" @click="importing = true">
          New batch<span class="appbar__key">⌥N</span>
        </button>
      </div>
      <div ref="list" class="library">
        <template v-for="row in rows" :key="row.name">
          <div
            v-if="row.batch"
            class="library__row"
            data-batch
            tabindex="0"
            @click="open(row)"
            @keydown="onKey($event, row)"
          >
            <span class="library__name">{{ row.name }}</span>
            <div class="library__sources">
              <span class="library__meta">{{ row.sources }} {{ noun(row.sources, 'source') }}</span>
              <span v-if="row.thumbs.length" class="library__thumbs">
                <img
                  v-for="name in row.thumbs"
                  :key="name"
                  class="library__thumb"
                  :src="sourceThumbAt(row.name, name)"
                  alt=""
                  loading="lazy"
                />
                <span v-if="row.sources > row.thumbs.length" class="library__meta">
                  +{{ row.sources - row.thumbs.length }}
                </span>
              </span>
            </div>
            <div class="library__chips">
              <span v-for="one in row.flows" :key="one.flow" class="library__chip">
                {{ one.flow }} {{ one.approved }}/{{ one.of }} approved ·
                {{ one.rendered }}/{{ one.of }} rendered
              </span>
              <span v-if="row.without_flow" class="library__meta">
                {{ row.without_flow }} {{ noun(row.without_flow, 'source') }} without a flow
              </span>
            </div>
            <span class="library__meta library__when">
              {{ when(row.newest) }}<template v-if="row.kind"> · {{ row.kind }}</template>
              <br />open ↵
            </span>
          </div>
          <div v-else class="library__row library__row--inert">
            <span class="library__name">{{ row.name }}</span>
            <span class="library__reason" style="grid-column: span 2">
              Not a batch: no sources/ folder inside. Move it out of ~/isekai/ in Finder to clear
              this row.
            </span>
            <span class="library__reason library__when">can't be opened</span>
          </div>
        </template>
      </div>
    </template>
  </section>
</template>
