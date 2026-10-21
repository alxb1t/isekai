<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { quoteRender, startRender } from '../api'
import { useLive } from '../composables/useLive'
import type { Quote } from '../types'

/* The Render dialog (design spec J4·1): per flow what renders and what is left
   out, the estimate and its limit, and the price at most. It has no URL, so a
   reload never reopens a confirmation that spends; ⌘↵ is the only act here that
   rents. */
const props = defineProps<{ batch: string }>()
const emit = defineEmits<{ close: [] }>()
const router = useRouter()
const { clock } = useLive()
const quote = ref<Quote | null>(null)
const refusal = ref<string | null>(null)
const keepOpen = ref(false)
const starting = ref(false)

const total = computed(() => quote.value?.flows.reduce((sum, one) => sum + one.images, 0) ?? 0)
const dollars = (amount: number) => (amount < 0.01 ? 'under $0.01' : `$${amount.toFixed(2)}`)
const minutes = (seconds: number) => `${Math.ceil(seconds / 60)} min`

async function confirm(): Promise<void> {
  if (!quote.value || quote.value.disabled || starting.value) return
  starting.value = true
  try {
    await startRender(props.batch, keepOpen.value, quote.value.estimate.limit_s, total.value)
    void router.push({ name: 'session' })
  } catch (reason) {
    refusal.value = (reason as Error).message
  } finally {
    starting.value = false
  }
}

function onKey(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault()
    emit('close')
  } else if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault()
    void confirm()
  }
}

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  try {
    quote.value = await quoteRender(props.batch)
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
})
onUnmounted(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="scrim" @click.self="emit('close')">
    <section class="render-dialog" role="dialog" aria-label="Render">
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
          {{ one.images }} image{{ one.images === 1 ? '' : 's' }}
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
            boot {{ clock(quote.estimate.boot_s) }} · {{ total }} images ·
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
          <input v-model="keepOpen" type="checkbox" />
          Keep the volume open after the session
          <span class="mono">{{ dollars(quote.price.keep_open) }}</span>
        </label>
      </template>
      <footer class="render-dialog__actions">
        <span v-if="quote?.disabled" class="render-dialog__reason">{{ quote.disabled }}</span>
        <button class="btn btn-secondary" type="button" @click="emit('close')">
          Cancel<span class="appbar__key">esc</span>
        </button>
        <button
          class="btn btn-primary"
          type="button"
          data-confirm
          :disabled="!quote || quote.disabled !== null || starting"
          @click="confirm"
        >
          Render<template v-if="quote"> · at most {{ dollars(quote.price.at_most) }}</template
          ><span class="appbar__key">⌘↵</span>
        </button>
      </footer>
    </section>
  </div>
</template>
