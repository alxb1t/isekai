<script setup lang="ts">
import { noun } from '../words'
import { computed, nextTick, onMounted, ref } from 'vue'
import { quoteRender, startRender } from '../api'
import { dialogTitle } from '../bakes'
import { useEdges } from '../composables/useEdges'
import { useKeys } from '../composables/useKeys'
import { useHeldFocus } from '../composables/useHeldFocus'
import type { Move } from '../grid'
import { modded, plain } from '../stores/keys'
import { useCollectionStore } from '../stores/collection'
import { useDrawerStore } from '../stores/drawer'
import { clock, collectionsOf, useLiveStore } from '../stores/live'
import {
  allOut,
  confirmReason,
  drawnBakes,
  drawnFlows,
  tileMoved,
  tileRow,
  type Thumb,
} from '../thumbs'
import type { Quote, QuotedCollection, TakenOut } from '../types'
import KeyHint from './KeyHint.vue'

/* The Render dialog (design spec J4·1): a row per collection short of images or holding a bake, in
   the Library's order, each ticked; per flow the tiles of what renders; one
   session's estimate, its limit against the ceiling, and the price at most.
   Unticking a row quotes the rest again, and so does taking a photograph out by
   its tile's `×` or `⌫`, or by its bake row's `×`, which takes its flow out with its
   bakes; a row with none left reads *all removed*. It has no URL,
   so a reload never reopens a confirmation that spends; ⌘↵ is the only act here
   that rents. It belongs to its page: confirming closes it and opens the render
   drawer over it. A modal dialog: the focus opens on the first tile, where `↵`
   does nothing, so only ⌘↵ spends. */
const emit = defineEmits<{ close: [] }>()
const live = useLiveStore()
const store = useCollectionStore()
const drawer = useDrawerStore()
/* Every row the first quote listed; a row unticked keeps its place. */
const rows = ref<QuotedCollection[]>([])
const ticked = ref<Set<string>>(new Set())
/* The photographs taken out, by their tile's key. */
const out = ref<Map<string, TakenOut>>(new Map())
const outKeys = computed(() => new Set(out.value.keys()))
const quote = ref<Quote | null>(null)
const quoting = ref(true)
const refusal = ref<string | null>(null)
const keepOpen = ref(false)
const starting = ref(false)
const dialog = ref<HTMLDialogElement | null>(null)
const keep = ref<HTMLInputElement | null>(null)
const list = ref<HTMLElement | null>(null)
/* The focused tile's place across the dialog, or null off the tiles. */
const focused = ref<number | null>(null)
const reveal = useEdges(() => list.value, true)
/* The newest quote asked for; an answer to an older one is dropped. */
let asked = 0

/* Each row as the newest quote reads it, else as the first did; a row all out is gone. */
const shown = computed(() => {
  const fresh = new Map((quote.value?.collections ?? []).map((one) => [one.collection, one]))
  return rows.value.map((first) => {
    const row = fresh.get(first.collection) ?? first
    return {
      ...row,
      gone: allOut(first, outKeys.value),
      drawn: drawnFlows(row, outKeys.value),
      baked: drawnBakes(row, outKeys.value),
    }
  })
})
/* Each tile drawn, in the dialog's order, with its row and flow. */
const tiles = computed(() =>
  shown.value.flatMap((row) =>
    row.drawn.flatMap((one) =>
      one.thumbs.map((thumb) => ({ collection: row.collection, flow: one.flow, thumb })),
    ),
  ),
)
const places = computed(() => new Map(tiles.value.map((one, index) => [one.thumb.key, index])))
/* Each drawn flow's tile count: the tiles' grid rows. */
const sizes = computed(() =>
  shown.value.flatMap((row) => row.drawn.map((one) => one.thumbs.length)),
)
/* The thumbnails whose source answered an error, drawn from the run's own photograph. */
const fell = ref<Set<string>>(new Set())
const fall = (key: string) => {
  fell.value = new Set(fell.value).add(key)
}
const names = computed(() =>
  rows.value
    .filter((one) => ticked.value.has(one.collection) && !allOut(one, outKeys.value))
    .map((one) => one.collection),
)
const taken = computed(() =>
  [...out.value.values()].filter((one) => names.value.includes(one.collection)),
)
const reason = computed(() =>
  quote.value ? confirmReason(rows.value, outKeys.value, quote.value.disabled) : null,
)
const total = computed(
  () => quote.value?.collections.reduce((sum, one) => sum + one.images, 0) ?? 0,
)
const bakes = computed(
  () => quote.value?.collections.reduce((sum, one) => sum + one.bakes.length, 0) ?? 0,
)
/* The estimate's parts, none for a count of zero. */
const counts = computed(() =>
  [
    total.value > 0 ? `${total.value} ${noun(total.value, 'image')}` : null,
    bakes.value > 0 ? `${bakes.value} ${noun(bakes.value, 'bake')}` : null,
  ].filter((part) => part !== null),
)
const dollars = (amount: number) => (amount < 0.01 ? 'under $0.01' : `$${amount.toFixed(2)}`)
const minutes = (seconds: number) => `${Math.ceil(seconds / 60)} min`

