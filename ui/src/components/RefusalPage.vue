<script setup lang="ts">
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
        <RouterLink to="/">Back to the library ⌥0</RouterLink>
      </p>
    </div>
  </section>
</template>
