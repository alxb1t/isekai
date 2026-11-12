<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { type Gesture, cursorOf, gestureOf } from '../press'
import type { Point } from '../types'
import { SCALE_FLOOR, type View, actual, fitted, panned, toImage, zoomedAt } from '../zoom'

/* One image in a viewport: the wheel zooms at the pointer, *Fit* and *1:1* set the view,
   and the zoom shows as a percentage. The geometry is `zoom.ts`; this draws it. A press
   is one gesture, read by `gestureOf`: with Shift it places, and a press that moves
   past the slop is dropped; with Shift up on what `grab` names it drags that, and
   elsewhere it pans. A press that stays within the slop is a click. The cursor follows
   Shift and the pan. The overlay slot is drawn in viewport pixels with the view. */
export interface Press {
  /* The image point under the pointer, the zoom it was pressed at, and Shift held at the press. */
  at: Point
  scale: number
  shift: boolean
}

const props = defineProps<{
  src: string
  alt: string
  width: number
  height: number
  /* The index of what lies under an image point at a zoom, or null; asked with Shift up. */
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
  gesture: Gesture
  grabbed: number | null
  shift: boolean
  moved: boolean
  fresh: boolean
}

let held: Held | null = null

/* Shift as the cursor knows it, and whether a pan or a move is under way. */
const shifting = ref(false)
const active = ref(false)
const cursor = computed(() => cursorOf(shifting.value, active.value))

function down(event: PointerEvent): void {
  if (event.button !== 0) return
  shifting.value = event.shiftKey
  const at = local(event)
  const grabbed = event.shiftKey ? null : (props.grab?.(toImage(view.value, at), view.value.scale) ?? null)
  const gesture = gestureOf(event.shiftKey, grabbed)
  held = { start: at, last: at, gesture, grabbed, shift: event.shiftKey, moved: false, fresh: true }
  frame.value?.setPointerCapture(event.pointerId)
}

function move(event: PointerEvent): void {
  shifting.value = event.shiftKey
  if (!held) return
  const at = local(event)
  if (!held.moved && Math.hypot(at[0] - held.start[0], at[1] - held.start[1]) <= SLOP) return
  held.moved = true
  if (held.gesture === 'move' && held.grabbed !== null) {
    active.value = true
    emit('drag', held.grabbed, toImage(view.value, at), held.fresh)
    held.fresh = false
  } else if (held.gesture === 'pan') {
    active.value = true
    view.value = panned(view.value, at[0] - held.last[0], at[1] - held.last[1], image.value, room.value)
    fitting.value = false
  }
  held.last = at
}

function up(event: PointerEvent): void {
  const was = held
  held = null
  active.value = false
  if (was && !was.moved) emit('click', { ...pressed(event), shift: was.shift })
}

function cancel(): void {
  held = null
  active.value = false
}

function shiftKey(event: KeyboardEvent): void {
  if (event.key === 'Shift') shifting.value = event.type === 'keydown'
}

function blur(): void {
  shifting.value = false
}

let watching: ResizeObserver | null = null

onMounted(() => {
  measure()
  if (frame.value) {
    watching = new ResizeObserver(measure)
    watching.observe(frame.value)
  }
  window.addEventListener('keydown', shiftKey)
  window.addEventListener('keyup', shiftKey)
  window.addEventListener('blur', blur)
})

onUnmounted(() => {
  watching?.disconnect()
  window.removeEventListener('keydown', shiftKey)
  window.removeEventListener('keyup', shiftKey)
  window.removeEventListener('blur', blur)
})

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
      :class="`panel__viewport--${cursor}`"
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
