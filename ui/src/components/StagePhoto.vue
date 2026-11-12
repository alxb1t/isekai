<script setup lang="ts">
import { computed, inject, ref, watch } from 'vue'
import { type Place, designAt, photoUrl } from '../api'
import { PLACING } from '../composables/usePlacing'
import { useNatural } from '../composables/useNatural'
import { usePreview } from '../composables/usePreview'
import { useKeys } from '../composables/useKeys'
import { placeCommands } from '../placeKeys'
import { type Pairs, clicked, cleared, complete, deleted, forward, lone, moved, redone, touched, undone } from '../pairs'
import { opacityOf } from '../preview'
import { circled, stepsOf } from '../stages'
import type { Point, TattooLimits } from '../types'
import PairList from './PairList.vue'
import PairPanel from './PairPanel.vue'
import type { Press } from './ImagePanel.vue'

/* The placement screen's stage 1: the tattoo's image beside the photograph, a point on one
   and its match on the other. The pairs are saved as they change, the warp is previewed over
   the photograph, and the stage goes forward with its floor of pairs and no lone point. */
const props = defineProps<{
  place: Place
  version: string
  seed: string
  limits: TattooLimits
}>()
const emit = defineEmits<{ forward: [] }>()

const placing = inject(PLACING)
if (!placing) throw new Error('the placement screen provides what its stages hold')

const tattoo = computed(() => placing.tattoo.value)
const pairs = computed(() => placing.first.value)
const photo = useNatural(() => photoUrl(props.place))
const waiting = computed(() => lone(pairs.value)?.waiting ?? null)
const wait = computed(() => forward(pairs.value, props.limits.floor_stage1))
const next = computed(() => {
  const step = stepsOf('two-stage').find((one) => one.step === 'render')
  return step ? `${circled(step.number)} ${step.label}` : ''
})

const opacity = ref(1)
const hidden = ref(false)
const preview = usePreview({
  ask: () => ({
    target: 'photo',
    place: props.place,
    version: props.version,
    seed: props.seed,
    edit: null,
    pairs: complete(pairs.value),
    limb: null,
    exclusions: [],
  }),
  count: () => complete(pairs.value).length,
  floor: props.limits.preview_floor,
  wait: props.limits.preview_wait_ms,
  collection: props.place.collection,
  name: () => tattoo.value?.name ?? '',
})

watch(
  () => JSON.stringify(complete(pairs.value)),
  () => preview.changed(),
  { immediate: true },
)

const edit = (next: Pairs): void => placing.editFirst(next)

useKeys('screen', placeCommands({
  undo: () => edit(undone(pairs.value)),
  redo: () => edit(redone(pairs.value)),
}))

function placed(side: 'a' | 'b', press: Press): void {
  const radius = props.limits.pair_radius
  edit(
    press.shift
      ? clicked(pairs.value, side, press.at, press.scale, radius)
      : touched(pairs.value, side, press.at, press.scale, radius),
  )
}

function dragged(side: 'a' | 'b', index: number, at: Point, fresh: boolean): void {
  edit(moved(pairs.value, index, side, at, fresh))
}
</script>

<template>
  <section v-if="tattoo" class="stage" data-stage="photo">
    <div class="stage__panels">
      <PairPanel
        :src="designAt(tattoo.name)"
        :alt="tattoo.name"
        :width="tattoo.size[0]"
        :height="tattoo.size[1]"
        side="a"
        :pairs="pairs"
        :radius="limits.pair_radius"
        :waiting="waiting === 'a'"
        @place="placed('a', $event)"
        @drag="(index, at, fresh) => dragged('a', index, at, fresh)"
      />
      <PairPanel
        v-if="photo"
        :src="photoUrl(place)"
        alt="the photograph"
        :width="photo.width"
        :height="photo.height"
        side="b"
        :pairs="pairs"
        :radius="limits.pair_radius"
        :waiting="waiting === 'b'"
        target
        :preview="preview.state.value.shown"
        :opacity="opacityOf(preview.state.value, opacity)"
        :hidden="hidden"
        :dimmed="preview.state.value.asking && preview.state.value.shown !== null"
        @place="placed('b', $event)"
        @drag="(index, at, fresh) => dragged('b', index, at, fresh)"
        @update:opacity="opacity = $event"
        @update:hidden="hidden = $event"
      />
    </div>
    <aside class="stage__side">
      <span class="section-label">{{ tattoo.name }} · tattoo ↔ photograph</span>
      <PairList
        :pairs="pairs"
        :names="['tattoo', 'photograph']"
        @change="edit"
        @undo="edit(undone(pairs))"
        @remove="edit(deleted(pairs))"
        @clear="edit(cleared(pairs))"
      />
      <p class="stage__status mono" data-save>{{ placing.status.value }}</p>
      <p v-if="preview.state.value.refusal" class="picker__refusal" data-preview-refusal>
        <span class="refusal__mark" />{{ preview.state.value.refusal }}
      </p>
      <div class="stage__forward">
        <span v-if="wait" class="stage__note mono">{{ wait }}</span>
        <button class="btn btn-primary" type="button" :disabled="wait !== null" @click="emit('forward')">
          Next: {{ next }}
        </button>
      </div>
    </aside>
  </section>
</template>
