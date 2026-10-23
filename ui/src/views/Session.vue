<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { thumbAt } from '../api'
import { alerting, clock, useLiveStore } from '../stores/live'

/* The render session (design spec J4·2, J4·3), and the billing alert's way out
   (J8b). It exists only while a render's session is in the slot or an alert is
   open; otherwise it is Home. No spend is shown after the quote. */
const router = useRouter()
const live = useLiveStore()
const { job, billing, loaded, now } = storeToRefs(live)
const refusal = ref<string | null>(null)

const session = computed(() => (job.value?.kind === 'render' ? job.value.session : undefined))
const running = computed(() => job.value?.kind === 'render' && job.value.state === 'running')
const alert = computed(() => alerting(billing.value))
/* Counted to the job's end once it has one, so a finished session's clock stops. */
const elapsed = computed(() => {
  const held = session.value
  if (!held) return 0
  const until = held.ended ? Date.parse(held.ended) : now.value
  return (until - Date.parse(held.started)) / 1000
})

function thumb(index: number): string | null {
  const image = session.value?.images[index]
  if (!image || !job.value) return null
  return thumbAt({ batch: job.value.batch, ...image })
}
const done = computed(() => session.value?.images.length ?? 0)

/* The five steps, always, each with its state. */
const steps = computed(() => {
  const held = session.value
  if (!held) return []
  const of = held.of
  const rendering = done.value === of ? 'done' : held.steps.pod === 'ready' ? 'running' : ''
  return [
    { name: 'volume up', state: held.steps['volume up'] },
    { name: 'pod boot', state: held.steps.pod },
    { name: 'rendering', state: rendering, note: `image ${done.value} of ${of}` },
    { name: 'teardown', state: held.steps.teardown },
    { name: 'volume down', state: held.steps['volume down'] },
  ]
})

/* Only when both teardown steps are confirmed and gpunit holds nothing. */
const quiet = computed(
  () =>
    session.value?.steps.teardown === 'done' &&
    session.value.steps['volume down'] === 'done' &&
    !alert.value,
)

async function stop(): Promise<void> {
  try {
    await live.stop()
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
}

async function check(): Promise<void> {
  try {
    await live.checkBilling()
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
}

watch(
  [loaded, session, alert],
  () => {
    if (loaded.value && !session.value && !alert.value) void router.replace({ name: 'home' })
  },
  { immediate: true },
)

</script>

<template>
  <section class="session">
    <p v-if="refusal" class="session__refusal"><span class="refusal__mark" />{{ refusal }}</p>
    <template v-if="session">
      <span class="section-label">
        Render session · {{ job?.batch }} · {{ session.of }} image{{ session.of === 1 ? '' : 's' }}
      </span>
      <p class="session__timer mono" data-session-timer>
        {{ clock(elapsed) }}<span class="session__limit"> of {{ clock(session.limit) }} at most</span>
      </p>
      <div class="session__bar">
        <span
          class="session__fill"
          :style="{ width: `${Math.min(100, (elapsed / session.limit) * 100)}%` }"
        />
      </div>
      <ol class="session__steps mono">
        <li v-for="step in steps" :key="step.name" :data-step="step.name" :data-state="step.state">
          <span class="session__mark" :class="`session__mark--${step.state || 'waiting'}`" />
          {{ step.name }}
          <span class="session__state">{{ step.note ?? step.state }}</span>
        </li>
      </ol>
      <div class="session__images">
        <span
          v-for="index in session.of"
          :key="index"
          class="session__tile"
          :class="{ 'session__tile--done': index <= done }"
        >
          <img v-if="thumb(index - 1)" :src="thumb(index - 1) ?? ''" alt="" />
        </span>
      </div>
      <p v-if="job?.state === 'failed'" class="session__refusal">
        <span class="refusal__mark" />{{ job.message }}
      </p>
      <footer class="session__actions">
        <button v-if="running" class="btn btn-secondary" type="button" @click="stop">
          Stop session now
        </button>
        <template v-else>
          <span v-if="quiet" class="session__quiet" data-quiet>Nothing is billing.</span>
          <span class="mono">{{ done }} of {{ session.of }} rendered</span>
          <RouterLink
            v-if="job"
            class="btn btn-primary"
            data-renders
            :to="{ name: 'renders', params: { batch: job.batch } }"
            >View in Renders<span class="appbar__key">⌥3</span></RouterLink
          >
        </template>
      </footer>
    </template>
    <div v-if="alert && !running" class="session__alert">
      <p v-if="billing?.pod">
        <span class="refusal__mark" />A pod may still be billing.
        <span class="mono">uv run --env-file .env gpunit down</span>, or stop it in RunPod's
        console, then Check again.
      </p>
      <p v-if="billing?.volume?.state === 'band'">
        <span class="refusal__mark" />The window volume may still be billing.
        <span class="mono">uv run --env-file .env gpunit volume down</span>, then Check again.
      </p>
      <button class="btn btn-primary" type="button" @click="check">Check again</button>
    </div>
  </section>
</template>
