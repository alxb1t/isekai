<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { renderAt, renders } from '../api'
import RefusalPage from '../components/RefusalPage.vue'
import type { RendersInfo } from '../types'

/* Renders: a grid of sources by flows, each cell's approvals newest first with
   their images (design spec J5·1). ↵ or a click opens an image's large view. */
const props = defineProps<{ batch: string }>()
const router = useRouter()
const info = ref<RendersInfo | null>(null)
const refusal = ref<string | null>(null)

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
  try {
    info.value = await renders(props.batch)
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
})
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
      <template v-for="source in info.sources" :key="source.name">
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
