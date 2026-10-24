<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { thumbAt } from '../api'
import KeyBar from '../components/KeyBar.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { useBatchStore } from '../stores/batch'
import { asked, lasted, outcome } from '../sessions'
import { clock, useLiveStore } from '../stores/live'
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

/* Each session as its row draws it. */
const rows = computed(() =>
  (sessions.value ?? []).map((one) => {
    const seconds = lasted(one.started, one.ended, one.outcome === 'running', now.value)
    return {
      one,
      lasted: seconds === null ? '—' : clock(seconds),
      of: asked(one),
      outcome: outcome(one),
    }
  }),
)

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
      v-for="{ one, lasted: took, of, outcome: ended } in rows"
      :key="one.id"
      class="sessions__row"
      :data-session="one.id"
      :to="{ name: 'session', params: { batch: props.batch, id: one.id } }"
    >
      <span class="sessions__start mono">{{ start(one.started) }}</span>
      <span class="sessions__lasted mono">{{ took }} of {{ clock(one.limit) }}</span>
      <span class="sessions__outcome" :data-outcome="one.outcome ?? 'ended'">{{ ended }}</span>
      <span class="sessions__count mono"
        >{{ one.images.length }} of {{ of }} {{ noun(of, 'image') }}</span
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
