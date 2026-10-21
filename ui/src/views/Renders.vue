<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { renderAt, renders } from '../api'
import RefusalPage from '../components/RefusalPage.vue'
import type { RendersInfo } from '../types'

/* Renders: a grid of sources by flows, each cell's approvals newest first with
   their images (design spec J5·1). ←→ move along a source's images, ↑↓ between
   sources, and ↵ or a click opens an image's large view (§7). */
const props = defineProps<{ batch: string }>()
const router = useRouter()
const info = ref<RendersInfo | null>(null)
const refusal = ref<string | null>(null)
const focus = ref<{ row: number; column: number }>({ row: 0, column: 0 })

interface Spot {
  digest: string
  flow: string
  version: number
  seed: string
}

/* Each source's images in the order they are drawn: flow, newest version, seed. */
const rows = computed<Spot[][]>(() => {
  const held = info.value
  if (!held) return []
  return held.sources.map((source) =>
    source.digest === null
      ? []
      : held.flows.flatMap((flow) =>
          (source.cells[flow] ?? []).flatMap((version) =>
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
  if (event.altKey || event.metaKey || event.ctrlKey) return
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

const clock = (at: number) =>
  new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

function thumb(digest: string, flow: string, version: number, seed: string): string {
  return `${renderAt({ batch: props.batch, digest, flow, version, seed })}/thumb`
}

function open(digest: string, flow: string, version: number, seed: string): void {
  void router.push({
    name: 'render',
    params: { batch: props.batch, digest, flow, version: `v${version}`, seed },
  })
}

onMounted(async () => {
  window.addEventListener('keydown', onKey)
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
    <div
      class="renders__grid"
      :style="{ gridTemplateColumns: `250px repeat(${info.flows.length}, 1fr)` }"
    >
      <span class="section-label">source</span>
      <span v-for="flow in info.flows" :key="flow" class="section-label">{{ flow }}</span>
      <template v-for="(source, row) in info.sources" :key="source.name">
        <span class="renders__name mono">{{ source.name }}</span>
        <div v-for="flow in info.flows" :key="flow" class="renders__cell">
          <div
            v-for="version in source.cells[flow] ?? []"
            :key="version.version"
            class="renders__version"
            :data-version="version.version"
          >
            <span class="renders__head mono">
              v{{ version.version }} · approved {{ clock(version.at) }} · count
              {{ version.count }}<template v-if="version.seeds.length">
                · seeds {{ version.seeds.join(', ') }}</template
              >
            </span>
            <span class="renders__images">
              <button
                v-for="seed in version.rendered"
                :key="seed"
                class="renders__image"
                :class="{
                  'renders__image--focused': focused === spot(row, flow, version.version, seed),
                }"
                type="button"
                :data-seed="seed"
                @click="source.digest && open(source.digest, flow, version.version, seed)"
              >
                <img
                  v-if="source.digest"
                  :src="thumb(source.digest, flow, version.version, seed)"
                  :alt="`${source.name} ${flow} v${version.version} seed ${seed}`"
                />
              </button>
            </span>
          </div>
        </div>
      </template>
    </div>
  </section>
</template>
