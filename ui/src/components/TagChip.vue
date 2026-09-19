<script setup lang="ts">
/* A committed tag. Bordered, with an ×; in-flight text is bare with a caret and
   never looks like this. Committed and in-flight must never be confusable. */
defineProps<{ tag: string; readonly?: boolean; selected?: boolean }>()
defineEmits<{ remove: [] }>()
</script>

<template>
  <span
    class="tag tag-outline chip"
    :style="
      selected
        ? { background: 'var(--color-accent-900)', color: 'var(--color-accent-100)' }
        : undefined
    "
  >
    {{ tag }}
    <button v-if="!readonly" class="chip__x" type="button" @click="$emit('remove')">
      ×
    </button>
  </span>
</template>
