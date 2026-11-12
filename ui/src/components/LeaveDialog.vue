<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { Ask } from '../leave'

/* *Leave this stage?* asks before a stage with a lone point is left: the point and the image
   that lacks its match, the pairs that stand and, for stage 1, when they were saved. *Stay*
   holds the focus and the native dialog's own `esc` closes it as *Stay*; *Leave* drops the
   lone point alone. It declares no command. */
defineProps<{ ask: Ask }>()
const emit = defineEmits<{ stay: []; leave: [] }>()
const dialog = ref<HTMLDialogElement | null>(null)
const stay = ref<HTMLButtonElement | null>(null)

onMounted(() => {
  dialog.value?.showModal()
  stay.value?.focus()
})
</script>

<template>
  <dialog
    ref="dialog"
    class="render-dialog leave-dialog"
    aria-label="Leave this stage?"
    data-leave-dialog
    @close="emit('stay')"
  >
    <header class="render-dialog__head">
      <h2 class="render-dialog__title">Leave this stage?</h2>
    </header>
    <p class="leave-dialog__point" data-leave-point>{{ ask.title }}</p>
    <p class="leave-dialog__standing mono" data-leave-standing>
      {{ ask.standing }}<template v-if="ask.saved"> · {{ ask.saved }}</template>
    </p>
    <footer class="render-dialog__actions">
      <button ref="stay" class="btn btn-secondary" type="button" data-leave-stay @click="emit('stay')">
        Stay
      </button>
      <button class="btn btn-secondary" type="button" data-leave-leave @click="emit('leave')">
        Leave
      </button>
    </footer>
  </dialog>
</template>
