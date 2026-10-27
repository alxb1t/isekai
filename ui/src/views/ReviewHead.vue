<script lang="ts">
/* The flow each collection's chooser last opened, so a return lands on its row. */
const chosen = new Map<string, string>()
</script>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { sourceThumbAt } from '../api'
import KeyHint from '../components/KeyHint.vue'
import LoadingSkeleton from '../components/LoadingSkeleton.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { chooses, flowsWaiting, head } from '../composables/useQueue'
import { useKeys } from '../composables/useKeys'
import { clamp, kept } from '../grid'
import { useCollectionStore } from '../stores/collection'
import { plain } from '../stores/keys'
import { noun } from '../words'

/* A collection's Review (design spec J3). With two or more flows waiting, a chooser:
   a row per flow, its counts and its waiting photographs. With one, its head's
   URL takes this one's place, so the address bar names the sheet (§4). With
   none, the way to the hub. */
const props = defineProps<{ collection: string }>()
const router = useRouter()
const store = useCollectionStore()
const refusal = ref<string | null>(null)
const empty = ref(false)
const choosing = ref(false)
const list = ref<HTMLElement | null>(null)
const waiting = computed(() => (store.hub ? flowsWaiting(store.hub) : []))

/* How many of a flow's waiting photographs its row shows, before `+n`. */
const ROW_THUMBS = 15

function review(digest: string, flow: string): void {
  chosen.set(props.collection, flow)
  void router.push({ name: 'review', params: { collection: props.collection, digest, flow } })
}

/* A row opens its flow's head: its first unapproved sheet, else its first short. */
function open(flow: string): void {
  const at = store.hub ? head(store.hub, [flow]) : null
  if (at) review(at.digest, flow)
}

function rows(): HTMLElement[] {
  return [...(list.value?.querySelectorAll<HTMLElement>('[data-flow-row]') ?? [])]
}
const at = () => rows().indexOf(document.activeElement as HTMLElement)
/* The flow of the row holding the focus, or undefined. */
const focusedFlow = () => (document.activeElement as HTMLElement | null)?.dataset?.flowRow

function walk(step: -1 | 1): void {
  const held = rows()
  held[clamp(at() + step, held.length - 1)]?.focus()
}

useKeys('screen', [
  { id: 'next', keys: plain('KeyJ', 'ArrowDown'), label: 'next flow', run: () => walk(1) },
  { id: 'previous', keys: plain('KeyK', 'ArrowUp'), label: 'previous flow', run: () => walk(-1) },
  {
    id: 'open',
    keys: plain('Enter'),
    label: 'review the flow',
    run: () => open(focusedFlow() ?? ''),
    when: () => choosing.value && at() >= 0,
  },
])

/* The hub the store holds is kept current by the page's stream; it is read only
   when none is held yet. */
onMounted(async () => {
  let info = store.hub
  try {
    info ??= await store.reloadHub()
  } catch (reason) {
    refusal.value = (reason as Error).message
    return
  }
  if (chooses(info)) {
    choosing.value = true
    await nextTick()
    kept(rows(), (row) => row.dataset.flowRow ?? '', chosen.get(props.collection) ?? null)?.focus()
    return
  }
  const first = head(info)
  if (first) void router.replace({ name: 'review', params: { collection: props.collection, ...first } })
  else empty.value = true
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="choosing" class="review-head review-head--chooser" data-chooser>
    <div ref="list" class="library">
      <div
        v-for="one in waiting"
        :key="one.flow"
        class="library__row library__row--collection"
        :data-flow-row="one.flow"
        tabindex="0"
        @click="open(one.flow)"
      >
        <div class="library__head">
          <span class="library__name">{{ one.flow }}</span>
          <span class="library__meta">
            {{ one.approve }} to approve · {{ one.short }} {{ noun(one.short, 'sheet') }} short
            of images
          </span>
          <span class="library__meta library__when">open ↵</span>
        </div>
        <div class="library__thumbs">
          <button
            v-for="source in one.sources.slice(0, ROW_THUMBS)"
            :key="source.digest"
            class="hub__thumb"
            type="button"
            :aria-label="`review ${source.name}`"
            @click.stop="review(source.digest, one.flow)"
          >
            <img :src="sourceThumbAt(collection, source.name)" alt="" loading="lazy" />
          </button>
          <span v-if="one.sources.length > ROW_THUMBS" class="library__meta">
            +{{ one.sources.length - ROW_THUMBS }}
          </span>
        </div>
      </div>
    </div>
  </section>
  <section v-else-if="empty" class="review-head" data-review-head>
    <p>No sheet waits for review.</p>
    <RouterLink :to="{ name: 'hub', params: { collection } }" class="btn btn-secondary"
      >Hub<KeyHint command="hub" /></RouterLink
    >
  </section>
  <LoadingSkeleton v-else :reading="null" :vocabulary="0" />
</template>
