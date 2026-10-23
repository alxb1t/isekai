<script setup lang="ts">
import KeyHint from './KeyHint.vue'

/* A screen that cannot be drawn: the server's refusal verbatim, then the way
   back to the library. The text is the CLI's; the page invents none of it. */
defineProps<{ refusal: string }>()
</script>

<template>
  <section class="refusal">
    <span class="refusal__mark" />
    <div>
      <p class="refusal__reason">{{ refusal }}</p>
      <p class="refusal__fix">
        <RouterLink to="/">Back to the library<KeyHint command="library" /></RouterLink>
      </p>
    </div>
  </section>
</template>
