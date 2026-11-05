<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useKeys } from '../composables/useKeys'
import { useHeldFocus } from '../composables/useHeldFocus'
import { clamp } from '../grid'
import { plain } from '../stores/keys'
import { THEMES, type Theme, chooser } from '../themes'
import KeyHint from './KeyHint.vue'

/* The theme dialog (D48): a row per theme, each drawn in its own tokens, the
   shown one focused. `j` `k` move and preview, `↵` keeps, `Esc` and the
   backdrop restore the theme it opened on. */
const emit = defineEmits<{ close: [] }>()
// `localStorage` is read inside `setItem`, where `keep` catches a browser that refuses it.
const choice = chooser(document.documentElement, {
  setItem: (key, value) => localStorage.setItem(key, value),
})
const dialog = ref<HTMLDialogElement | null>(null)

useHeldFocus(dialog, restore)
onMounted(() => {
  dialog.value?.showModal()
  rows()[THEMES.findIndex((one) => one.id === choice.opened)]?.focus()
})

function rows(): HTMLElement[] {
  return [...(dialog.value?.querySelectorAll<HTMLElement>('[data-theme-row]') ?? [])]
}
const at = () => rows().indexOf(document.activeElement as HTMLElement)

function walk(by: number): void {
  const held = rows()
  if (!held.length) return
  const to = clamp(at() + by, held.length - 1)
  held[to].focus()
  choice.preview(THEMES[to].id)
}

function keep(theme: Theme): void {
  choice.keep(theme)
  emit('close')
}

function restore(): void {
  choice.restore()
  emit('close')
}

useKeys('overlay', [
  { id: 'cancel', keys: plain('Escape'), label: 'close', run: restore },
  { id: 'down', keys: plain('KeyJ', 'ArrowDown'), label: 'next theme', run: () => walk(1) },
  { id: 'up', keys: plain('KeyK', 'ArrowUp'), label: 'previous theme', run: () => walk(-1) },
  {
    id: 'keep',
    keys: plain('Enter'),
    label: 'keep the theme',
    run: () => keep(THEMES[at()].id),
    when: () => at() >= 0,
  },
])
</script>

<template>
  <dialog
    ref="dialog"
    class="render-dialog"
    aria-label="Theme"
    data-theme-dialog
    @cancel.prevent
  >
    <header class="render-dialog__head">
      <h2 class="render-dialog__title">Theme</h2>
    </header>
    <div class="render-dialog__targets">
      <button
        v-for="theme in THEMES"
        :key="theme.id"
        class="theme-dialog__row"
        type="button"
        :data-theme="theme.id"
        data-theme-row
        @click="keep(theme.id)"
      >
        {{ theme.name }}
      </button>
    </div>
    <footer class="render-dialog__actions">
      <button class="btn btn-secondary" type="button" @click="restore">
        Close<KeyHint command="cancel" />
      </button>
    </footer>
  </dialog>
</template>
