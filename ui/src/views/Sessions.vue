<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { thumbAt } from '../api'
import KeyBar from '../components/KeyBar.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { useBatchStore } from '../stores/batch'
import { clock, useLiveStore } from '../stores/live'
import type { SessionRecord } from '../types'
import { noun } from '../words'

/* A batch's render sessions, read from their records: the running one first,
   then newest first, each with its start, its duration against its limit, its
   outcome and its images. A row opens its session's page. */
const props = defineProps<{ batch: string }>()
const store = useBatchStore()
const { sessions } = storeToRefs(store)
const { now } = storeToRefs(useLiveStore())
const refusal = ref<string | null>(null)

/* The session's date and time on this machine's clock. */
const start = (at: string) =>
  new Date(at).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

/* Seconds from the start to the end, or to now while it runs; null once ended outright. */
function lasted(one: SessionRecord): number | null {
  if (one.ended) return (Date.parse(one.ended) - Date.parse(one.started)) / 1000
  if (one.outcome === 'running') return (now.value - Date.parse(one.started)) / 1000
  return null
}

const asked = (one: SessionRecord) => Object.values(one.asked).reduce((sum, n) => sum + n, 0)

onMounted(async () => {
  try {
    await store.reloadSessions()
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="sessions" class="sessions">
    <span class="section-label">Render sessions · {{ props.batch }}</span>
    <p v-if="!sessions.length" class="sessions__none">No render session has run for this batch.</p>
    <RouterLink
      v-for="one in sessions"
      :key="one.id"
      class="sessions__row"
      :data-session="one.id"
      :to="{ name: 'session', params: { batch: props.batch, id: one.id } }"
    >
      <span class="sessions__start mono">{{ start(one.started) }}</span>
      <span class="sessions__lasted mono"
        >{{ lasted(one) === null ? '—' : clock(lasted(one) ?? 0) }} of
        {{ clock(one.limit) }}</span
      >
      <span class="sessions__outcome" :data-outcome="one.outcome ?? 'ended'">{{
        one.outcome ?? 'ended, no outcome'
      }}</span>
      <span class="sessions__count mono"
        >{{ one.images.length }} of {{ asked(one) }} {{ noun(asked(one), 'image') }}</span
      >
      <span class="sessions__images">
        <span v-for="image in one.images" :key="`${image.digest}/${image.seed}`" class="session__tile session__tile--done">
          <img :src="thumbAt({ batch: props.batch, ...image })" alt="" loading="lazy" />
        </span>
      </span>
    </RouterLink>
    <KeyBar />
  </section>
</template>
