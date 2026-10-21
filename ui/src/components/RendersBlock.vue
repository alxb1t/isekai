<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Renders } from '../types'
import TagChip from './TagChip.vue'

/* ④ Renders: how many images the approval renders, and the seeds it renders
   first (design spec J3·2). Count never falls below the seeds listed; the rest
   of Count is drawn. Both are approved with the sheet. */
const props = defineProps<{ renders: Renders; readonly: boolean }>()
const emit = defineEmits<{ change: [renders: Renders] }>()

const typed = ref('')
const floor = computed(() => Math.max(1, props.renders.seeds.length))

function setCount(count: number): void {
  emit('change', { count: Math.max(count, floor.value), seeds: props.renders.seeds })
}

function addSeed(): void {
  const seed = typed.value.trim()
  if (!/^\d+$/.test(seed) || props.renders.seeds.includes(seed)) return
  const seeds = [...props.renders.seeds, seed]
  emit('change', { count: Math.max(props.renders.count, seeds.length), seeds })
  typed.value = ''
}

function removeSeed(index: number): void {
  const seeds = props.renders.seeds.filter((_, at) => at !== index)
  emit('change', { count: props.renders.count, seeds })
}

const draws = computed(() => {
  const { count, seeds } = props.renders
  const images = `${count} image${count === 1 ? '' : 's'}`
  const drawn = count - seeds.length
  if (seeds.length === 0) return `${images} · random seed${count === 1 ? '' : 's'}`
  const listed = `seed${seeds.length === 1 ? '' : 's'} ${seeds.join(', ')}`
  return drawn > 0 ? `${images} · ${listed} + ${drawn} random` : `${images} · ${listed}`
})
</script>

<template>
  <section class="renders-block">
    <div class="renders-block__row">
      <span class="section-label">④ Renders</span>
      <span class="renders-block__label">count</span>
      <span class="renders-block__count mono">
        <button
          v-if="!readonly"
          class="btn btn-secondary renders-block__step"
          type="button"
          aria-label="fewer"
          :disabled="renders.count <= floor"
          @click="setCount(renders.count - 1)"
        >
          −
        </button>
        <span class="renders-block__value" data-renders-count>{{ renders.count }}</span>
        <button
          v-if="!readonly"
          class="btn btn-secondary renders-block__step"
          type="button"
          aria-label="more"
          @click="setCount(renders.count + 1)"
        >
          +
        </button>
      </span>
      <span class="renders-block__label">seeds</span>
      <span class="renders-block__seeds">
        <TagChip
          v-for="(seed, index) in renders.seeds"
          :key="seed"
          class="mono"
          :tag="seed"
          :readonly="readonly"
          @remove="removeSeed(index)"
        />
        <input
          v-if="!readonly"
          v-model="typed"
          class="input mono renders-block__seed"
          inputmode="numeric"
          placeholder="+ seed"
          aria-label="add a seed"
          @keydown.enter.prevent="addSeed"
          @keydown.esc="typed = ''"
        />
      </span>
    </div>
    <p class="section-label renders-block__draws">The next render draws {{ draws }}</p>
  </section>
</template>
