<script setup lang="ts">
import { computed, ref } from 'vue'
import { fewer, more, renders as read, set, slots, type Slot } from '../slots'
import type { Renders } from '../types'

/* ④ Renders: one slot per image, each a seed or random (design spec J3). The
   slots are held here, so a seed typed into the third slot stays there while
   the draft lists it first. Review mounts this afresh for each read of the
   sheet, so the draft never moves under it. */
const props = defineProps<{ renders: Renders; readonly: boolean }>()
const emit = defineEmits<{ change: [renders: Renders] }>()

const held = ref<Slot[]>(slots(props.renders))
/* A refused entry, by slot: the slot keeps what was typed and says why. */
const refused = ref<Record<number, string>>({})

function change(next: Slot[]): void {
  held.value = next
  emit('change', read(next))
}

function type(at: number, typed: string): void {
  const next = set(held.value, at, typed)
  if (typeof next === 'string') {
    refused.value = { ...refused.value, [at]: next }
    return
  }
  const { [at]: _, ...rest } = refused.value
  refused.value = rest
  change(next)
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
  <section class="renders-block" tabindex="-1">
    <span class="section-label">④ Renders</span>
    <div class="renders-block__count mono">
      <span class="renders-block__label">images</span>
      <button
        v-if="!readonly"
        class="btn btn-secondary renders-block__step"
        type="button"
        aria-label="fewer"
        data-renders-count
        :disabled="held.length <= 1"
        @click="change(fewer(held))"
      >
        −
      </button>
      <span class="renders-block__value" data-renders-value>{{ held.length }}</span>
      <button
        v-if="!readonly"
        class="btn btn-secondary renders-block__step"
        type="button"
        aria-label="more"
        @click="change(more(held))"
      >
        +
      </button>
    </div>
    <ol class="renders-block__slots">
      <li v-for="(slot, at) in held" :key="at" class="renders-block__slot">
        <span class="renders-block__label mono">{{ at + 1 }}</span>
        <span v-if="readonly" class="mono">{{ slot ?? 'random' }}</span>
        <input
          v-else
          class="input mono renders-block__seed"
          inputmode="numeric"
          placeholder="random"
          :aria-label="`seed of image ${at + 1}`"
          :value="slot ?? ''"
          data-slot
          @input="type(at, ($event.target as HTMLInputElement).value)"
        />
        <span v-if="refused[at]" class="renders-block__refusal mono"
          ><span class="refusal__mark" />{{ refused[at] }}</span
        >
      </li>
    </ol>
    <p class="section-label renders-block__draws">The next render draws {{ draws }}</p>
  </section>
</template>
