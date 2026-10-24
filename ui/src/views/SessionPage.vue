<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { imageAt, sourceAt, sourceThumbAt, thumbAt } from '../api'
import ImageViewer, { type Shown } from '../components/ImageViewer.vue'
import KeyBar from '../components/KeyBar.vue'
import KeyHint from '../components/KeyHint.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { asked, lasted, outcome } from '../sessions'
import { useBatchStore } from '../stores/batch'
import { alerting, clock, useLiveStore } from '../stores/live'

/* One render session (design spec J4·2, J4·3), from the record its verb writes.
   While the job slot runs it, the slot adds the volume steps and Stop, and the
   page is drawn from the slot until the verb has written the record. A finished
   image and each of the batch's photographs open in the viewer. No spend is
   shown after the quote. */
const props = defineProps<{ batch: string; id: string }>()
const store = useBatchStore()
const live = useLiveStore()
const { session: record, hub } = storeToRefs(store)
const { job, billing, now } = storeToRefs(live)
const refusal = ref<string | null>(null)
const stopRefusal = ref<string | null>(null)

/* The job slot's session, while it is this one. */
const slot = computed(() =>
  job.value?.kind === 'render' && job.value.batch === props.batch && job.value.session?.id === props.id
    ? job.value
    : null,
)
const running = computed(() => record.value?.outcome === 'running' || slot.value?.state === 'running')
const alert = computed(() => alerting(billing.value))

const started = computed(() => record.value?.started ?? slot.value?.session?.started ?? null)
const limit = computed(() => record.value?.limit ?? slot.value?.session?.limit ?? 0)
const of = computed(() => (record.value ? asked(record.value) : (slot.value?.session?.of ?? 0)))
const images = computed(() => record.value?.images ?? [])
const done = computed(() => images.value.length)
const steps = computed(() => record.value?.steps ?? {})
const volume = computed(() => slot.value?.session?.steps ?? {})

const elapsed = computed(() =>
  started.value
    ? lasted(
        started.value,
        record.value?.ended ?? slot.value?.session?.ended,
        running.value,
        now.value,
      )
    : null,
)

/* The five steps, always, each with its state. */
const shown = computed(() => {
  const rendering =
    of.value > 0 && done.value === of.value
      ? 'done'
      : steps.value.pod === 'ready' && running.value
        ? 'running'
        : ''
  return [
    { name: 'volume up', state: volume.value['volume up'] ?? '' },
    { name: 'pod boot', state: steps.value.pod ?? '' },
    { name: 'rendering', state: rendering, note: `image ${done.value} of ${of.value}` },
    { name: 'teardown', state: steps.value.teardown ?? '' },
    { name: 'volume down', state: volume.value['volume down'] ?? '' },
  ]
})

/* Only when both teardown steps are confirmed and gpunit holds nothing. */
const quiet = computed(
  () => steps.value.teardown === 'done' && volume.value['volume down'] === 'done' && !alert.value,
)
/* Why it failed: the record's word, else the job's before the record was written. */
const failure = computed(() =>
  record.value?.outcome === 'failed'
    ? record.value.message
    : slot.value?.state === 'failed'
      ? slot.value.message
      : null,
)
const ended = computed(() => (running.value || !record.value ? null : outcome(record.value)))

const thumbs = computed(() => images.value.map((one) => thumbAt({ batch: props.batch, ...one })))

/* What the viewer steps through: the finished images, or the batch's photographs. */
const viewing = ref<{ images: 'rendered' | 'sources'; start: number } | null>(null)
const sources = computed(() => hub.value?.sources ?? [])
const viewed = computed<Shown[]>(() =>
  viewing.value?.images === 'sources'
    ? sources.value.map((one) => ({
        src: sourceAt(props.batch, one.name),
        name: one.name,
        width: one.width,
        height: one.height,
      }))
    : images.value.map((one) => ({
        src: imageAt({ batch: props.batch, ...one }),
        name: `${one.flow} · v${one.version} · seed ${one.seed}`,
      })),
)

async function stop(): Promise<void> {
  try {
    await live.stop()
  } catch (reason) {
    stopRefusal.value = (reason as Error).message
  }
}

onMounted(async () => {
  try {
    await store.showSession(props.id)
  } catch (reason) {
    // The job has started and its verb has not written the record yet.
    if (!slot.value) refusal.value = (reason as Error).message
  }
})
</script>

<template>
  <RefusalPage v-if="refusal && !slot && !record" :refusal="refusal" />
  <section v-else-if="record || slot" class="session" :data-session-page="id">
    <span class="section-label">
      Render session · {{ batch }} · {{ of }} image{{ of === 1 ? '' : 's' }}
    </span>
    <p class="session__timer mono" data-session-timer>
      {{ elapsed === null ? '—' : clock(elapsed)
      }}<span class="session__limit"> of {{ clock(limit) }} at most</span>
    </p>
    <div class="session__bar">
      <span
        class="session__fill"
        :style="{ width: `${Math.min(100, ((elapsed ?? 0) / (limit || 1)) * 100)}%` }"
      />
    </div>
    <ol class="session__steps mono">
      <li v-for="step in shown" :key="step.name" :data-step="step.name" :data-state="step.state">
        <span class="session__mark" :class="`session__mark--${step.state || 'waiting'}`" />
        {{ step.name }}
        <span class="session__state">{{ step.note ?? step.state }}</span>
      </li>
    </ol>
    <div class="session__images">
      <template v-for="index in of" :key="index">
        <button
          v-if="thumbs[index - 1]"
          class="session__tile session__tile--done"
          type="button"
          :aria-label="`view image ${index}`"
          data-session-image
          @click="viewing = { images: 'rendered', start: index - 1 }"
        >
          <img :src="thumbs[index - 1]" alt="" />
        </button>
        <span v-else class="session__tile" />
      </template>
    </div>
    <span v-if="sources.length" class="section-label">Photographs</span>
    <div v-if="sources.length" class="session__images">
      <button
        v-for="(one, index) in sources"
        :key="one.name"
        class="session__tile session__tile--photo"
        type="button"
        :aria-label="`view ${one.name}`"
        data-session-source
        @click="viewing = { images: 'sources', start: index }"
      >
        <img :src="sourceThumbAt(batch, one.name)" alt="" loading="lazy" />
      </button>
    </div>
    <p v-if="failure" class="session__refusal"><span class="refusal__mark" />{{ failure }}</p>
    <p v-if="stopRefusal" class="session__refusal">
      <span class="refusal__mark" />{{ stopRefusal }}
    </p>
    <footer class="session__actions">
      <button v-if="slot?.state === 'running'" class="btn btn-secondary" type="button" @click="stop">
        Stop session now
      </button>
      <template v-if="!running">
        <span v-if="quiet" class="session__quiet" data-quiet>Nothing is billing.</span>
        <span v-if="ended" class="mono" data-outcome>{{ ended }}</span>
        <span class="mono">{{ done }} of {{ of }} rendered</span>
        <RouterLink class="btn btn-primary" data-renders :to="{ name: 'renders', params: { batch } }"
          >View in Renders<KeyHint command="renders" /></RouterLink
        >
      </template>
    </footer>
    <ImageViewer
      v-if="viewing && viewed.length"
      :images="viewed"
      :start="viewing.start"
      @close="viewing = null"
    />
    <KeyBar />
  </section>
</template>
