<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, shallowRef } from 'vue'
import { type Place, designAt, inkView, photoUrl, saveOutline, tattooNamed } from '../api'
import {
  type Draft,
  type Rules,
  blank,
  box,
  cleared,
  drafted,
  moved,
  placed,
  ready,
  removed,
  undone,
  vertexAt,
} from '../polygon'
import {
  type Tone,
  card,
  controlsWait,
  defaultTone,
  differs,
  greyOf,
  inkSize,
  scaleOf,
  whiteState,
} from '../tattoos'
import { type Mode, type Step, circled, forwardOf, stepsOf } from '../stages'
import type { InkView, Outline, Point, Tattoo, TattooLimits } from '../types'
import { type View, toScreen } from '../zoom'
import ImagePanel, { type Press } from './ImagePanel.vue'
import RefusalPage from './RefusalPage.vue'

/* The placement screen's second step: the tattoo, or the photograph of a cut, in the
   panel with its outline drawn on it; the outline and its tone are saved as they
   change, and once it is closed the server's ink view is drawn beside it. The ink view
   is the judge: nothing here grades the cut. */
const props = defineProps<{
  place: Place
  name: string
  limits: TattooLimits
  /* How the tattoo is placed, once the screen has read it; the forward action follows it. */
  mode: Mode | null
}>()
const emit = defineEmits<{ instead: [cut: string]; forward: [step: Step] }>()

const SAVE_DELAY = 400
const INK_DELAY = 250

const tattoo = ref<Tattoo | null>(null)
const refusal = ref<string | null>(null)
const draft = ref<Draft>(blank)
const tone = ref<Tone>({ neutral: false, depth: 1 })
const scale = ref(1)
const status = ref('')

const isCut = computed(() => tattoo.value?.kind === 'cut')
const held = computed(() =>
  tattoo.value ? card(tattoo.value, props.place.digest, undefined, props.limits.floor_stage1) : null,
)
const rules = computed<Rules>(() => ({
  min: props.limits.outline_min,
  max: props.limits.outline_max,
  width: tattoo.value?.size[0] ?? 0,
  height: tattoo.value?.size[1] ?? 0,
}))
const src = computed(() => (isCut.value ? photoUrl(props.place) : designAt(props.name)))
const wait = computed(() => controlsWait(draft.value))
const complete = computed(() => ready(draft.value, rules.value))
const standard = computed(() =>
  tattoo.value ? defaultTone(tattoo.value.kind, props.limits) : null,
)
const resettable = computed(() => standard.value !== null && differs(tone.value, standard.value))
const onward = computed(() => {
  if (props.mode === null) return null
  const to = forwardOf(props.mode, { closed: draft.value.closed, points: draft.value.points.length })
  const held = stepsOf(props.mode).find((one) => one.step === to.step)
  return { ...to, label: held ? `${circled(held.number)} ${held.label}` : '' }
})

function current(): Outline {
  const { points, closed } = draft.value
  return {
    points: points.map(([x, y]): Point => [x, y]),
    closed,
    white: scale.value,
    neutral: tone.value.neutral,
    depth: tone.value.depth,
  }
}

let saveTimer: ReturnType<typeof setTimeout> | undefined
let saving: Promise<void> = Promise.resolve()

/* Send the outline as it stands, after the saves already on their way. */
function flush(): void {
  clearTimeout(saveTimer)
  saveTimer = undefined
  const outline = current()
  saving = saving.then(async () => {
    try {
      await saveOutline(props.name, outline)
      if (saveTimer === undefined) status.value = 'saved'
    } catch (reason) {
      status.value = (reason as Error).message
    }
  })
}

/* Go forward once the outline as it stands is saved: the next stage reads it from the server. */
async function goForward(step: Step): Promise<void> {
  if (saveTimer !== undefined) flush()
  await saving
  emit('forward', step)
}

const ink = shallowRef<{ url: string; box: InkView['box']; white: number } | null>(null)
const inkRefusal = ref<string | null>(null)
const drawing = ref(false)
let inkTimer: ReturnType<typeof setTimeout> | undefined
let asking: AbortController | null = null

function release(): void {
  if (ink.value) URL.revokeObjectURL(ink.value.url)
  ink.value = null
}

