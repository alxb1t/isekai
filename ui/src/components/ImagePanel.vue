<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import type { Point } from '../types'
import { SCALE_FLOOR, type View, actual, fitted, panned, toImage, zoomedAt } from '../zoom'

/* One image in a viewport: the wheel zooms at the pointer, a drag pans, *Fit* and *1:1*
   set the view, and the zoom shows as a percentage. The geometry is `zoom.ts`; this
   draws it. A press that moves a few pixels is a click, one that moves more a pan,
   and a press on what `grab` names is a drag of it. The overlay slot is drawn in
   viewport pixels with the view. */
export interface Press {
  /* The image point under the pointer, and the zoom it was pressed at. */
  at: Point
  scale: number
  shift: boolean
}

const props = defineProps<{
  src: string
  alt: string
  width: number
  height: number
  /* The index of what lies under an image point at a zoom, or null. */
  grab?: (at: Point, scale: number) => number | null
}>()

const emit = defineEmits<{
  click: [press: Press]
  dblclick: [press: Press]
  drag: [index: number, at: Point, fresh: boolean]
}>()

const SLOP = 4
const WHEEL_RATE = 0.0015

const frame = ref<HTMLElement | null>(null)
const room = ref({ width: 0, height: 0 })
const view = ref<View>({ scale: 1, x: 0, y: 0 })
const fitting = ref(true)
const image = computed(() => ({ width: props.width, height: props.height }))
const percent = computed(() => Math.round(view.value.scale * 100))
/* The floor is lower for an image whose fit is smaller than it. */
const floor = computed(() => (room.value.width > 0 ? Math.min(SCALE_FLOOR, fitted(image.value, room.value).scale) : SCALE_FLOOR))

function measure(): void {
  const held = frame.value
  if (!held || held.clientWidth === 0 || held.clientHeight === 0) return
  room.value = { width: held.clientWidth, height: held.clientHeight }
  if (fitting.value) view.value = fitted(image.value, room.value)
}

function fit(): void {
  fitting.value = true
  measure()
}

function oneToOne(): void {
  if (room.value.width === 0) return
  view.value = actual(view.value, room.value)
  fitting.value = false
}

function local(event: MouseEvent): Point {
  const box = frame.value?.getBoundingClientRect()
  return [event.clientX - (box?.left ?? 0), event.clientY - (box?.top ?? 0)]
}

function pressed(event: MouseEvent): Press {
  return { at: toImage(view.value, local(event)), scale: view.value.scale, shift: event.shiftKey }
}

function wheel(event: WheelEvent): void {
  if (room.value.width === 0) return
  view.value = zoomedAt(view.value, Math.exp(-event.deltaY * WHEEL_RATE), local(event), floor.value)
  fitting.value = false
}

interface Held {
  start: Point
  last: Point
  grabbed: number | null
  moved: boolean
  fresh: boolean
}

let held: Held | null = null

function down(event: PointerEvent): void {
  if (event.button !== 0) return
  const at = local(event)
  const grabbed = props.grab?.(toImage(view.value, at), view.value.scale) ?? null
  held = { start: at, last: at, grabbed, moved: false, fresh: true }
  frame.value?.setPointerCapture(event.pointerId)
}

function move(event: PointerEvent): void {
  if (!held) return
  const at = local(event)
  if (!held.moved && Math.hypot(at[0] - held.start[0], at[1] - held.start[1]) <= SLOP) return
  held.moved = true
  if (held.grabbed !== null) {
    emit('drag', held.grabbed, toImage(view.value, at), held.fresh)
    held.fresh = false
  } else {
    view.value = panned(view.value, at[0] - held.last[0], at[1] - held.last[1], image.value, room.value)
    fitting.value = false
  }
  held.last = at
}

function up(event: PointerEvent): void {
  const was = held
  held = null
  if (was && !was.moved) emit('click', pressed(event))
}

function cancel(): void {
  held = null
}

let watching: ResizeObserver | null = null

onMounted(() => {
  measure()
  if (frame.value) {
    watching = new ResizeObserver(measure)
    watching.observe(frame.value)
  }
})

onUnmounted(() => watching?.disconnect())

watch(
  () => [props.src, props.width, props.height],
  () => fit(),
)
</script>

<template>
  <div class="panel" data-panel>
    <div
      ref="frame"
      class="panel__viewport"
      @wheel.prevent="wheel"
      @pointerdown="down"
      @pointermove="move"
      @pointerup="up"
      @pointercancel="cancel"
      @dblclick="emit('dblclick', pressed($event))"
    >
      <img
        class="panel__image"
        :src="src"
        :alt="alt"
        :width="width"
        :height="height"
        draggable="false"
        :style="{ transform: `translate(${view.x}px, ${view.y}px) scale(${view.scale})` }"
      />
      <svg class="panel__overlay" :viewBox="`0 0 ${room.width} ${room.height}`">
        <slot :view="view" />
      </svg>
    </div>
    <div class="panel__bar">
      <button class="btn btn-secondary" type="button" @click="fit">Fit</button>
      <button class="btn btn-secondary" type="button" @click="oneToOne">1:1</button>
      <span class="panel__zoom mono" data-zoom>{{ percent }}%</span>
    </div>
  </div>
</template>
