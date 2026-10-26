<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { revise } from '../api'
import { useKeys } from '../composables/useKeys'
import { modded, plain, shifted } from '../stores/keys'
import type { RefusedImage, RevisedDraft, RevisedImage } from '../types'
import KeyHint from './KeyHint.vue'

/* The Revise confirm (design spec J5·3): each image, the version it copies and
   the seed it prefills. All or nothing: a refusal lists every image, and offers
   to deselect the refused; it has no primary button then. An image whose flow
   holds a waiting draft is left out: alone, Review opens on that draft; beside
   written ones, the confirm names it `already waiting` before Review. */
const props = defineProps<{ batch: string; images: RevisedImage[] }>()
const emit = defineEmits<{ close: [] }>()
const router = useRouter()
const refused = ref<RefusedImage[] | null>(null)
const failure = ref<string | null>(null)
const writing = ref(false)
/* The answer of a selection some of whose images were already waiting. */
const answered = ref<RevisedDraft[] | null>(null)

const kept = computed(() => (refused.value ?? []).filter((one) => one.refusal === null))
const dropped = computed(() => (refused.value ?? []).length - kept.value.length)
const plural = (count: number, word: string) => `${count} ${word}${count === 1 ? '' : 's'}`
const key = (one: RevisedImage) => `${one.digest}|${one.flow}|${one.version}|${one.seed}`
const waits = (one: RevisedImage) =>
  answered.value?.some((held) => held.waiting !== null && key(held) === key(one)) ?? false

/* Review on the first draft written, else the first already waiting; the rest
   wait in the rail. */
function review(drafts: RevisedDraft[]): void {
  const first = drafts.find((one) => one.draft !== null) ?? drafts[0]
  void router.push({
    name: 'review',
    params: { batch: props.batch, digest: first.digest, flow: first.flow },
  })
}

async function confirm(images: RevisedImage[]): Promise<void> {
  if (writing.value || !images.length) return
  writing.value = true
  try {
    const answer = await revise(props.batch, images)
    if ('images' in answer) {
      refused.value = answer.images
      return
    }
    const waiting = answer.drafts.some((one) => one.waiting !== null)
    if (waiting && answer.drafts.some((one) => one.draft !== null)) answered.value = answer.drafts
    else review(answer.drafts)
  } catch (reason) {
    failure.value = (reason as Error).message
  } finally {
    writing.value = false
  }
}

function deselect(): void {
  const images = kept.value.map(({ refusal: _, ...image }) => image)
  refused.value = null
  void confirm(images)
}

useKeys('overlay', [
  { id: 'cancel', keys: plain('Escape'), label: 'cancel', run: () => emit('close') },
  {
    id: 'deselect',
    keys: [shifted('Enter')],
    label: 'deselect the refused and revise',
    run: deselect,
    when: () => refused.value !== null && kept.value.length > 0,
  },
  {
    id: 'confirm',
    keys: [modded('Enter')],
    label: 'write and review',
    run: () => void confirm(props.images),
    when: () => !refused.value && !answered.value,
  },
  {
    id: 'review',
    keys: [modded('Enter')],
    label: 'review',
    run: () => answered.value && review(answered.value),
    when: () => answered.value !== null,
  },
])
</script>

<template>
  <div class="scrim" @click.self="emit('close')">
    <section class="render-dialog" role="dialog" aria-label="Revise" data-revise-confirm>
      <header class="render-dialog__head">
        <span class="section-label">Revise · {{ batch }}</span>
        <h2 class="render-dialog__title">Revise {{ plural(images.length, 'image') }}</h2>
      </header>
      <p v-if="failure" class="render-dialog__refusal">
        <span class="refusal__mark" />{{ failure }}
      </p>
      <p
        v-for="one in refused ?? images.map((image) => ({ ...image, refusal: null }))"
        :key="key(one)"
        class="render-dialog__flow mono"
      >
        <span class="render-dialog__name">{{ one.flow }}</span>
        {{ one.digest }} · copies v{{ one.version }} · prefills seed {{ one.seed }}
        <span v-if="waits(one)" data-waiting>· already waiting</span>
        <span v-if="one.refusal" class="render-dialog__refusal" data-refused
          ><span class="refusal__mark" />{{ one.refusal }}</span
        >
      </p>
      <footer class="render-dialog__actions">
        <button class="btn btn-secondary" type="button" @click="emit('close')">
          Cancel<KeyHint command="cancel" />
        </button>
        <button
          v-if="refused && kept.length"
          class="btn btn-secondary"
          type="button"
          data-deselect
          @click="deselect"
        >
          Deselect those {{ dropped }} and revise {{ kept.length }}<KeyHint command="deselect" />
        </button>
        <button
          v-else-if="answered"
          class="btn btn-primary"
          type="button"
          @click="review(answered)"
        >
          Review<KeyHint command="review" />
        </button>
        <button
          v-else-if="!refused"
          class="btn btn-primary"
          type="button"
          data-confirm
          :disabled="writing"
          @click="confirm(images)"
        >
          Write {{ plural(images.length, 'draft') }} and review<KeyHint command="confirm" />
        </button>
      </footer>
    </section>
  </div>
</template>
