<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { renderDetail, tattoos, thumbAt, versionOf } from '../api'
import OutlineStep from '../components/OutlineStep.vue'
import RefusalPage from '../components/RefusalPage.vue'
import TattooPicker from '../components/TattooPicker.vue'
import type { RenderDetail, TattooList } from '../types'

/* The placement screen (design spec J9): the render it places on, the steps built, and
   the step's component by the route. It stays mounted as the step changes, and holds the
   kept tattoos both steps read. It declares no key: the app-wide ones stay. */
const props = defineProps<{
  collection: string
  digest: string
  flow: string
  version: string
  seed: string
  step: 'tattoo' | 'outline'
  name?: string
}>()
const router = useRouter()
const route = useRoute()

const detail = ref<RenderDetail | null>(null)
const list = ref<TattooList | null>(null)
const refusal = ref<string | null>(null)

const render = computed(() => ({
  collection: props.collection,
  digest: props.digest,
  flow: props.flow,
  version: props.version,
  seed: props.seed,
}))
const place = computed(() => ({
  collection: props.collection,
  digest: props.digest,
  flow: props.flow,
}))
const instead = computed(() =>
  typeof route.query.instead === 'string' ? route.query.instead : null,
)
const back = computed(() => ({ name: 'render', params: render.value }))
const picking = computed(() => ({ name: 'place', params: { ...render.value, step: 'tattoo' } }))
const outlining = computed(() =>
  props.name ? { name: 'place', params: { ...render.value, step: 'outline', name: props.name } } : null,
)

async function refresh(): Promise<void> {
  list.value = await tattoos()
}

function choose(name: string): void {
  void router.push({ name: 'place', params: { ...render.value, step: 'outline', name } })
}

async function kept(name: string): Promise<void> {
  try {
    await refresh()
  } catch (reason) {
    refusal.value = (reason as Error).message
    return
  }
  choose(name)
}

function uploadInstead(cut: string): void {
  void router.push({ ...picking.value, query: { instead: cut } })
}

/* An outline step with no tattoo named goes back to the picker. */
watch(
  () => [props.step, props.name],
  () => {
    if (props.step === 'outline' && !props.name) void router.replace(picking.value)
  },
  { immediate: true },
)

/* The picker shows each tattoo's state as the outline step left it. */
watch(
  () => props.step,
  (now) => {
    if (now === 'tattoo' && list.value) void refresh().catch(() => undefined)
  },
)

onMounted(async () => {
  try {
    const own = { ...render.value, version: versionOf(props.version) }
    const [shown, listed] = await Promise.all([renderDetail(own), tattoos()])
    detail.value = shown
    list.value = listed
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="detail && list" class="place">
    <header class="place__head">
      <img
        class="place__render"
        :src="thumbAt({ ...render, version: versionOf(version) })"
        :alt="`seed ${detail.seed}`"
      />
      <span class="section-label">
        place a tattoo · {{ detail.flow }} · v{{ detail.version }} · seed {{ detail.seed }}
      </span>
      <nav class="place__steps" aria-label="steps">
        <RouterLink class="place__step" :class="{ 'place__step--on': step === 'tattoo' }" :to="picking">
          ① tattoo
        </RouterLink>
        <RouterLink
          v-if="outlining"
          class="place__step"
          :class="{ 'place__step--on': step === 'outline' }"
          :to="outlining"
        >
          ② outline
        </RouterLink>
        <span v-else class="place__step place__step--wait">② outline</span>
      </nav>
      <RouterLink class="btn btn-secondary place__back" :to="back">Back to the render</RouterLink>
    </header>
    <TattooPicker
      v-if="step === 'tattoo'"
      :place="place"
      :list="list"
      :instead="instead"
      @choose="choose"
      @kept="kept"
    />
    <OutlineStep
      v-else-if="name"
      :key="name"
      :place="place"
      :name="name"
      :limits="list.limits"
      @instead="uploadInstead"
    />
  </section>
</template>
