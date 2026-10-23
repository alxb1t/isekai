<script setup lang="ts">
import { computed } from 'vue'
import { useKeyStore } from '../stores/keys'

/* A button's key, drawn from the command it runs; nothing while none declares it. */
const props = defineProps<{ command: string }>()
const keys = useKeyStore()
const text = computed(() => keys.hint(props.command))
</script>

<template>
  <span v-if="text" class="appbar__key">{{ text }}</span>
</template>
