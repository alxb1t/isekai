<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { imageAt, photoUrl, renderDetail } from '../api'
import ImageViewer from '../components/ImageViewer.vue'
import KeyBar from '../components/KeyBar.vue'
import KeyHint from '../components/KeyHint.vue'
import RefusalPage from '../components/RefusalPage.vue'
import ReviseConfirm from '../components/ReviseConfirm.vue'
import { useKeys } from '../composables/useKeys'
import { plain, shifted } from '../stores/keys'
import type { RenderDetail } from '../types'

/* An image's large view (design spec J5·2): the image on `ground-media`, the
   sheet it was rendered from beside it — filled fields only, read-only. e
   revises it; c compares it with the newest older version of its seed (J5·8);
   ⇧C sets it beside its run's photograph. */
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
/* The image beside its run's photograph, in the viewer's pair. */
const pairing = ref(false)
const pair = computed(() => [
  { src: photoUrl(place.value), name: 'photograph' },
  { src: imageAt(place.value), name: `seed ${props.seed}` },
])

const place = computed(() => ({
  batch: props.batch,
  digest: props.digest,
  flow: props.flow,
  version: Number(props.version.replace(/^v/, '')),
  seed: props.seed,
}))

const clock = (at: number) =>
  new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

/* Compare carries where this view was opened from, so its esc returns here
   with the same way back. */
function compare(): void {
  void router.push({
    name: 'compare',
    params: { ...props },
    state: { from: window.history.state?.from ?? null },
  })
}

/* Where esc and the back button go: the hub when it opened this view, else
   Renders, which holds every image. A pasted address carries no state. */
const back = computed(() =>
  window.history.state?.from === 'hub'
    ? { to: { name: 'hub', params: { batch: props.batch } }, label: 'Back to Hub' }
    : { to: { name: 'renders', params: { batch: props.batch } }, label: 'Back to Renders' },
)

useKeys('screen', [
  {
    id: 'revise',
    keys: plain('KeyE'),
    label: 'revise',
    run: () => (revising.value = true),
  },
  {
    id: 'compare',
    keys: plain('KeyC'),
    label: 'compare',
    run: compare,
    when: () => Boolean(detail.value?.compare),
  },
  {
    id: 'side-by-side',
    keys: [shifted('KeyC')],
    label: 'side by side',
    run: () => (pairing.value = true),
  },
  {
    id: 'back',
    keys: plain('Escape'),
    label: 'back',
    run: () => void router.push(back.value.to),
  },
])

onMounted(async () => {
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
        ><template v-if="detail.damaged === null">
          · count {{ detail.count }}<template v-if="detail.seeds.length">
            · seeds {{ detail.seeds.join(', ') }}</template
          ></template
        ><template v-else> · damaged</template>
      </span>
      <p v-if="detail.damaged" class="renders__refusal">
        <span class="refusal__mark" />{{ detail.damaged }}
      </p>
      <dl class="large__fields">
        <template v-for="(tags, name) in detail.fields" :key="name">
          <dt class="mono">{{ name }}</dt>
          <dd>{{ tags.join(' · ') }}</dd>
        </template>
      </dl>
      <div class="large__actions">
        <button class="btn btn-secondary" type="button" data-revise @click="revising = true">
          Revise this image<KeyHint command="revise" />
        </button>
        <button
          v-if="detail.compare"
          class="btn btn-secondary"
          type="button"
          data-compare
          @click="compare"
        >
          Compare with v{{ detail.compare }}<KeyHint command="compare" />
        </button>
        <button class="btn btn-secondary" type="button" data-side-by-side @click="pairing = true">
          Side by side<KeyHint command="side-by-side" />
        </button>
        <RouterLink class="btn btn-secondary" :to="back.to"
          >{{ back.label }}<KeyHint command="back" /></RouterLink
        >
      </div>
      <KeyBar />
    </aside>
    <ImageViewer
      v-if="pairing"
      :images="pair"
      pair
      @close="pairing = false"
    />
    <ReviseConfirm
      v-if="revising"
      :batch="batch"
      :images="[{ digest, flow, version: place.version, seed }]"
      @close="revising = false"
    />
  </section>
</template>
