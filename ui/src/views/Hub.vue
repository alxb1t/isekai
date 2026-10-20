<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { hub } from '../api'
import RefusalPage from '../components/RefusalPage.vue'
import type { HubInfo } from '../types'

/* A batch's hub: its sources by its tracked flows. */
const props = defineProps<{ batch: string }>()
const info = ref<HubInfo | null>(null)
const refusal = ref<string | null>(null)

onMounted(async () => {
  try {
    info.value = await hub(props.batch)
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="info" class="home">
    <p class="section-label">{{ info.sources.length }} sources × {{ info.flows.length }} flows</p>
    <div v-for="source in info.sources" :key="source.name" class="library__row">
      <span class="library__name">{{ source.name }}</span>
      <template v-for="flow in info.flows" :key="flow">
        <RouterLink
          v-if="source.digest && source.cells[flow]?.status"
          :to="`/b/${batch}/review/${source.digest}/${flow}`"
          class="library__meta"
          >{{ flow }} · {{ source.cells[flow]?.stage }}</RouterLink
        >
      </template>
    </div>
  </section>
</template>
