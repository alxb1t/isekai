<script setup lang="ts">
import { computed } from 'vue'
import { chainRows } from '../bakes'
import type { Bake } from '../types'

/* A render's chain (design spec J5·2): the render first, then each bake of its
   seed by number, one level further in for each bake it descends through. The
   shown row is framed; a baked row opens its large view, a queued or damaged
   one none. `shown` is the bake's number, or null on the render's own view. */
const props = defineProps<{
  bakes: readonly Bake[]
  shown: number | null
  params: { collection: string; digest: string; flow: string; version: string; seed: string }
}>()

const rows = computed(() => chainRows(props.bakes))

const clock = (at: number) => new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })
</script>

<template>
  <ol class="chain" aria-label="the render and its bakes" data-chain>
    <li class="chain__row" :class="{ 'chain__row--shown': shown === null }" :aria-current="shown === null">
      <span v-if="shown === null" class="chain__label mono">the render · seed {{ params.seed }}</span>
      <RouterLink v-else class="chain__label chain__link mono" :to="{ name: 'render', params }"
        >the render · seed {{ params.seed }}</RouterLink
      >
    </li>
    <li
      v-for="row in rows"
      :key="row.k"
      class="chain__row"
      :class="{ 'chain__row--shown': shown === row.k }"
      :style="{ '--depth': row.depth + 1 }"
      :aria-current="shown === row.k"
      :data-bake="row.k"
    >
      <span class="chain__step" aria-hidden="true">↳</span>
      <RouterLink
        v-if="row.state === 'baked'"
        class="chain__label chain__link mono"
        :to="{ name: 'bake', params: { ...params, k: String(row.k) } }"
        >edit {{ row.k }} · baked {{ clock(row.baked_at ?? 0) }}</RouterLink
      >
      <span v-else-if="row.state === 'queued'" class="chain__label mono"
        >edit {{ row.k }} · queued, waits for the next session</span
      >
      <span v-else class="chain__label mono" :title="row.reason ?? ''"
        >edit {{ row.k }} · damaged<template v-if="row.reason"> · {{ row.reason }}</template></span
      >
    </li>
  </ol>
</template>
