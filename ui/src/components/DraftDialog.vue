<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { draft } from '../api'
import { useKeys } from '../composables/useKeys'
import { useHeldFocus } from '../composables/useHeldFocus'
import { imageKey } from '../cells'
import { clamp } from '../grid'
import { plain, shifted } from '../stores/keys'
import type { DraftedImage, ImageRef, RefusedImage } from '../types'
import KeyHint from './KeyHint.vue'

/* *Draft from this* (design spec J5·3): a row per offered flow, the first
   image's own first, named *revise* where every image is of it, and focused. `j` `k` move, `↵` drafts and opens Review
   on the first draft, `Esc` closes. All or nothing: a refusal lists every image
   and offers to deselect the refused. A target's edited waiting draft is opened,
   not replaced; beside written drafts, the dialog names it `already waiting`. */
const props = defineProps<{ collection: string; images: ImageRef[]; targets: string[] }>()
const emit = defineEmits<{ close: [] }>()
const router = useRouter()
/* The target the last draft was asked for. */
const chosen = ref<string | null>(null)
const refused = ref<RefusedImage[] | null>(null)
const failure = ref<string | null>(null)
const writing = ref(false)
/* The answer of a selection some of whose targets were already waiting. */
const answered = ref<DraftedImage[] | null>(null)
const dialog = ref<HTMLDialogElement | null>(null)

useHeldFocus(dialog, () => emit('close'))
onMounted(() => {
  dialog.value?.showModal()
  rows()[0]?.focus()
})

const title = computed(() => {
  const [one] = props.images
  return props.images.length === 1
    ? `Draft from this · ${one.flow} v${one.version} · seed ${one.seed}`
    : `Draft from this · ${props.images.length} images`
})
const revises = (target: string) => props.images.every((one) => one.flow === target)
const rowsFor = computed(() => {
  const own = props.images[0]?.flow
  return [...props.targets].sort((a, b) => Number(b === own) - Number(a === own))
})
const kept = computed(() => (refused.value ?? []).filter((one) => one.refusal === null))
const dropped = computed(() => (refused.value ?? []).length - kept.value.length)

function rows(): HTMLElement[] {
  return [...(dialog.value?.querySelectorAll<HTMLElement>('[data-target]') ?? [])]
}
const at = () => rows().indexOf(document.activeElement as HTMLElement)

function walk(by: number): void {
  const held = rows()
  if (held.length) held[clamp(at() + by, held.length - 1)].focus()
}

/* Review on the first draft written, else the first already waiting; the rest
   wait in the rail. */
function review(target: string, drafts: DraftedImage[]): void {
  const first = drafts.find((one) => one.draft !== null) ?? drafts[0]
  void router.push({
    name: 'review',
    params: { collection: props.collection, digest: first.digest, flow: target },
  })
}

async function write(target: string, images: ImageRef[]): Promise<void> {
  if (writing.value || !images.length) return
  writing.value = true
  chosen.value = target
  failure.value = null
  try {
    const answer = await draft(props.collection, target, images)
    if ('images' in answer) {
      refused.value = answer.images
      return
    }
    const { drafts } = answer
    if (drafts.some((one) => one.waiting) && drafts.some((one) => one.draft)) answered.value = drafts
    else review(target, drafts)
  } catch (reason) {
    failure.value = (reason as Error).message
  } finally {
    writing.value = false
  }
}

function deselect(): void {
  const images = kept.value.map(({ refusal: _, ...image }) => image)
  refused.value = null
  if (chosen.value) void write(chosen.value, images)
}

useKeys('overlay', [
  { id: 'cancel', keys: plain('Escape'), label: 'close', run: () => emit('close') },
  { id: 'down', keys: plain('KeyJ', 'ArrowDown'), label: 'next flow', run: () => walk(1) },
  { id: 'up', keys: plain('KeyK', 'ArrowUp'), label: 'previous flow', run: () => walk(-1) },
  {
    id: 'draft',
    keys: plain('Enter'),
    label: 'draft and review',
    run: () => void write(rowsFor.value[at()], props.images),
    when: () => !refused.value && !answered.value && at() >= 0,
  },
  {
    id: 'deselect',
    keys: [shifted('Enter')],
    label: 'deselect the refused and draft',
    run: deselect,
    when: () => refused.value !== null && kept.value.length > 0,
  },
  {
    id: 'review',
    keys: plain('Enter'),
    label: 'review',
    run: () => answered.value && chosen.value && review(chosen.value, answered.value),
    when: () => answered.value !== null,
  },
])
</script>

<template>
  <dialog
    ref="dialog"
    class="render-dialog"
    aria-label="Draft from this"
    data-draft-dialog
    @cancel.prevent
  >
    <header class="render-dialog__head">
      <span class="section-label">Draft · {{ collection }}</span>
      <h2 class="render-dialog__title">{{ title }}</h2>
    </header>
    <p v-if="failure" class="render-dialog__refusal">
      <span class="refusal__mark" />{{ failure }}
    </p>
    <template v-if="refused || answered">
      <p
        v-for="one in refused ?? answered ?? []"
        :key="imageKey(one)"
        class="render-dialog__flow mono"
      >
        <span class="render-dialog__name">{{ one.flow }}</span>
        {{ one.digest }} · v{{ one.version }} · seed {{ one.seed }}
        <span v-if="'waiting' in one && one.waiting" data-waiting>· already waiting</span>
        <span
          v-if="'refusal' in one && one.refusal"
          class="render-dialog__refusal"
          data-refused
          ><span class="refusal__mark" />{{ one.refusal }}</span
        >
      </p>
    </template>
    <div v-else class="render-dialog__targets">
      <button
        v-for="target in rowsFor"
        :key="target"
        class="btn btn-secondary render-dialog__target mono"
        type="button"
        data-target
        :data-revise="revises(target) || undefined"
        :disabled="writing"
        @click="write(target, images)"
      >
        <span class="render-dialog__name">{{ target }}</span>
        <span v-if="revises(target)">revise</span>
      </button>
    </div>
    <footer class="render-dialog__actions">
      <button class="btn btn-secondary" type="button" @click="emit('close')">
        Close<KeyHint command="cancel" />
      </button>
      <button
        v-if="refused && kept.length"
        class="btn btn-secondary"
        type="button"
        data-deselect
        @click="deselect"
      >
        Deselect those {{ dropped }} and draft {{ kept.length }}<KeyHint command="deselect" />
      </button>
      <button
        v-else-if="answered && chosen"
        class="btn btn-primary"
        type="button"
        @click="review(chosen, answered)"
      >
        Review<KeyHint command="review" />
      </button>
    </footer>
  </dialog>
</template>
