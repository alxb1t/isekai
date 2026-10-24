<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import KeyHint from './components/KeyHint.vue'
import KeyList from './components/KeyList.vue'
import { useKeys } from './composables/useKeys'
import { queue } from './composables/useQueue'
import { lasted } from './sessions'
import { useBatchStore } from './stores/batch'
import { shifted, useKeyStore } from './stores/keys'
import { alerting, clock, useLiveStore } from './stores/live'

/* The shell: the AppBar, the BillingBanner's slot, the route's screen and the
   JobStrip (design spec §3). Review is keyed by batch and flow, so moving to
   another run keeps the view and its autosave; another flow is a new view. */
const route = useRoute()
const router = useRouter()
const live = useLiveStore()
const { jobs, billing, now, activeRender, renderConfirmed, sessionsRefusal } = storeToRefs(live)
const { prepareTotals, renderTotals } = live

const alert = computed(() => alerting(billing.value))
/* Each kind's job, running or ended, Prepare's first. */
const held = computed(() => [jobs.value.prepare, jobs.value.render].filter((slot) => slot !== null))
const runningJobs = computed(() => held.value.filter((slot) => slot.state === 'running'))
const running = computed(() => runningJobs.value.length > 0)
/* `HH:MM` of a UTC time gpunit recorded, on this machine's clock. */
const hour = (at: string | null) =>
  at ? new Date(at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : ''

/* The strip's items: one per running job, sharing its totals and the live clock
   with its bar; with none running, each kind's last outcome. */
const items = computed(() =>
  running.value
    ? runningJobs.value.map((slot) => ({
        kind: slot.kind,
        label: `job · ${slot.kind}`,
        totals: renderTotals(slot) || prepareTotals(slot),
      }))
    : held.value.map((slot) => ({
        kind: slot.kind,
        label: '',
        totals: `last: ${slot.kind} · ${slot.state}`,
      })),
)

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

/* The Review tab counts the batch's unapproved sheets, every flow's. */
const unapproved = computed(() => {
  const held = batchStore.hub
  return held ? held.flows.reduce((sum, flow) => sum + queue(held, flow).length, 0) : 0
})
const listing = ref(false)

const onBatch = () => batch.value !== null
function open(name: string): void {
  void router.push({ name, params: batch.value ? { batch: batch.value } : {} })
}

/* The running render's session, wherever the screen is, and its clock. */
const rendered = computed(() => {
  const held = activeRender.value
  if (!held) return null
  const elapsed = lasted(held.started, null, true, now.value) ?? 0
  return { batch: held.batch, id: held.id, clock: clock(elapsed) }
})
/* ⇧S: the running session, else the open batch's sessions. */
function sessions(): void {
  const held = rendered.value
  if (held) void router.push({ name: 'session', params: { batch: held.batch, id: held.id } })
  else open('sessions')
}

/* The keys every screen answers, outside a text field (D25). */
useKeys('everywhere', [
  { id: 'library', keys: [shifted('KeyL')], label: 'library', run: () => open('home') },
  { id: 'hub', keys: [shifted('KeyH')], label: 'hub', run: () => open('hub'), when: onBatch },
  { id: 'review', keys: [shifted('KeyR')], label: 'review', run: () => open('review-head'), when: onBatch },
  {
    id: 'renders',
    keys: [shifted('KeyI')],
    label: 'renders',
    run: () => open('renders'),
    when: onBatch,
  },
  { id: 'session', keys: [shifted('KeyS')], label: 'sessions', run: sessions, when: onBatch },
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
        <RouterLink
          :to="{ name: 'review-head', params: { batch } }"
          class="appbar__tab"
          :class="{ 'appbar__tab--active': screen === 'review' || screen === 'review-head' }"
          data-review-tab
          >Review<span v-if="unapproved" class="appbar__count">{{ unapproved }}</span
          ><KeyHint command="review" /></RouterLink
        >
        <RouterLink
          :to="{ name: 'renders', params: { batch } }"
          class="appbar__tab"
          :class="{ 'appbar__tab--active': screen === 'renders' || screen === 'render' }"
          >Renders<KeyHint command="renders" /></RouterLink
        >
        <RouterLink
          :to="{ name: 'sessions', params: { batch } }"
          class="appbar__tab"
          :class="{ 'appbar__tab--active': screen === 'sessions' || screen === 'session' }"
          data-sessions-tab
          >Sessions<KeyHint command="session" /></RouterLink
        >
      </template>
      <!-- A running render bills by the minute, so every screen shows it. -->
      <RouterLink
        v-if="rendered"
        :to="{ name: 'session', params: { batch: rendered.batch, id: rendered.id } }"
        class="appbar__render mono"
        data-rendering
        >● render {{ rendered.clock }}</RouterLink
      >
      <!-- A failed read of the disk's running renders leaves its last answer unconfirmed. -->
      <span
        v-if="!renderConfirmed"
        class="appbar__render mono"
        :title="sessionsRefusal ?? ''"
        data-sessions-unconfirmed
        >running renders unconfirmed</span
      >
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
      <RouterLink :to="{ name: 'billing' }" class="band__resolve">Resolve</RouterLink>
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
      <span v-if="!running">job · idle</span>
      <template v-for="item in items" :key="item.kind">
        <span v-if="item.label">{{ item.label }}</span>
        <span class="jobstrip__totals" :data-job-item="item.kind">{{ item.totals }}</span>
      </template>
      <span
        v-if="billing?.volume?.state === 'open'"
        class="jobstrip__volume"
        data-volume-item
        >volume open · until {{ hour(billing.volume.ends) }}</span
      >
    </footer>
  </div>
</template>
