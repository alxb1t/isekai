<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useKeys } from '../composables/useKeys'
import { plain, shifted, useKeyStore } from '../stores/keys'
import KeyHint from './KeyHint.vue'

/* Every key this screen answers, everywhere's first, read from their declarations. */
const emit = defineEmits<{ close: [] }>()
const { listed } = storeToRefs(useKeyStore())

useKeys('overlay', [
  {
    id: 'close',
    keys: [...plain('Escape'), shifted('Slash')],
    label: 'close',
    run: () => emit('close'),
  },
])
</script>

<template>
  <Teleport to="body">
    <div class="overlay" data-key-list @click.self="emit('close')">
      <div class="overlay__side" @click.stop>
        <div class="overlay__controls">
          <span class="kicker">keys</span>
          <span class="overlay__exit mono"><KeyHint command="close" /> · click anywhere</span>
        </div>
        <dl class="keylist mono">
          <template v-for="(one, index) in listed" :key="index">
            <dt class="keylist__keys">{{ one.keys }}</dt>
            <dd class="keylist__label">{{ one.label }}</dd>
          </template>
        </dl>
      </div>
    </div>
  </Teleport>
</template>
