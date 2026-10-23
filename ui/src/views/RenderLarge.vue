<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { imageAt, renderDetail } from '../api'
import RefusalPage from '../components/RefusalPage.vue'
import ReviseConfirm from '../components/ReviseConfirm.vue'
import type { RenderDetail } from '../types'

/* An image's large view (design spec J5·2): the image on `ground-media`, the
   sheet it was rendered from beside it — filled fields only, read-only. ⌥E
   revises it; C compares it with the newest older version of its seed (J5·8). */
const props = defineProps<{
  batch: string
  digest: string
  flow: string
  version: string
  seed: string
}>()
const router = useRouter()
const detail = ref<RenderDetail | null>(null)
const refusal = ref<string | null>(null)
const revising = ref(false)

const place = computed(() => ({
  batch: props.batch,
  digest: props.digest,
  flow: props.flow,
  version: Number(props.version.replace(/^v/, '')),
  seed: props.seed,
}))

const clock = (at: number) =>
  new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

function compare(): void {
  void router.push({ name: 'compare', params: { ...props } })
}

/* Where esc and the back button go: the hub when it opened this view, else
   Renders, which holds every image. A pasted address carries no state. */
const back = computed(() =>
  window.history.state?.from === 'hub'
    ? { to: { name: 'hub', params: { batch: props.batch } }, label: 'Back to Hub' }
    : { to: { name: 'renders', params: { batch: props.batch } }, label: 'Back to Renders' },
)

/* Matched on `event.code`: ⌥E types a character. */
function onKey(event: KeyboardEvent): void {
  if (revising.value) return
  if (event.altKey && event.code === 'KeyE') {
    event.preventDefault()
    revising.value = true
  } else if (
    event.code === 'KeyC' &&
    !event.altKey &&
    !event.metaKey &&
    !event.ctrlKey &&
    detail.value?.compare
  ) {
    event.preventDefault()
    compare()
  } else if (event.key === 'Escape') {
    event.preventDefault()
    void router.push(back.value.to)
  }
}

onUnmounted(() => window.removeEventListener('keydown', onKey))
onMounted(async () => {
  window.addEventListener('keydown', onKey)
  try {
    detail.value = await renderDetail(place.value)
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="detail" class="large">
    <div class="large__media">
      <img :src="imageAt(place)" :alt="`seed ${detail.seed}`" />
    </div>
    <aside class="large__sheet" data-sheet>
      <span class="section-label">
        {{ detail.flow }} · v{{ detail.version }} · seed {{ detail.seed }}
      </span>
      <span class="large__head mono" data-heading>
        v{{ detail.version }}<template v-if="detail.kind">
          · {{ detail.kind }} of v{{ detail.came_from }}</template
        ><template v-if="detail.approved_at !== null">
          · approved {{ clock(detail.approved_at) }}</template
        >
        · count {{ detail.count }}<template v-if="detail.seeds.length">
          · seeds {{ detail.seeds.join(', ') }}</template
        >
      </span>
      <dl class="large__fields">
        <template v-for="(tags, name) in detail.fields" :key="name">
          <dt class="mono">{{ name }}</dt>
          <dd>{{ tags.join(' · ') }}</dd>
        </template>
      </dl>
      <div class="large__actions">
        <button class="btn btn-secondary" type="button" data-revise @click="revising = true">
          Revise this image<span class="appbar__key">⌥E</span>
        </button>
        <button
          v-if="detail.compare"
          class="btn btn-secondary"
          type="button"
          data-compare
          @click="compare"
        >
          Compare with v{{ detail.compare }}<span class="appbar__key">C</span>
        </button>
        <RouterLink class="btn btn-secondary" :to="back.to"
          >{{ back.label }}<span class="appbar__key">esc</span></RouterLink
        >
      </div>
    </aside>
    <ReviseConfirm
      v-if="revising"
      :batch="batch"
      :images="[{ digest, flow, version: place.version, seed }]"
      @close="revising = false"
    />
  </section>
</template>
