<script setup lang="ts">
import { computed, onMounted, onUnmounted, provide, ref, watch } from 'vue'
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router'
import { renderDetail, tattoos, thumbAt, versionOf } from '../api'
import { PLACING, usePlacing } from '../composables/usePlacing'
import LeaveDialog from '../components/LeaveDialog.vue'
import OutlineStep from '../components/OutlineStep.vue'
import RefusalPage from '../components/RefusalPage.vue'
import ReviewBake from '../components/ReviewBake.vue'
import StagePhoto from '../components/StagePhoto.vue'
import StageRender from '../components/StageRender.vue'
import TattooPicker from '../components/TattooPicker.vue'
import { type Ask, type Stage, asks, left } from '../leave'
import { complete } from '../pairs'
import { type Step, circled, shortStep, skipped, stepsOf } from '../stages'
import type { RenderDetail, TattooList } from '../types'

/* The placement screen (design spec J9): the render it places on, the steps built, and
   the step's component by the route. It stays mounted as the step changes, and holds the
   kept tattoos and what the stages place, which every step reads. It declares no key: the
   app-wide ones stay. */
const props = defineProps<{
  collection: string
  digest: string
  flow: string
  version: string
  seed: string
  step: Step
  name?: string
}>()
const router = useRouter()
const route = useRoute()

const detail = ref<RenderDetail | null>(null)
const list = ref<TattooList | null>(null)
const refusal = ref<string | null>(null)

const placing = usePlacing({ collection: props.collection, digest: props.digest, flow: props.flow })
provide(PLACING, placing)

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
const steps = computed(() => (props.name && placing.mode.value ? stepsOf(placing.mode.value) : null))
const at = (step: Step) => ({
  name: 'place',
  params: { ...render.value, step, name: props.name },
})

/* The list is read after the saves on their way, so a card never sends pairs older than the file. */
async function refresh(): Promise<void> {
  list.value = await placing.after(() => tattoos(props.digest))
}

function choose(name: string, step: Step): void {
  void router.push({ name: 'place', params: { ...render.value, step, name } })
}

async function kept(name: string): Promise<void> {
  try {
    await refresh()
  } catch (reason) {
    refusal.value = (reason as Error).message
    return
  }
  choose(name, 'outline')
}

/* The flag changed on a card: the picker reads the list again, and what the screen holds of
   the tattoo is read again when it is next chosen. */
async function flagged(): Promise<void> {
  placing.forget()
  try {
    await refresh()
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
}

function uploadInstead(cut: string): void {
  void router.push({ ...picking.value, query: { instead: cut } })
}

function forwardTo(step: Step): void {
  void router.push(at(step))
}

/* A step that needs a tattoo with none named goes back to the picker. */
watch(
  () => [props.step, props.name],
  () => {
    if (props.step !== 'tattoo' && !props.name) void router.replace(picking.value)
  },
  { immediate: true },
)

/* The tattoo a step names is read once, and again for the outline the step before it saved. */
watch(
  () => [props.step, props.name] as const,
  ([now, name], before) => {
    if (name === undefined || now === 'tattoo') return
    void placing.load(name)
    if (before?.[0] === 'outline' && now !== 'outline') void placing.reload()
  },
  { immediate: true },
)

/* The earliest stage short of its floor: the review goes there until the pairs stand. */
const short = computed(() =>
  placing.mode.value && list.value
    ? shortStep(
        placing.mode.value,
        { first: complete(placing.first.value).length, second: complete(placing.second.value).length },
        list.value.limits,
      )
    : null,
)

/* The mode is read data, so the route cannot know a step it skips: once the tattoo is read,
   the route is replaced by the step its mode takes in place. */
watch(
  () => [placing.mode.value, props.step, short.value] as const,
  ([mode, step, earliest]) => {
    if (mode === null || !props.name) return
    const taken = skipped(mode, step, earliest)
    if (taken !== step) void router.replace(at(taken))
  },
  { immediate: true },
)

/* The stage the route is on, with the pairs it holds; the other steps pair no images. */
const stage = computed<Stage | null>(() => {
  const mode = placing.mode.value
  if (mode === null) return null
  if (props.step === 'photo') {
    return { mode, step: 'photo', pairs: placing.first.value, saved: placing.savedAt.value }
  }
  if (props.step === 'render') return { mode, step: 'render', pairs: placing.second.value, saved: null }
  return null
})

/* The Leave dialog: a navigation off a stage that holds a lone point waits for the answer.
   *Stay* cancels it; *Leave* drops the lone point and lets it go. */
const asking = ref<Ask | null>(null)
let decide: ((go: boolean) => void) | null = null

const leaving = (): Promise<boolean> => {
  const now = stage.value
  const ask = now ? asks(now) : null
  if (ask === null) return placing.settled().then(() => true)
  decide?.(false)
  asking.value = ask
  return new Promise((resolve) => {
    decide = resolve
  })
}

const answer = (go: boolean): void => {
  const now = stage.value
  if (go && now) (now.step === 'photo' ? placing.editFirst : placing.editSecond)(left(now.pairs))
  asking.value = null
  decide?.(go)
  decide = null
}

onBeforeRouteUpdate((to) =>
  to.params.step === props.step && to.params.name === props.name ? true : leaving(),
)
onBeforeRouteLeave(leaving)

/* The picker shows each tattoo's state as the stages left it. */
watch(
  () => props.step,
  (now) => {
    if (now === 'tattoo' && list.value) void refresh().catch(() => undefined)
  },
)

onMounted(async () => {
  try {
    const own = { ...render.value, version: versionOf(props.version) }
    const [shown, listed] = await Promise.all([renderDetail(own), tattoos(props.digest)])
    detail.value = shown
    list.value = listed
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
})

onUnmounted(() => void placing.settled())
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <RefusalPage v-else-if="placing.refusal.value" :refusal="placing.refusal.value" />
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
        <template v-if="steps">
          <RouterLink
            v-for="one in steps"
            :key="one.step"
            class="place__step"
            :class="{ 'place__step--on': step === one.step }"
            :to="one.step === 'tattoo' ? picking : at(one.step)"
          >
            {{ circled(one.number) }} {{ one.label }}
          </RouterLink>
        </template>
        <template v-else>
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
        </template>
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
      @flagged="flagged"
    />
    <OutlineStep
      v-else-if="step === 'outline' && name"
      :key="name"
      :place="place"
      :name="name"
      :limits="list.limits"
      :mode="placing.mode.value"
      @instead="uploadInstead"
      @forward="forwardTo"
    />
    <StagePhoto
      v-else-if="step === 'photo' && name && placing.tattoo.value"
      :key="`photo-${name}`"
      :place="place"
      :version="version"
      :seed="seed"
      :limits="list.limits"
      @forward="forwardTo('render')"
    />
    <StageRender
      v-else-if="step === 'render' && name && placing.tattoo.value"
      :key="`render-${name}`"
      :place="place"
      :version="version"
      :seed="seed"
      :limits="list.limits"
      @forward="forwardTo('review')"
    />
    <ReviewBake
      v-else-if="step === 'review' && name && placing.tattoo.value"
      :key="`review-${name}`"
      :place="place"
      :version="version"
      :seed="seed"
      :limits="list.limits"
      @back="forwardTo"
    />
    <LeaveDialog v-if="asking" :ask="asking" @stay="answer(false)" @leave="answer(true)" />
  </section>
</template>
