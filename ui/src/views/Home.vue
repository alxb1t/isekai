<script setup lang="ts">
import { noun } from '../words'
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { library, sourceThumbAt } from '../api'
import ImportSheet from '../components/ImportSheet.vue'
import KeyBar from '../components/KeyBar.vue'
import KeyHint from '../components/KeyHint.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { useKeys } from '../composables/useKeys'
import { plain, shifted } from '../stores/keys'
import type { LibraryRow } from '../types'

/* Home: every folder of the library, batches by their newest file first, the
   rest after them, inert (design spec J7·1). New batch opens the import sheet
   over it (J1); it sits in the library's header row, and on a first start under
   the privacy line (J1·1). */
const router = useRouter()
const rows = ref<LibraryRow[] | null>(null)
const batches = computed(() => rows.value?.filter((row) => row.batch) ?? [])
const batchCount = computed(() => batches.value.length)
const refusal = ref<string | null>(null)
const list = ref<HTMLElement | null>(null)
const importing = ref(false)

function imported(batch: string): void {
  importing.value = false
  void router.push({ name: 'hub', params: { batch } })
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

/* The batch rows, and the one holding the focus, or -1. */
function cards(): HTMLElement[] {
  return [...(list.value?.querySelectorAll<HTMLElement>('[data-batch]') ?? [])]
}
const at = () => cards().indexOf(document.activeElement as HTMLElement)

function walk(step: -1 | 1): void {
  const held = cards()
  held[Math.min(Math.max(at() + step, 0), held.length - 1)]?.focus()
}

const onRow = () => at() >= 0

/* j k or ↓ ↑ walk the batches, ↵ opens the focused one (D25). */
useKeys('screen', [
  {
    id: 'new',
    keys: [shifted('KeyN')],
    label: 'new batch',
    run: () => (importing.value = true),
  },
  {
    id: 'next',
    keys: plain('KeyJ', 'ArrowDown'),
    label: 'next batch',
    run: () => walk(1),
  },
  {
    id: 'previous',
    keys: plain('KeyK', 'ArrowUp'),
    label: 'previous batch',
    run: () => walk(-1),
  },
  {
    id: 'open',
    keys: plain('Enter'),
    label: 'open the batch',
    run: () => open(batches.value[at()]),
    when: onRow,
  },
])

onMounted(async () => {
  try {
    rows.value = (await library()).rows
  } catch (reason) {
    refusal.value = (reason as Error).message
    return
  }
  await nextTick()
  list.value?.querySelector<HTMLElement>('[data-batch]')?.focus()
})
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
        New batch<KeyHint command="new" />
      </button>
    </div>
    <template v-else>
      <div class="home__head">
        <p class="section-label">
          library · {{ batchCount }} {{ noun(batchCount, 'batch', 'batches') }} · newest activity
          first
        </p>
        <button class="btn btn-primary" type="button" @click="importing = true">
          New batch<KeyHint command="new" />
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
    <KeyBar />
  </section>
</template>
