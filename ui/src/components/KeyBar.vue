<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useKeyStore } from '../stores/keys'

/* The screen's keys under it, read from their declarations. */
const { bar } = storeToRefs(useKeyStore())
</script>

<template>
  <p v-if="bar.length" class="keybar mono" data-key-bar>
    <template v-for="(one, index) in bar" :key="index"
      >{{ index ? ' · ' : '' }}{{ one.keys }} {{ one.label }}</template
    >
  </p>
</template>
