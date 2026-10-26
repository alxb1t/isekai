<script setup lang="ts">
import { noun } from '../words'
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { quoteRender, startRender } from '../api'
import { useKeys } from '../composables/useKeys'
import { useHeldFocus } from '../composables/useHeldFocus'
import { modded, plain } from '../stores/keys'
import { useBatchStore } from '../stores/batch'
import { clock, useLiveStore } from '../stores/live'
import type { Quote } from '../types'
import KeyHint from './KeyHint.vue'

/* The Render dialog (design spec J4·1): per flow what renders and what is left
   out, the estimate and its limit, and the price at most. It has no URL, so a
   reload never reopens a confirmation that spends; ⌘↵ is the only act here that
   rents. It belongs to its page: confirming closes it before the session opens.
   A modal dialog: the focus waits on *Keep the volume open*, where `↵` does
   nothing, so only ⌘↵ spends. */
const props = defineProps<{ batch: string }>()
const emit = defineEmits<{ close: [] }>()
const router = useRouter()
const live = useLiveStore()
const store = useBatchStore()
const quote = ref<Quote | null>(null)
const refusal = ref<string | null>(null)
const keepOpen = ref(false)
const starting = ref(false)
const dialog = ref<HTMLDialogElement | null>(null)
const keep = ref<HTMLInputElement | null>(null)

const total = computed(() => quote.value?.flows.reduce((sum, one) => sum + one.images, 0) ?? 0)
const dollars = (amount: number) => (amount < 0.01 ? 'under $0.01' : `$${amount.toFixed(2)}`)
const minutes = (seconds: number) => `${Math.ceil(seconds / 60)} min`

async function confirm(): Promise<void> {
  if (!quote.value || quote.value.disabled || starting.value) return
  starting.value = true
  try {
    const { job } = await startRender(
      props.batch,
      keepOpen.value,
      quote.value.estimate.limit_s,
      total.value,
    )
    // Held at once, so the session's page draws from the render slot as it opens.
    live.hold(job)
    store.closeDialog()
    const id = job.session?.id
    void router.push(
      id
        ? { name: 'session', params: { batch: props.batch, id } }
        : { name: 'sessions', params: { batch: props.batch } },
    )
  } catch (reason) {
    refusal.value = (reason as Error).message
  } finally {
    starting.value = false
  }
}

/* The dialog itself is the backdrop's target: a click inside lands on its content. */
function outside(event: MouseEvent): void {
  if (event.target === dialog.value) emit('close')
}

useKeys('overlay', [
  { id: 'cancel', keys: plain('Escape'), label: 'cancel', run: () => emit('close') },
  { id: 'confirm', keys: [modded('Enter')], label: 'render', run: () => void confirm() },
])

useHeldFocus(dialog)

/* The checkbox is drawn with the quote, so it takes the focus once the quote lands. */
onMounted(async () => {
  dialog.value?.showModal()
  try {
    quote.value = await quoteRender(props.batch)
  } catch (reason) {
    refusal.value = (reason as Error).message
    return
  }
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
    @click="outside"
  >
    <header class="render-dialog__head">
      <span class="section-label">Render · {{ batch }} · on a rented GPU</span>
      <h2 class="render-dialog__title">
        Render {{ total }} image{{ total === 1 ? '' : 's' }}
      </h2>
    </header>
    <p v-if="refusal" class="render-dialog__refusal">
      <span class="refusal__mark" />{{ refusal }}
    </p>
    <template v-if="quote">
      <p v-for="one in quote.flows" :key="one.flow" class="render-dialog__flow mono">
        <span class="render-dialog__name">{{ one.flow }}</span>
        {{ one.images }} {{ noun(one.images, 'image') }}
        <span v-for="source in one.sources" :key="source.digest">
          · {{ source.name }} v{{ source.version }} ×{{ source.images }}</span
        >
      </p>
      <p v-if="quote.left_out.length" class="render-dialog__left mono" data-left-out>
        Not included:
        <span v-for="(one, index) in quote.left_out" :key="`${one.digest}|${one.flow}`"
          >{{ index ? ' · ' : '' }}{{ one.name }} · {{ one.flow }} is {{ one.reason }}</span
        >
      </p>
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
        :disabled="!quote || quote.disabled !== null || starting"
        @click="confirm"
      >
        Render<template v-if="quote"> · at most {{ dollars(quote.price.at_most) }}</template
        ><KeyHint command="confirm" />
      </button>
    </footer>
  </dialog>
</template>
