<script setup lang="ts">
import { computed } from 'vue'
import { type Pairs, type Side, selected } from '../pairs'
import type { Answer } from '../preview'
import type { Point } from '../types'
import { toScreen } from '../zoom'
import ImagePanel, { type Press } from './ImagePanel.vue'

/* One image of a pair editor: the image with its points numbered over it, the selected pair
   and the lone point marked, and, on the target, the preview multiplied over the image at
   the operator's opacity with a way to hide it. A panel that waits for its match takes
   the accent edge. `offset` is where the shown pixels start in the points' own pixels, for a
   crop of the tattoo. It declares no command. */
const props = defineProps<{
  src: string
  alt: string
  width: number
  height: number
  side: Side
  pairs: Pairs
  /* The selection radius in screen pixels. */
  radius: number
  waiting: boolean
  offset?: Point
  /* On the target only: the preview, its opacity and whether it is hidden or dimmed. */
  target?: boolean
  preview?: Answer | null
  opacity?: number
  hidden?: boolean
  dimmed?: boolean
}>()

const emit = defineEmits<{
  place: [press: Press]
  drag: [index: number, at: Point, fresh: boolean]
  'update:opacity': [value: number]
  'update:hidden': [value: boolean]
}>()

const origin = computed<Point>(() => props.offset ?? [0, 0])
const shift = (at: Point): Point => [at[0] + origin.value[0], at[1] + origin.value[1]]

const grab = (at: Point, scale: number) =>
  selected(props.pairs, props.side, shift(at), scale, props.radius)

const marks = computed(() =>
  props.pairs.slots.flatMap((slot, index) => {
    const point = slot[props.side]
    if (!point) return []
    const alone = (slot.a === null) !== (slot.b === null)
    return [{ index, point, alone, on: index === props.pairs.selected }]
  }),
)

const at = (view: Parameters<typeof toScreen>[0], point: Point): Point =>
  toScreen(view, [point[0] - origin.value[0], point[1] - origin.value[1]])

function setOpacity(event: Event): void {
  emit('update:opacity', Number((event.target as HTMLInputElement).value))
}
</script>

<template>
  <div class="pair" :class="{ 'pair--waiting': waiting }" :data-side="side">
    <ImagePanel
      :src="src"
      :alt="alt"
      :width="width"
      :height="height"
      :grab="grab"
      @click="emit('place', { ...$event, at: shift($event.at) })"
      @drag="(index, point, fresh) => emit('drag', index, shift(point), fresh)"
    >
      <template #default="{ view }">
        <image
          v-if="target && preview && !hidden"
          class="pair__preview"
          :href="preview.url"
          :x="at(view, [preview.box.x, preview.box.y])[0]"
          :y="at(view, [preview.box.x, preview.box.y])[1]"
          :width="preview.box.width * view.scale"
          :height="preview.box.height * view.scale"
          :opacity="opacity ?? 1"
          preserveAspectRatio="none"
        />
        <g v-for="mark in marks" :key="mark.index">
          <circle
            class="pair__point"
            :class="{ 'pair__point--on': mark.on, 'pair__point--lone': mark.alone }"
            :cx="at(view, mark.point)[0]"
            :cy="at(view, mark.point)[1]"
            :r="mark.on ? 7 : 5"
          />
          <text
            class="pair__tag mono"
            :x="at(view, mark.point)[0] + 9"
            :y="at(view, mark.point)[1] - 9"
          >
            {{ mark.index + 1 }}
          </text>
        </g>
      </template>
    </ImagePanel>
    <div v-if="target" class="pair__bar">
      <label class="pair__opacity mono">
        opacity
        <input
          type="range"
          min="0.1"
          max="1"
          step="0.05"
          aria-label="Preview opacity"
          :value="opacity ?? 1"
          @input="setOpacity"
        />
      </label>
      <button class="btn btn-secondary" type="button" @click="emit('update:hidden', !hidden)">
        {{ hidden ? 'Show the preview' : 'Hide the preview' }}
      </button>
      <span v-if="dimmed" class="pair__note mono">asking…</span>
    </div>
  </div>
</template>