/* Ask for the ink once the outline is closed, after its save: the server reads the saved outline. */
function askInk(): void {
  clearTimeout(inkTimer)
  asking?.abort()
  asking = null
  drawing.value = false
  if (!complete.value) {
    release()
    inkRefusal.value = null
    return
  }
  drawing.value = true
  inkTimer = setTimeout(async () => {
    const mine = new AbortController()
    asking = mine
    if (saveTimer !== undefined) flush()
    await saving
    if (mine.signal.aborted) return
    try {
      const made = await inkView(
        props.place.collection,
        props.name,
        current(),
        isCut.value ? props.place : null,
        mine.signal,
      )
      if (mine.signal.aborted) return
      release()
      ink.value = { url: URL.createObjectURL(made.image), box: made.box, white: made.white }
      inkRefusal.value = null
    } catch (reason) {
      if (!mine.signal.aborted) inkRefusal.value = (reason as Error).message
    } finally {
      if (!mine.signal.aborted) drawing.value = false
    }
  }, INK_DELAY)
}

/* Every change goes here: it is saved soon, and the ink is asked for again. */
function changed(): void {
  clearTimeout(saveTimer)
  status.value = 'saving…'
  saveTimer = setTimeout(flush, SAVE_DELAY)
  askInk()
}

function edit(next: Draft): void {
  if (next === draft.value) return
  draft.value = next
  changed()
}

function setTone(next: Tone): void {
  tone.value = next
  changed()
}

const grab = (at: Point, zoom: number) => vertexAt(draft.value, at, zoom)

function clicked(press: Press): void {
  if (!press.shift) return
  edit(placed(draft.value, press.at, press.scale, rules.value))
}

function doubled(press: Press): void {
  if (press.shift) return
  const index = vertexAt(draft.value, press.at, press.scale)
  if (index !== null) edit(removed(draft.value, index, rules.value))
}

function dragged(index: number, at: Point, fresh: boolean): void {
  edit(moved(draft.value, index, at, rules.value, fresh))
}

/* The automatic white point's grey, once the ink view has read it, and the grey shown. */
const automatic = computed(() => ink.value?.white ?? null)
const grey = computed(() =>
  automatic.value === null ? null : greyOf(automatic.value, scale.value),
)
const whiteWait = computed(() => wait.value ?? (automatic.value === null ? 'reading the ink' : null))

function setGrey(event: Event): void {
  const value = Number((event.target as HTMLInputElement).value)
  if (automatic.value === null || !Number.isFinite(value)) return
  scale.value = scaleOf(value, automatic.value)
  changed()
}

function setAuto(): void {
  scale.value = 1
  changed()
}

function setNeutral(event: Event): void {
  setTone({ ...tone.value, neutral: (event.target as HTMLInputElement).checked })
}

function setDepth(event: Event): void {
  const value = Number((event.target as HTMLInputElement).value)
  if (!Number.isFinite(value)) return
  const { depth_min: low, depth_max: high } = props.limits
  setTone({ ...tone.value, depth: Math.min(high, Math.max(low, value)) })
}

function reset(): void {
  if (standard.value) setTone({ ...standard.value })
}

/* The outline's line and fill, and the dimming around a cut's ink, in viewport pixels. */
const trace = (view: View, points: readonly Point[]) =>
  points.map((point) => toScreen(view, point).join(',')).join(' ')
const dimmed = (view: View, points: readonly Point[]) =>
  `M-100000,-100000H100000V100000H-100000ZM${points
    .map((point) => toScreen(view, point).join(','))
    .join('L')}Z`
const waiting = (view: View, points: readonly Point[]) => {
  const [x1, y1] = toScreen(view, points[points.length - 1])
  const [x2, y2] = toScreen(view, points[0])
  return { x1, y1, x2, y2 }
}

