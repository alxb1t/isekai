<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { revise } from '../api'
import { reviewQueue } from '../composables/useQueue'
import type { RevisedImage } from '../types'

/* The Revise confirm (design spec J5·3): each image, the version it copies and
   the seed it prefills. All or nothing: a refusal lists every image, and offers
   to deselect the refused; it has no primary button then. */
const props = defineProps<{ batch: string; images: RevisedImage[] }>()
const emit = defineEmits<{ close: [] }>()
const router = useRouter()
const refused = ref<(RevisedImage & { refusal: string | null })[] | null>(null)
const failure = ref<string | null>(null)
const writing = ref(false)

const kept = computed(() => (refused.value ?? []).filter((one) => one.refusal === null))
const dropped = computed(() => (refused.value ?? []).length - kept.value.length)
const plural = (count: number, word: string) => `${count} ${word}${count === 1 ? '' : 's'}`

async function confirm(images: RevisedImage[]): Promise<void> {
  if (writing.value || !images.length) return
  writing.value = true
  try {
    const answer = await revise(props.batch, images)
    if ('images' in answer) {
      refused.value = answer.images
      return
    }
    const [first, ...rest] = answer.drafts
    void router.push({
      name: 'review',
      params: { batch: props.batch, digest: first.digest, flow: first.flow },
      query: { queue: reviewQueue(rest) },
    })
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

function onKey(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault()
    emit('close')
  } else if (event.altKey && event.key === 'Enter' && refused.value && kept.value.length) {
    event.preventDefault()
    deselect()
  } else if ((event.metaKey || event.ctrlKey) && event.key === 'Enter' && !refused.value) {
    event.preventDefault()
    void confirm(props.images)
  }
}

onMounted(() => window.addEventListener('keydown', onKey))
onUnmounted(() => window.removeEventListener('keydown', onKey))
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
        :key="`${one.digest}|${one.flow}|${one.version}|${one.seed}`"
        class="render-dialog__flow mono"
      >
        <span class="render-dialog__name">{{ one.flow }}</span>
        {{ one.digest }} · copies v{{ one.version }} · prefills seed {{ one.seed }}
        <span v-if="one.refusal" class="render-dialog__refusal" data-refused
          ><span class="refusal__mark" />{{ one.refusal }}</span
        >
      </p>
      <footer class="render-dialog__actions">
        <button class="btn btn-secondary" type="button" @click="emit('close')">
          Cancel<span class="appbar__key">esc</span>
        </button>
        <button
          v-if="refused && kept.length"
          class="btn btn-secondary"
          type="button"
          data-deselect
          @click="deselect"
        >
          Deselect those {{ dropped }} and revise {{ kept.length }}<span class="appbar__key"
            >⌥↵</span
          >
        </button>
        <button
          v-else-if="!refused"
          class="btn btn-primary"
          type="button"
          data-confirm
          :disabled="writing"
          @click="confirm(images)"
        >
          Write {{ plural(images.length, 'draft') }} and review<span class="appbar__key"
            >⌘↵</span
          >
        </button>
      </footer>
    </section>
  </div>
</template>