/* Quote `collections`, less what is taken out, or every collection short with none named. */
async function ask(collections?: string[]): Promise<Quote | null> {
  const mine = ++asked
  quoting.value = true
  try {
    const found = await quoteRender(collections, taken.value)
    if (mine !== asked) return null
    quote.value = found
    refusal.value = null
    return found
  } catch (reason) {
    if (mine === asked) refusal.value = (reason as Error).message
    return null
  } finally {
    if (mine === asked) quoting.value = false
  }
}

function toggle(name: string): void {
  const next = new Set(ticked.value)
  if (!next.delete(name)) next.add(name)
  ticked.value = next
  void ask(names.value)
}

/* Focus tile `index`; a key's move reveals it by the edges' rule, its row its flow's. */
function focusTile(index: number, key = false): void {
  void nextTick(() => {
    const tile = list.value?.querySelectorAll<HTMLElement>('[data-tile]')[index]
    if (!tile) return
    if (!key) return tile.focus()
    tile.focus({ preventScroll: true })
    reveal(tile, tileRow(sizes.value, index), sizes.value.length)
  })
}

function move(to: Move): void {
  if (focused.value !== null) focusTile(tileMoved(sizes.value, focused.value, to), true)
}

/* Take a photograph's flow out of the session and quote the rest; the focus takes the tile
   now in its place, else the last, else *Keep the volume open*. */
function takeOut(collection: string, flow: string, thumb: Thumb): void {
  const at = places.value.get(thumb.key) ?? 0
  out.value = new Map(out.value).set(thumb.key, { collection, run: thumb.run, flow })
  void ask(names.value)
  void nextTick(() => {
    const left = tiles.value.length
    if (left) focusTile(Math.min(at, left - 1))
    else keep.value?.focus()
  })
}

async function confirm(): Promise<void> {
  if (!quote.value || reason.value || quoting.value || starting.value) return
  starting.value = true
  try {
    const { job } = await startRender(
      names.value,
      keepOpen.value,
      quote.value.estimate.limit_s,
      total.value,
      bakes.value,
      taken.value,
    )
    // Held at once, so the drawer draws from the render slot as it opens.
    live.hold(job)
    store.closeDialog()
    const id = job.session?.id
    if (id) drawer.openOn(collectionsOf(job), id)
  } catch (reason) {
    refusal.value = (reason as Error).message
  } finally {
    starting.value = false
  }
}

const onTile = () => focused.value !== null

useKeys('overlay', [
  { id: 'cancel', keys: plain('Escape'), label: 'cancel', run: () => emit('close') },
  { id: 'confirm', keys: [modded('Enter')], label: 'render', run: () => void confirm() },
  ...(
    [
      ['photo-left', plain('KeyH', 'ArrowLeft'), 'column-'],
      ['photo-right', plain('KeyL', 'ArrowRight'), 'column+'],
      ['photo-up', plain('KeyK', 'ArrowUp'), 'row-'],
      ['photo-down', plain('KeyJ', 'ArrowDown'), 'row+'],
    ] as const
  ).map(([id, keys, to]) => ({
    id,
    keys: [...keys],
    label: 'move',
    run: () => move(to),
    when: onTile,
  })),
  {
    id: 'take-out',
    keys: plain('Backspace'),
    label: 'take the photograph out',
    run: () => {
      const one = focused.value === null ? undefined : tiles.value[focused.value]
      if (one) takeOut(one.collection, one.flow, one.thumb)
    },
    when: onTile,
  },
])

useHeldFocus(dialog, () => emit('close'))

/* The tiles are drawn with the quote, so the first takes the focus once the quote lands,
   else the checkbox. */
onMounted(async () => {
  dialog.value?.showModal()
  const found = await ask()
  if (!found) return
  rows.value = found.collections
  ticked.value = new Set(found.collections.map((one) => one.collection))
  await nextTick()
  if (tiles.value.length) focusTile(0)
  else keep.value?.focus()
})
</script>

