<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { bar } from '../bars'
import { renders, sourceAt, sourceThumbAt, thumbAt } from '../api'
import ImageViewer from '../components/ImageViewer.vue'
import RefusalPage from '../components/RefusalPage.vue'
import RenderBar from '../components/RenderBar.vue'
import RenderDialog from '../components/RenderDialog.vue'
import ReviseConfirm from '../components/ReviseConfirm.vue'
import { useLive } from '../composables/useLive'
import { useRenderOffer } from '../composables/useRenderOffer'
import { noun } from '../words'
import type { RenderVersion, RendersInfo, RevisedImage } from '../types'

/* Renders: a grid of sources by flows, each cell one row of its images from
   oldest to newest, each marked with its version (design spec J5·1). ←→ move
   along a source's images, ↑↓ between sources, and ↵ or a click opens an image's
   large view; space selects, and ⌥E revises the selection (§7). A seed rendered
   under two versions is marked ⇄. The Render bar offers what the newest
   approvals lack, ⌥R; a source's thumbnail opens it in the viewer. */
const props = defineProps<{ batch: string }>()
const router = useRouter()
const info = ref<RendersInfo | null>(null)
const refusal = ref<string | null>(null)
const focus = ref<{ row: number; column: number }>({ row: 0, column: 0 })
/* The selected images, each as `key` spells it. */
const selected = ref(new Set<string>())
const revising = ref(false)
/* The source open in the viewer, by name, or null. */
const viewing = ref<string | null>(null)
const { job, renderRunning } = useLive()
const { offer, dialog, check: checkRender, open: openRender, close } = useRenderOffer(props.batch)
const shown = computed(() =>
  bar({ changes: 0, preparing: false, images: offer.value.images, rendering: renderRunning.value }),
)

interface Spot {
  digest: string
  flow: string
  version: number
  seed: string
}

/* Each cell's versions as they are drawn, oldest first, by source row then flow.
   The payload lists them newest first, which a living scenario holds. */
const oldest = computed<Record<string, RenderVersion[]>[]>(() =>
  (info.value?.sources ?? []).map((source) =>
    Object.fromEntries(
      (info.value?.flows ?? []).map((flow) => [flow, [...(source.cells[flow] ?? [])].reverse()]),
    ),
  ),
)

/* Each source's images in the order they are drawn: flow, oldest version, seed. */
const rows = computed<Spot[][]>(() => {
  const held = info.value
  if (!held) return []
  return held.sources.map((source, row) =>
    source.digest === null
      ? []
      : held.flows.flatMap((flow) =>
          oldest.value[row][flow].flatMap((version) =>
            version.rendered.map((seed) => ({
              digest: source.digest as string,
              flow,
              version: version.version,
              seed,
            })),
          ),
        ),
  )
})

/* The focused image, as `spot` spells it. e.g. "0|summon-anime-wai|1|42" */
const focused = computed(() => {
  const here = rows.value[focus.value.row]?.[focus.value.column]
  return here ? spot(focus.value.row, here.flow, here.version, here.seed) : ''
})

function spot(row: number, flow: string, version: number, seed: string): string {
  return `${row}|${flow}|${version}|${seed}`
}

/* An image as the selection holds it. e.g. "0d4b…|summon-anime-wai|1|42" */
const key = (one: Spot) => `${one.digest}|${one.flow}|${one.version}|${one.seed}`

const chosen = computed<RevisedImage[]>(() =>
  rows.value.flat().filter((one) => selected.value.has(key(one))),
)

function toggle(one: Spot): void {
  const next = new Set(selected.value)
  if (!next.delete(key(one))) next.add(key(one))
  selected.value = next
}

/* The seeds each cell renders under more than one version, by `digest|flow`. */
const shared = computed(() => {
  const found = new Map<string, Set<string>>()
  for (const source of info.value?.sources ?? [])
    for (const [flow, versions] of Object.entries(source.cells))
      found.set(`${source.digest}|${flow}`, repeated(versions))
  return found
})

function repeated(versions: RenderVersion[]): Set<string> {
  const seen = new Map<string, number>()
  for (const version of versions)
    for (const seed of version.rendered) seen.set(seed, (seen.get(seed) ?? 0) + 1)
  return new Set([...seen].filter(([, count]) => count > 1).map(([seed]) => seed))
}

function move(rowStep: number, columnStep: number): void {
  const held = rows.value
  const filled = held.map((one, index) => (one.length ? index : -1)).filter((one) => one >= 0)
  if (!filled.length) return
  let { row, column } = focus.value
  if (rowStep) {
    const at = filled.indexOf(row)
    row = filled[Math.min(Math.max(at + rowStep, 0), filled.length - 1)]
  }
  column = Math.min(Math.max(column + columnStep, 0), held[row].length - 1)
  focus.value = { row, column }
  void nextTick(() =>
    document.querySelector<HTMLElement>('.renders__image--focused')?.scrollIntoView({ block: 'nearest' }),
  )
}

