<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { renderAt, renderDetail } from '../api'
import RefusalPage from '../components/RefusalPage.vue'
import type { RenderDetail } from '../types'

/* An image's large view (design spec J5·2): the image on `ground-media`, the
   sheet it was rendered from beside it — filled fields only, read-only. */
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

const place = computed(() => ({
  batch: props.batch,
  digest: props.digest,
  flow: props.flow,
  version: Number(props.version.replace(/^v/, '')),
  seed: props.seed,
}))

/* esc goes back to Renders. */
function onKey(event: KeyboardEvent): void {
  if (event.key !== 'Escape') return
  event.preventDefault()
  void router.push({ name: 'renders', params: { batch: props.batch } })
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
      <img :src="`${renderAt(place)}/image`" :alt="`seed ${detail.seed}`" />
    </div>
    <aside class="large__sheet" data-sheet>
      <span class="section-label">
        {{ detail.flow }} · v{{ detail.version }} · seed {{ detail.seed }}
      </span>
      <dl class="large__fields">
        <template v-for="(tags, name) in detail.fields" :key="name">
          <dt class="mono">{{ name }}</dt>
          <dd>{{ tags.join(' · ') }}</dd>
        </template>
      </dl>
      <RouterLink class="btn btn-secondary" :to="{ name: 'renders', params: { batch } }"
        >Back to Renders<span class="appbar__key">esc</span></RouterLink
      >
    </aside>
  </section>
</template>