<template>
  <dialog
    ref="dialog"
    class="render-dialog"
    aria-label="Render"
    @cancel.prevent
  >
    <header class="render-dialog__head">
      <span class="section-label">Render · on a rented GPU</span>
      <h2 class="render-dialog__title">{{ dialogTitle(total, bakes) }}</h2>
    </header>
    <p v-if="refusal" class="render-dialog__refusal">
      <span class="refusal__mark" />{{ refusal }}
    </p>
    <template v-if="quote">
      <div ref="list" class="render-dialog__collections">
        <section
          v-for="row in shown"
          :key="row.collection"
          class="render-dialog__collection"
          :class="{ 'render-dialog__collection--off': !ticked.has(row.collection) }"
          :data-collection="row.collection"
        >
          <label class="render-dialog__tick mono">
            <input
              type="checkbox"
              data-tick
              :checked="ticked.has(row.collection) && !row.gone"
              :disabled="row.gone"
              @change="toggle(row.collection)"
            />
            <span class="render-dialog__name">{{ row.collection }}</span>
            <template v-if="row.gone">all removed</template>
            <template v-else>
              {{ row.images }} {{ noun(row.images, 'image') }}
              <template v-if="row.bakes.length">
                · {{ row.bakes.length }} {{ noun(row.bakes.length, 'bake') }}
              </template>
            </template>
          </label>
          <div v-for="one in row.drawn" :key="one.flow" :data-flow="one.flow">
            <p class="render-dialog__flow mono">
              <span class="render-dialog__name">{{ one.flow }}</span>
              {{ one.images }} {{ noun(one.images, 'image') }}
            </p>
            <div class="render-dialog__thumbs">
              <div
                v-for="thumb in one.thumbs"
                :key="thumb.key"
                class="render-dialog__thumb"
                data-tile
                :title="thumb.title"
                :tabindex="places.get(thumb.key) === (focused ?? 0) ? 0 : -1"
                @focusin="focused = places.get(thumb.key) ?? null"
                @focusout="focused = null"
              >
                <img
                  alt=""
                  loading="lazy"
                  :src="fell.has(thumb.key) ? thumb.fallback : thumb.src"
                  @error="fall(thumb.key)"
                />
                <span v-if="thumb.times" class="render-dialog__times mono">×{{ thumb.times }}</span>
                <button
                  class="render-dialog__remove"
                  type="button"
                  tabindex="-1"
                  :aria-label="`Take ${thumb.title} out`"
                  @click="takeOut(row.collection, one.flow, thumb)"
                >
                  ×
                </button>
              </div>
              <span v-if="one.more" class="render-dialog__more mono">+{{ one.more }}</span>
            </div>
          </div>
          <div v-if="row.baked.length" data-bakes>
            <p class="render-dialog__flow mono">
              <span class="render-dialog__name">bakes</span>
              {{ row.baked.length }} {{ noun(row.baked.length, 'bake') }}
            </p>
            <ul class="render-dialog__bakes">
              <li
                v-for="(one, at) in row.baked"
                :key="`${one.key}|${at}`"
                class="render-dialog__bake"
                data-bake
              >
                <img
                  class="render-dialog__bake-thumb"
                  alt=""
                  loading="lazy"
                  :src="fell.has(one.key) ? one.fallback : one.src"
                  @error="fall(one.key)"
                />
                <span class="render-dialog__bake-name">{{ one.title }}</span>
                <span class="render-dialog__bake-label mono">{{ one.label }}</span>
                <button
                  class="render-dialog__bake-remove"
                  type="button"
                  :aria-label="`Take ${one.title} out, with its bakes`"
                  @click="takeOut(row.collection, one.flow, one)"
                >
                  ×
                </button>
              </li>
            </ul>
          </div>
          <p v-if="row.refused" class="render-dialog__left mono">{{ row.refused }}</p>
        </section>
      </div>
      <dl class="render-dialog__table mono">
        <dt class="section-label">Estimate</dt>
        <dd>
          boot {{ clock(quote.estimate.boot_s) }} ·
          <template v-for="part in counts" :key="part">{{ part }} · </template>teardown
          {{ clock(quote.estimate.teardown_s) }}
        </dd>
        <dd class="render-dialog__figure">{{ minutes(quote.estimate.seconds) }}</dd>
        <dt />
        <dd>limit, at most</dd>
        <dd class="render-dialog__figure" data-limit>{{ clock(quote.estimate.limit_s) }}</dd>
        <dt />
        <dd>gpunit.toml's ceiling</dd>
        <dd class="render-dialog__figure" data-ceiling>{{ clock(quote.ceiling_s) }}</dd>
        <dt class="section-label">Price</dt>
        <dd>the estimate, pod and volume</dd>
        <dd class="render-dialog__figure">about {{ dollars(quote.price.about) }}</dd>
        <dt />
        <dd>at the limit</dd>
        <dd class="render-dialog__figure">at most {{ dollars(quote.price.at_most) }}</dd>
      </dl>
      <label class="render-dialog__keep">
        <input ref="keep" v-model="keepOpen" type="checkbox" data-keep-open />
        Keep the volume open after the session
        <span class="mono">{{ dollars(quote.price.keep_open) }}</span>
      </label>
    </template>
    <footer class="render-dialog__actions">
      <span v-if="reason" class="render-dialog__reason">{{ reason }}</span>
      <button class="btn btn-secondary" type="button" @click="emit('close')">
        Cancel<KeyHint command="cancel" />
      </button>
      <button
        class="btn btn-primary"
        type="button"
        data-confirm
        :disabled="!quote || reason !== null || quoting || starting"
        @click="confirm"
      >
        {{ total === 0 && bakes > 0 ? 'Bake' : 'Render'
        }}<template v-if="quote"> · at most {{ dollars(quote.price.at_most) }}</template
        ><KeyHint command="confirm" />
      </button>
    </footer>
  </dialog>
</template>