function onKey(event: KeyboardEvent): void {
  if (revising.value || dialog.value || viewing.value) return
  // Matched on `event.code`: ⌥E types a character.
  if (event.altKey && event.code === 'KeyE') {
    event.preventDefault()
    if (chosen.value.length) revising.value = true
    return
  }
  if (event.altKey && event.code === 'KeyR') {
    event.preventDefault()
    openRender()
    return
  }
  if (event.altKey || event.metaKey || event.ctrlKey) return
  if (event.key === ' ') {
    const here = rows.value[focus.value.row]?.[focus.value.column]
    if (here) {
      event.preventDefault()
      toggle(here)
    }
    return
  }
  const steps: Record<string, [number, number]> = {
    ArrowUp: [-1, 0],
    ArrowDown: [1, 0],
    ArrowLeft: [0, -1],
    ArrowRight: [0, 1],
  }
  const step = steps[event.key]
  if (step) {
    event.preventDefault()
    move(...step)
  } else if (event.key === 'Enter') {
    const spot = rows.value[focus.value.row]?.[focus.value.column]
    if (spot) {
      event.preventDefault()
      open(spot.digest, spot.flow, spot.version, spot.seed)
    }
  }
}

function thumb(digest: string, flow: string, version: number, seed: string): string {
  return thumbAt({ batch: props.batch, digest, flow, version, seed })
}

function open(digest: string, flow: string, version: number, seed: string): void {
  void router.push({
    name: 'render',
    params: { batch: props.batch, digest, flow, version: `v${version}`, seed },
  })
}

/* A job that ends changes the images. */
watch(job, (slot, before) => {
  if (before?.state === 'running' && slot?.state !== 'running')
    void renders(props.batch).then((read) => (info.value = read))
})

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  void checkRender()
  try {
    info.value = await renders(props.batch)
  } catch (reason) {
    refusal.value = (reason as Error).message
    return
  }
  const first = rows.value.findIndex((one) => one.length > 0)
  if (first >= 0) focus.value = { row: first, column: 0 }
})
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="info" class="renders">
    <div class="renders__bar">
      <button
        class="btn btn-secondary"
        type="button"
        data-revise
        :disabled="!chosen.length"
        @click="revising = true"
      >
        Revise {{ chosen.length || '' }}<span class="appbar__key">⌥E</span>
      </button>
      <span v-if="!chosen.length" class="renders__reason">No image selected</span>
    </div>
    <div
      class="renders__grid"
      :style="{ gridTemplateColumns: `250px repeat(${info.flows.length}, 1fr)` }"
    >
      <span class="section-label">source</span>
      <span v-for="flow in info.flows" :key="flow" class="section-label">{{ flow }}</span>
      <template v-for="(source, row) in info.sources" :key="source.name">
        <div class="renders__source">
          <button
            class="hub__thumb"
            type="button"
            :aria-label="`view ${source.name}`"
            data-source-thumb
            @click="viewing = source.name"
          >
            <img :src="sourceThumbAt(batch, source.name)" alt="" loading="lazy" />
          </button>
          <span class="renders__name mono">{{ source.name }}</span>
        </div>
        <div v-for="flow in info.flows" :key="flow" class="renders__cell">
          <span class="renders__images">
            <template v-for="version in oldest[row][flow]" :key="version.version">
              <span
                v-if="version.damaged"
                class="renders__image renders__image--damaged"
                :data-version="version.version"
                data-damaged
              >
                <span class="renders__badge mono">v{{ version.version }}</span>
              </span>
              <button
                v-for="seed in version.rendered"
                v-else
                :key="seed"
                class="renders__image"
                :class="{
                  'renders__image--focused': focused === spot(row, flow, version.version, seed),
                  'renders__image--selected':
                    source.digest &&
                    selected.has(
                      key({ digest: source.digest, flow, version: version.version, seed }),
                    ),
                }"
                type="button"
                :data-version="version.version"
                :data-seed="seed"
                @click="source.digest && open(source.digest, flow, version.version, seed)"
              >
                <img
                  v-if="source.digest"
                  :src="thumb(source.digest, flow, version.version, seed)"
                  :alt="`${source.name} ${flow} v${version.version} seed ${seed}`"
                />
                <span class="renders__badge mono"
                  >v{{ version.version }}
                  <span
                    v-if="shared.get(`${source.digest}|${flow}`)?.has(seed)"
                    class="renders__shared"
                    data-shared
                    >⇄</span
                  ></span
                >
              </button>
            </template>
            <span
              v-if="(source.ready[flow] ?? 0) > 0"
              class="renders__image renders__image--ready mono"
              data-ready
              >ready · {{ source.ready[flow] }} {{ noun(source.ready[flow], 'image') }}</span
            >
          </span>
          <p
            v-for="version in oldest[row][flow].filter((one) => one.damaged)"
            :key="version.version"
            class="renders__refusal"
          >
            <span class="refusal__mark" />v{{ version.version }} · {{ version.damaged }}
          </p>
        </div>
      </template>
    </div>
    <ImageViewer
      v-if="viewing"
      :src="sourceAt(batch, viewing)"
      :name="viewing"
      @close="viewing = null"
    />
    <ReviseConfirm
      v-if="revising"
      :batch="batch"
      :images="chosen"
      @close="revising = false"
    />
    <RenderBar
      v-if="shown === 'render'"
      :images="offer.images"
      :disabled="offer.disabled"
      @open="openRender"
    />
    <RenderDialog v-if="dialog" :batch="batch" @close="close" />
  </section>
</template>