onMounted(async () => {
  try {
    const { outline, ...record } = await tattooNamed(props.name)
    tattoo.value = record
    draft.value = drafted(outline.points, outline.closed)
    tone.value = { neutral: outline.neutral, depth: outline.depth }
    scale.value = outline.white
    if (outline.closed) askInk()
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
})

onUnmounted(() => {
  clearTimeout(inkTimer)
  asking?.abort()
  release()
  if (saveTimer !== undefined) flush()
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <RefusalPage v-else-if="held && !held.choosable" :refusal="held.reason ?? ''" />
  <section v-else-if="tattoo" class="outline">
    <ImagePanel
      :src="src"
      :alt="name"
      :width="tattoo.size[0]"
      :height="tattoo.size[1]"
      :grab="grab"
      @click="clicked"
      @dblclick="doubled"
      @drag="dragged"
    >
      <template #default="{ view }">
        <path
          v-if="isCut && draft.closed"
          class="outline__dim"
          fill-rule="evenodd"
          :d="dimmed(view, draft.points)"
        />
        <polygon
          v-if="draft.closed"
          class="outline__shape"
          :points="trace(view, draft.points)"
        />
        <template v-else-if="draft.points.length > 0">
          <polyline class="outline__line" :points="trace(view, draft.points)" />
          <line
            v-if="draft.points.length > 1"
            class="outline__waiting"
            v-bind="waiting(view, draft.points)"
          />
        </template>
        <g v-for="(point, index) in draft.points" :key="index">
          <circle
            class="outline__vertex"
            :class="{ 'outline__vertex--first': index === 0 }"
            :cx="toScreen(view, point)[0]"
            :cy="toScreen(view, point)[1]"
            r="5"
          />
          <text
            class="outline__tag mono"
            :x="toScreen(view, point)[0] + 8"
            :y="toScreen(view, point)[1] - 8"
          >
            {{ index + 1 }}
          </text>
        </g>
      </template>
    </ImagePanel>
    <aside class="outline__side">
      <span class="section-label">{{ name }} · {{ held?.state }}</span>
      <p class="outline__source mono" data-source>
        {{ held?.source }}<template v-if="isCut && draft.closed">
          · ink {{ inkSize(box(draft)) }} on the photograph</template
        >
      </p>
      <p class="outline__hint mono">
        click adds · the first point closes · drag moves · ⇧-click inserts · double click removes
      </p>
      <div class="outline__row">
        <button class="btn btn-secondary" type="button" :disabled="draft.past.length === 0" @click="edit(undone(draft))">
          Undo
        </button>
        <button class="btn btn-secondary" type="button" :disabled="draft.points.length === 0" @click="edit(cleared(draft))">
          Clear
        </button>
        <span class="outline__status mono" data-save>{{ status }}</span>
      </div>
      <p class="section-label">ink view</p>
      <div class="outline__ink" data-ink>
        <img v-if="ink" class="outline__ink-image" :src="ink.url" :alt="`the ink of ${name}`" />
        <span v-else-if="wait" class="outline__wait mono">{{ wait }}</span>
        <span v-else-if="drawing" class="outline__wait mono">drawing the ink…</span>
      </div>
      <p v-if="ink" class="outline__hint mono">
        crop at {{ Math.round(ink.box.x) }},{{ Math.round(ink.box.y) }} ·
        {{ Math.round(ink.box.width) }}×{{ Math.round(ink.box.height) }}
      </p>
      <p v-if="inkRefusal" class="picker__refusal" data-ink-refusal>
        <span class="refusal__mark" />{{ inkRefusal }}
      </p>
      <p class="section-label">white point · {{ whiteState(scale) }}</p>
      <div class="outline__row">
        <input
          class="input mono outline__number"
          type="number"
          min="1"
          max="255"
          step="1"
          aria-label="White point"
          :value="grey ?? ''"
          :disabled="whiteWait !== null"
          @change="setGrey"
        />
        <button class="btn btn-secondary" type="button" :disabled="whiteWait !== null || scale === 1" @click="setAuto">
          Auto
        </button>
        <span v-if="whiteWait" class="outline__wait mono">{{ whiteWait }}</span>
      </div>
      <p class="section-label">tone</p>
      <div class="outline__row">
        <label class="outline__check mono">
          <input type="checkbox" :checked="tone.neutral" :disabled="wait !== null" @change="setNeutral" />neutral
        </label>
        <label class="outline__check mono">
          depth
          <input
            class="input mono outline__number"
            type="number"
            :min="limits.depth_min"
            :max="limits.depth_max"
            step="0.1"
            aria-label="Depth"
            :value="tone.depth"
            :disabled="wait !== null"
            @change="setDepth"
          />
        </label>
        <button v-if="resettable" class="btn btn-secondary" type="button" @click="reset">Reset</button>
        <span v-if="wait" class="outline__wait mono">{{ wait }}</span>
      </div>
      <button v-if="isCut" class="btn btn-secondary" type="button" @click="emit('instead', name)">
        Upload a tattoo instead
      </button>
      <div v-if="onward" class="stage__forward">
        <span v-if="onward.wait" class="stage__note mono" data-forward-wait>{{ onward.wait }}</span>
        <button
          class="btn btn-primary"
          type="button"
          :disabled="onward.step === null"
          @click="onward.step && goForward(onward.step)"
        >
          Next: {{ onward.label || 'the stage' }}
        </button>
      </div>
    </aside>
  </section>
</template>
