<script setup lang="ts">
import { computed, inject, onUnmounted, ref, shallowRef, watch } from 'vue'
import { type Place, imageAt, inkView, photoUrl, proposePairs, versionOf } from '../api'
import { PLACING } from '../composables/usePlacing'
import { useNatural } from '../composables/useNatural'
import { usePreview } from '../composables/usePreview'
import {
  type Kind,
  begun,
  closed,
  drawing,
  drawn,
  held as drawingHeld,
  regions,
  rows as rowsOf,
  rulesOf,
  shapes as shapesOf,
  stopped,
} from '../outlines'
import {
  type Pairs,
  accepted,
  acceptedAll,
  arrived,
  clicked,
  cleared,
  complete,
  deleted,
  forward,
  lone,
  moved,
  proposals,
  sent,
  undone,
} from '../pairs'
import { added, closed as closedDraft, closes, undone as undoneDraft, vertexAt } from '../polygon'
import { opacityOf } from '../preview'
import { answered, asked, due, keyOf, pointsOf, refused, stands, view } from '../propose'
import { floorOf } from '../stages'
import type { InkView, Point, TattooLimits } from '../types'
import PairList from './PairList.vue'
import PairPanel from './PairPanel.vue'
import type { Press } from './ImagePanel.vue'

/* The placement screen's render stage: the pairs between what the tattoo is on and the
   render. For a two-stage tattoo or a cut the left image is the photograph; for a tattoo
   that is not on this photo it is the tattoo's ink view. The warp is previewed over the
   render with the limb and the exclusions drawn on it, which the pairs give way to while
   one is drawn, and the stage goes forward with its floor of pairs, no lone point and no
   proposed pair. A two-stage tattoo or a cut that opens here with no pair asks the server once
   for proposed pairs and holds them dashed until they are accepted. */
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

const outlines = computed(() => placing.outlines.value)
const locked = computed(() => drawingHeld(outlines.value))
const shapes = computed(() => shapesOf(outlines.value))
const outlineRows = computed(() => rowsOf(outlines.value))
const sketch = computed(() => drawing(outlines.value))
const rules = computed(() => (render.value ? rulesOf(props.limits, [render.value.width, render.value.height]) : null))

const opacity = ref(1)
const hidden = ref(false)
const preview = usePreview({
  ask: () => ({
    target: 'render',
    place: props.place,
    version: props.version,
    seed: props.seed,
    edit: null,
    pairs: sent(pairs.value),
    ...regions(outlines.value),
  }),
  count: () => sent(pairs.value).length,
  floor: props.limits.preview_floor,
  wait: props.limits.preview_wait_ms,
  collection: props.place.collection,
  name: () => tattoo.value?.name ?? '',
})

watch(
  () => JSON.stringify([sent(pairs.value), regions(outlines.value)]),
  () => preview.changed(),
  { immediate: true },
)

const key = computed(() => keyOf(tattoo.value?.name ?? '', props.version, props.seed))
const line = computed(() => view(placing.proposalAsked.value, key.value))
const waitingProposals = computed(() => proposals(pairs.value).length)

/* Ask once for the tattoo's proposed pairs on this render. The answer is kept whether or not
   this stage is still on screen, but only by the ask that made it: a later ask under the same
   key is another; a refusal is shown and the clicks still work. */
const propose = async (): Promise<void> => {
  const held = tattoo.value
  const at = key.value
  if (!held || !mode.value) return
  const points = pointsOf(mode.value, complete(placing.first.value), held.outline)
  placing.proposalAsked.value = asked(placing.proposalAsked.value, at)
  const mine = placing.proposalAsked.value[at]
  const stillAsking = (): boolean => stands(placing.proposalAsked.value, at, mine)
  try {
    const answer = await proposePairs(props.place, props.version, props.seed, points)
    if (!stillAsking()) return
    if (key.value === at) placing.editSecond(arrived(placing.second.value, answer.pairs))
    placing.proposalAsked.value = answered(placing.proposalAsked.value, at, answer.pairs.length)
  } catch (reason) {
    if (stillAsking()) placing.proposalAsked.value = refused(placing.proposalAsked.value, at, (reason as Error).message)
  }
}

watch(
  () => due(mode.value, pairs.value, placing.proposalAsked.value, key.value),
  (now) => {
    if (now) void propose()
  },
  { immediate: true },
)

const edit = (next: Pairs): void => placing.editSecond(next)

/* A click while an outline is drawn goes to the outline, on the render alone: it adds a
   point, or closes the outline on its first. */
const sketched = (press: Press): void => {
  const draft = sketch.value
  const held = rules.value
  if (!draft || !held) return
  if (closes(draft, press.at, press.scale, held)) {
    placing.editOutlines(closed(drawn(outlines.value, closedDraft(draft, held))))
  } else if (vertexAt(draft, press.at, press.scale) === null) {
    placing.editOutlines(drawn(outlines.value, added(draft, press.at, held)))
  }
}

function placed(side: 'a' | 'b', press: Press): void {
  if (locked.value) {
    if (side === 'b') sketched(press)
    return
  }
  edit(clicked(pairs.value, side, press.at, press.scale, props.limits.pair_radius))
}

function dragged(side: 'a' | 'b', index: number, at: Point, fresh: boolean): void {
  if (!locked.value) edit(moved(pairs.value, index, side, at, fresh))
}

const draw = (kind: Kind, index?: number): void =>
  placing.editOutlines(begun(outlines.value, kind, index))

const undoPoint = (): void => {
  if (sketch.value) placing.editOutlines(drawn(outlines.value, undoneDraft(sketch.value)))
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
        :locked="locked"
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
        :shapes="shapes"
        :locked="locked"
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
      <p v-if="line" class="stage__note mono" data-proposal>{{ line }}</p>
      <div v-if="waitingProposals > 0" class="outline__row" data-proposed-bar>
        <button
          class="btn btn-secondary"
          type="button"
          :disabled="accepted(pairs) === pairs"
          @click="edit(accepted(pairs))"
        >
          Accept
        </button>
        <button class="btn btn-secondary" type="button" @click="edit(acceptedAll(pairs))">Accept all</button>
      </div>
      <span class="section-label">limb and exclusions</span>
      <div class="outline__row">
        <button class="btn btn-secondary" type="button" @click="draw('limb')">Draw limb</button>
        <button class="btn btn-secondary" type="button" @click="draw('exclusion')">Draw exclusion</button>
      </div>
      <p v-if="locked" class="stage__note mono" data-outline-hint>
        click on the render adds a point · the first point closes · the pairs wait
      </p>
      <ul v-if="outlineRows.length" class="outlinelist" data-outlines>
        <li v-for="row in outlineRows" :key="`${row.kind}-${row.index}`" class="outlinelist__row">
          <span class="outlinelist__text mono">{{ row.title }} · {{ row.label }}</span>
          <template v-if="row.drawing">
            <button class="btn btn-secondary" type="button" :disabled="!sketch || sketch.past.length === 0" @click="undoPoint">
              Undo
            </button>
            <button class="btn btn-secondary" type="button" @click="placing.editOutlines(stopped(outlines))">Stop</button>
          </template>
          <button v-else class="btn btn-secondary" type="button" @click="draw(row.kind, row.index)">Edit</button>
        </li>
      </ul>
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
