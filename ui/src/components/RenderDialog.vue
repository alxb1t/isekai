<script setup lang="ts">
import { noun } from '../words'
import { computed, nextTick, onMounted, ref } from 'vue'
import { quoteRender, startRender } from '../api'
import { useKeys } from '../composables/useKeys'
import { useHeldFocus } from '../composables/useHeldFocus'
import { modded, plain } from '../stores/keys'
import { useCollectionStore } from '../stores/collection'
import { useDrawerStore } from '../stores/drawer'
import { clock, useLiveStore } from '../stores/live'
import type { Quote, QuotedCollection } from '../types'
import KeyHint from './KeyHint.vue'

/* The Render dialog (design spec J4·1): a row per collection short of images, in
   the Library's order, each ticked; per flow what renders and what is left out;
   one session's estimate, its limit against the ceiling, and the price at most.
   Unticking a row quotes the rest again. It has no URL, so a reload never reopens
   a confirmation that spends; ⌘↵ is the only act here that rents. It belongs to
   its page: confirming closes it and opens the render drawer over it. A modal
   dialog: the focus waits on *Keep the volume open*, where `↵` does nothing, so
   only ⌘↵ spends. */
defineProps<{ collection: string }>()
const emit = defineEmits<{ close: [] }>()
const live = useLiveStore()
const store = useCollectionStore()
const drawer = useDrawerStore()
/* Every row the first quote listed; a row unticked keeps its place. */
const rows = ref<QuotedCollection[]>([])
const ticked = ref<Set<string>>(new Set())
const quote = ref<Quote | null>(null)
const quoting = ref(true)
const refusal = ref<string | null>(null)
const keepOpen = ref(false)
const starting = ref(false)
const dialog = ref<HTMLDialogElement | null>(null)
const keep = ref<HTMLInputElement | null>(null)
/* The newest quote asked for; an answer to an older one is dropped. */
let asked = 0

/* Each row as the newest quote reads it, else as the first did. */
const shown = computed(() => {
  const fresh = new Map((quote.value?.collections ?? []).map((one) => [one.collection, one]))
  return rows.value.map((one) => fresh.get(one.collection) ?? one)
})
const names = computed(() =>
  rows.value.map((one) => one.collection).filter((name) => ticked.value.has(name)),
)
const total = computed(
  () => quote.value?.collections.reduce((sum, one) => sum + one.images, 0) ?? 0,
)
const dollars = (amount: number) => (amount < 0.01 ? 'under $0.01' : `$${amount.toFixed(2)}`)
const minutes = (seconds: number) => `${Math.ceil(seconds / 60)} min`

/* Quote `collections`, or every collection short with none named. */
async function ask(collections?: string[]): Promise<Quote | null> {
  const mine = ++asked
  quoting.value = true
  try {
    const found = await quoteRender(collections)
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

async function confirm(): Promise<void> {
  if (!quote.value || quote.value.disabled || quoting.value || starting.value) return
  starting.value = true
  try {
    const { job } = await startRender(
      names.value,
      keepOpen.value,
      quote.value.estimate.limit_s,
      total.value,
    )
    // Held at once, so the drawer draws from the render slot as it opens.
    live.hold(job)
    store.closeDialog()
    const id = job.session?.id
    if (id) drawer.openOn(job.collection, id)
  } catch (reason) {
    refusal.value = (reason as Error).message
  } finally {
    starting.value = false
  }
}

useKeys('overlay', [
  { id: 'cancel', keys: plain('Escape'), label: 'cancel', run: () => emit('close') },
  { id: 'confirm', keys: [modded('Enter')], label: 'render', run: () => void confirm() },
])

useHeldFocus(dialog, () => emit('close'))

/* The checkbox is drawn with the quote, so it takes the focus once the quote lands. */
onMounted(async () => {
  dialog.value?.showModal()
  const found = await ask()
  if (!found) return
  rows.value = found.collections
  ticked.value = new Set(found.collections.map((one) => one.collection))
  await nextTick()
  keep.value?.focus()
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
      <h2 class="render-dialog__title">
        Render {{ total }} image{{ total === 1 ? '' : 's' }}
      </h2>
    </header>
    <p v-if="refusal" class="render-dialog__refusal">
      <span class="refusal__mark" />{{ refusal }}
    </p>
    <template v-if="quote">
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
            :checked="ticked.has(row.collection)"
            @change="toggle(row.collection)"
          />
          <span class="render-dialog__name">{{ row.collection }}</span>
          {{ row.images }} {{ noun(row.images, 'image') }}
        </label>
        <p v-for="one in row.flows" :key="one.flow" class="render-dialog__flow mono">
          <span class="render-dialog__name">{{ one.flow }}</span>
          {{ one.images }} {{ noun(one.images, 'image') }}
          <span v-for="source in one.sources" :key="source.digest">
            · {{ source.name }} v{{ source.version }} ×{{ source.images }}</span
          >
        </p>
        <p v-if="row.left_out.length" class="render-dialog__left mono" data-left-out>
          Not included:
          <span v-for="(one, index) in row.left_out" :key="`${one.digest}|${one.flow}`"
            >{{ index ? ' · ' : '' }}{{ one.name }} · {{ one.flow }} is {{ one.reason }}</span
          >
        </p>
        <p v-if="row.refused" class="render-dialog__left mono">{{ row.refused }}</p>
      </section>
      <dl class="render-dialog__table mono">
        <dt class="section-label">Estimate</dt>
        <dd>
          boot {{ clock(quote.estimate.boot_s) }} · {{ total }} {{ noun(total, 'image') }} ·
          teardown {{ clock(quote.estimate.teardown_s) }}
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
      <span v-if="quote?.disabled" class="render-dialog__reason">{{ quote.disabled }}</span>
      <button class="btn btn-secondary" type="button" @click="emit('close')">
        Cancel<KeyHint command="cancel" />
      </button>
      <button
        class="btn btn-primary"
        type="button"
        data-confirm
        :disabled="!quote || quote.disabled !== null || quoting || starting"
        @click="confirm"
      >
        Render<template v-if="quote"> · at most {{ dollars(quote.price.at_most) }}</template
        ><KeyHint command="confirm" />
      </button>
    </footer>
  </dialog>
</template>
