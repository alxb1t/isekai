<script setup lang="ts">
import { computed, inject, onMounted, onUnmounted, ref, shallowRef } from 'vue'
import { type Place, bakeTattoo, imageAt, placementPreview, versionOf } from '../api'
import { PLACING } from '../composables/usePlacing'
import { useNatural } from '../composables/useNatural'
import { regions } from '../outlines'
import { complete } from '../pairs'
import { bakeState, fitted, summary } from '../review'
import { type Step, circled, stepsOf } from '../stages'
import type { Preview, TattooLimits } from '../types'

/* The placement screen's review: the render's crop before and after, fitted to two columns, the
   summary of what was placed, a button back to each earlier stage and *Bake*. A bake only
   queues an edit request; the render session samples it. */
const props = defineProps<{
  place: Place
  version: string
  seed: string
  limits: TattooLimits
}>()
const emit = defineEmits<{ back: [step: Step] }>()

const placing = inject(PLACING)
if (!placing) throw new Error('the placement screen provides what its stages hold')

const tattoo = computed(() => placing.tattoo.value)
const mode = computed(() => placing.mode.value)
const renderUrl = computed(() => imageAt({ ...props.place, version: versionOf(props.version), seed: props.seed }))
const natural = useNatural(renderUrl)

const kept = computed(() => ({
  pairs: complete(placing.second.value),
  ...regions(placing.outlines.value),
}))
const ask = () => ({
  place: props.place,
  version: props.version,
  seed: props.seed,
  edit: null,
  ...kept.value,
})

const asking = ref(false)
const edit = ref<number | null>(null)
const refusal = ref<string | null>(null)
const state = computed(() =>
  mode.value
    ? bakeState({
        mode: mode.value,
        first: placing.first.value,
        second: placing.second.value,
        limits: props.limits,
        asking: asking.value,
        edit: edit.value,
        refusal: refusal.value,
      })
    : null,
)

/* The preview of the stage as it stands, asked once the pairs are enough. */
const shown = shallowRef<{ url: string; box: Preview['box']; white: number } | null>(null)
const previewRefusal = ref<string | null>(null)
const controller = new AbortController()

onMounted(async () => {
  const held = tattoo.value
  if (!held || state.value?.phase === 'waiting') return
  try {
    const got = await placementPreview(props.place.collection, held.name, { target: 'render', ...ask() }, controller.signal)
    shown.value = { url: URL.createObjectURL(got.image), box: got.box, white: got.white }
  } catch (reason) {
    if (!controller.signal.aborted) previewRefusal.value = (reason as Error).message
  }
})

onUnmounted(() => {
  controller.abort()
  if (shown.value) URL.revokeObjectURL(shown.value.url)
})

const summed = computed(() => {
  const held = tattoo.value
  if (!held || !mode.value) return null
  return summary({
    tattoo: held,
    mode: mode.value,
    photograph: props.place.digest,
    automatic: shown.value?.white ?? null,
    seed: props.seed,
    edit: null,
    first: complete(placing.first.value),
    second: kept.value.pairs,
    limb: kept.value.limb,
    exclusions: kept.value.exclusions,
    limits: props.limits,
  })
})

/* The crop of the render the preview covers, fitted to its column. */
const crop = computed(() => {
  const size = natural.value
  const own = shown.value
  if (!size || !own) return null
  return { ...fitted(own.box, size), backgroundImage: `url(${renderUrl.value})` }
})

const stages = computed(() =>
  mode.value ? stepsOf(mode.value).filter((one) => one.step === 'photo' || one.step === 'render') : [],
)

const bake = async (): Promise<void> => {
  const held = tattoo.value
  if (!held || asking.value) return
  asking.value = true
  refusal.value = null
  try {
    edit.value = (await bakeTattoo(props.place.collection, held.name, ask())).edit
  } catch (reason) {
    refusal.value = (reason as Error).message
  } finally {
    asking.value = false
  }
}
</script>

<template>
  <section v-if="tattoo && summed && state" class="stage" data-stage="review">
    <div class="review__main">
      <p v-if="previewRefusal" class="picker__refusal" data-preview-refusal>
        <span class="refusal__mark" />{{ previewRefusal }}
      </p>
      <div v-if="crop && shown" class="review__crops" data-review-crops>
        <figure class="review__crop">
          <div class="review__pixels" :style="crop" role="img" aria-label="before" />
          <figcaption class="mono">before</figcaption>
        </figure>
        <figure class="review__crop">
          <div class="review__pixels" :style="crop" role="img" aria-label="after">
            <img class="review__ink review__ink--crop" :src="shown.url" alt="" />
          </div>
          <figcaption class="mono">after</figcaption>
        </figure>
      </div>
    </div>
    <aside class="stage__side">
      <span class="section-label">review · {{ tattoo.name }}</span>
      <ul class="reviewlist mono" data-summary>
        <li>{{ summed.image }}</li>
        <li>{{ summed.tattoo }}</li>
        <li v-for="line in summed.stages" :key="line">{{ line }}</li>
        <li v-for="line in summed.outlines" :key="line">{{ line }}</li>
      </ul>
      <div class="review__actions">
        <span v-if="state.text" class="stage__note mono" data-bake-state>{{ state.text }}</span>
        <div class="outline__row">
          <button v-for="one in stages" :key="one.step" class="btn btn-secondary" type="button" @click="emit('back', one.step)">
            Back to {{ circled(one.number) }} {{ one.label }}
          </button>
          <button class="btn btn-primary" type="button" :disabled="!state.enabled" @click="bake">Bake</button>
        </div>
      </div>
    </aside>
  </section>
</template>
