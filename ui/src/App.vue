<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import KeyHint from './components/KeyHint.vue'
import KeyList from './components/KeyList.vue'
import { useKeys } from './composables/useKeys'
import { head } from './composables/useQueue'
import { useBatchStore } from './stores/batch'
import { shifted, useKeyStore } from './stores/keys'
import { alerting, useLiveStore } from './stores/live'

/* The shell: the AppBar, the BillingBanner's slot, the route's screen and the
   JobStrip (design spec §3). Review is keyed by batch and flow, so moving to
   another run keeps the view and its autosave; another flow is a new view. */
const route = useRoute()
const router = useRouter()
const live = useLiveStore()
const { job, billing } = storeToRefs(live)
const { prepareTotals, renderTotals } = live

const alert = computed(() => alerting(billing.value))
const running = computed(() => job.value?.state === 'running')
/* `HH:MM` of a UTC time gpunit recorded, on this machine's clock. */
const hour = (at: string | null) =>
  at ? new Date(at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : ''

/* The strip shares its totals and the live clock with the Prepare and Render bars. */
const totals = computed(() => {
  const held = job.value
  if (!held) return ''
  if (held.state === 'running') return renderTotals(held) || prepareTotals(held)
  return `last: ${held.kind} · ${held.state}`
})

const batch = computed(() => (typeof route.params.batch === 'string' ? route.params.batch : null))
/* The page's one stream names the batch the screen shows, and the batch store holds it. */
const batchStore = useBatchStore()
watch(
  batch,
  (shown) => {
    batchStore.open(shown)
    live.follow({ batch: shown })
  },
  { immediate: true },
)
const place = computed(() => batch.value ?? 'library')
const screen = computed(() => route.name)
const key = computed(() =>
  route.name === 'review' ? `${route.params.batch}/${route.params.flow}` : route.path,
)

const queued = computed(() => (batchStore.hub ? head(batchStore.hub) : null))
const listing = ref(false)

const onBatch = () => batch.value !== null
function open(name: string): void {
  void router.push({ name, params: batch.value ? { batch: batch.value } : {} })
}

/* The keys every screen answers, outside a text field (D25). */
useKeys('everywhere', [
  { id: 'library', keys: [shifted('KeyL')], label: 'library', run: () => open('home') },
  { id: 'hub', keys: [shifted('KeyH')], label: 'hub', run: () => open('hub'), when: onBatch },
  {
    id: 'review',
    keys: [shifted('KeyR')],
    label: "review the queue's head",
    run: () => {
      if (queued.value && batch.value)
        void router.push({ name: 'review', params: { batch: batch.value, ...queued.value } })
    },
    when: () => queued.value !== null,
  },
  {
    id: 'renders',
    keys: [shifted('KeyI')],
    label: 'renders',
    run: () => open('renders'),
    when: onBatch,
  },
  { id: 'session', keys: [shifted('KeyS')], label: 'session', run: () => open('session') },
  {
    id: 'keys',
    keys: [shifted('Slash')],
    label: 'the key list',
    run: () => (listing.value = true),
  },
])

/* The page's one key listener: every command is a declaration in the key store. */
const keys = useKeyStore()
onMounted(() => window.addEventListener('keydown', keys.press))
onUnmounted(() => window.removeEventListener('keydown', keys.press))
</script>

<template>
  <div class="app">
    <header class="appbar">
      <RouterLink to="/" class="appbar__mark">isekai</RouterLink>
      <span class="appbar__place">{{ place }}</span>
      <template v-if="batch">
        <RouterLink
          :to="{ name: 'hub', params: { batch } }"
          class="appbar__tab"
          :class="{ 'appbar__tab--active': screen === 'hub' }"
          >Hub<KeyHint command="hub" /></RouterLink
        >
        <span class="appbar__tab" :class="{ 'appbar__tab--active': screen === 'review' }"
          >Review<KeyHint command="review" /></span
        >
        <RouterLink
          :to="{ name: 'renders', params: { batch } }"
          class="appbar__tab"
          :class="{ 'appbar__tab--active': screen === 'renders' || screen === 'render' }"
          >Renders<KeyHint command="renders" /></RouterLink
        >
      </template>
    </header>
    <!-- The BillingBanner: only when something may be billing; esc never closes it. -->
    <div v-if="alert" class="band" role="alert">
      <span v-if="billing?.pod">A pod may still be billing.</span>
      <span v-else
        >Volume gpunit-isekai is still open past its window and is billing.<template
          v-if="billing?.volume?.ends"
        >
          Window ended {{ hour(billing.volume.ends) }}.</template
        ></span
      >
      <RouterLink :to="{ name: 'session' }" class="band__resolve"
        >Resolve<KeyHint command="session" /></RouterLink
      >
    </div>
    <main class="app__screen">
      <RouterView :key="key" />
    </main>
    <KeyList v-if="listing" @close="listing = false" />
    <footer class="jobstrip">
      <span
        class="jobstrip__dot"
        :class="{ 'jobstrip__dot--running': running, 'jobstrip__dot--alert': alert }"
      />
      <span>job · {{ running ? job?.kind : 'idle' }}</span>
      <span class="jobstrip__totals">{{ totals }}</span>
      <span
        v-if="billing?.volume?.state === 'open'"
        class="jobstrip__volume"
        data-volume-item
        >volume open · until {{ hour(billing.volume.ends) }}</span
      >
    </footer>
  </div>
</template>
