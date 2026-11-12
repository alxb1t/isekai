<script setup lang="ts">
import { computed, inject, onUnmounted, ref, shallowRef, watch } from 'vue'
import { type Place, imageAt, inkView, photoUrl, versionOf } from '../api'
import { PLACING } from '../composables/usePlacing'
import { useNatural } from '../composables/useNatural'
import { usePreview } from '../composables/usePreview'
import { type Pairs, clicked, cleared, complete, deleted, forward, lone, moved, undone } from '../pairs'
import { opacityOf } from '../preview'
import { floorOf } from '../stages'
import type { InkView, Point, TattooLimits } from '../types'
import PairList from './PairList.vue'
import PairPanel from './PairPanel.vue'
import type { Press } from './ImagePanel.vue'

/* The placement screen's render stage: the pairs between what the tattoo is on and the
   render. For a two-stage tattoo or a cut the left image is the photograph; for a tattoo
   that is not on this photo it is the tattoo's ink view. The warp is previewed over the
   render, and the stage goes forward with its floor of pairs and no lone point. */
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
const mode = computed(() => placing.mode.value)
const direct = computed(() => mode.value === 'direct')
const pairs = computed(() => placing.second.value)

const renderUrl = computed(() => imageAt({ ...props.place, version: versionOf(props.version), seed: props.seed }))
const render = useNatural(renderUrl)
const photo = useNatural(() => (direct.value ? null : photoUrl(props.place)))

/* A direct tattoo's left image: its ink view, a crop at `box` of the tattoo's pixels. */
const ink = shallowRef<{ url: string; box: InkView['box'] } | null>(null)
const inkRefusal = ref<string | null>(null)

function releaseInk(): void {
  if (ink.value) URL.revokeObjectURL(ink.value.url)
  ink.value = null
}

watch(
  () => [direct.value, tattoo.value?.name],
  async () => {
    releaseInk()
    inkRefusal.value = null
    const held = tattoo.value
    if (!direct.value || !held) return
    try {
      const made = await inkView(props.place.collection, held.name, held.outline, null)
      ink.value = { url: URL.createObjectURL(made.image), box: made.box }
    } catch (reason) {
      inkRefusal.value = (reason as Error).message
    }
  },
  { immediate: true },
)

onUnmounted(releaseInk)

const left = computed(() => {
  if (direct.value) {
    const held = ink.value
    return held
      ? {
          src: held.url,
          alt: 'the ink of the tattoo',
          width: held.box.width,
          height: held.box.height,
          offset: [held.box.x, held.box.y] as Point,
        }
      : null
  }
  const size = photo.value
  return size ? { src: photoUrl(props.place), alt: 'the photograph', ...size, offset: undefined } : null
})

const waiting = computed(() => lone(pairs.value)?.waiting ?? null)
const floor = computed(() => (mode.value ? floorOf(mode.value, 'render', props.limits) : 0))
const wait = computed(() => forward(pairs.value, floor.value))
const names = computed<[string, string]>(() => [direct.value ? 'tattoo' : 'photograph', 'render'])

const opacity = ref(1)
const hidden = ref(false)
const preview = usePreview({
  ask: () => ({
    target: 'render',
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

const edit = (next: Pairs): void => placing.editSecond(next)

function placed(side: 'a' | 'b', press: Press): void {
  edit(clicked(pairs.value, side, press.at, press.scale, props.limits.pair_radius))
}

function dragged(side: 'a' | 'b', index: number, at: Point, fresh: boolean): void {
  edit(moved(pairs.value, index, side, at, fresh))
}
</script>

<template>
  <section v-if="tattoo" class="stage" data-stage="render">
    <div class="stage__panels">
      <PairPanel
        v-if="left"
        :src="left.src"
        :alt="left.alt"
        :width="left.width"
        :height="left.height"
        :offset="left.offset"
        side="a"
        :pairs="pairs"
        :radius="limits.pair_radius"
        :waiting="waiting === 'a'"
        @place="placed('a', $event)"
        @drag="(index, at, fresh) => dragged('a', index, at, fresh)"
      />
      <p v-else-if="inkRefusal" class="picker__refusal" data-ink-refusal>
        <span class="refusal__mark" />{{ inkRefusal }}
      </p>
      <PairPanel
        v-if="render"
        :src="renderUrl"
        :alt="`seed ${seed}`"
        :width="render.width"
        :height="render.height"
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
      <span class="section-label">{{ tattoo.name }} · {{ names[0] }} ↔ render</span>
      <PairList
        :pairs="pairs"
        :names="names"
        @change="edit"
        @undo="edit(undone(pairs))"
        @remove="edit(deleted(pairs))"
        @clear="edit(cleared(pairs))"
      />
      <p v-if="preview.state.value.refusal" class="picker__refusal" data-preview-refusal>
        <span class="refusal__mark" />{{ preview.state.value.refusal }}
      </p>
      <div class="stage__forward">
        <span v-if="wait" class="stage__note mono">{{ wait }}</span>
        <button class="btn btn-primary" type="button" :disabled="wait !== null" @click="emit('forward')">
          Next: review
        </button>
      </div>
    </aside>
  </section>
</template>
