<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { fewer, more, renders as read, set, slots, type Slot } from '../slots'
import type { Renders } from '../types'

/* ④ Renders: one slot per image, each a seed or random (design spec J3). The
   slots are held here, so a seed typed into the third slot stays there while
   the draft lists it first; they are read again only when the draft moves. */
const props = defineProps<{ renders: Renders; readonly: boolean }>()
const emit = defineEmits<{ change: [renders: Renders] }>()

const held = ref<Slot[]>(slots(props.renders))
/* A refused entry, by slot: the slot keeps what was typed and says why. */
const refused = ref<Record<number, string>>({})
const panel = ref<HTMLElement | null>(null)

function same(one: Renders, other: Renders): boolean {
  return (
    one.count === other.count &&
    one.seeds.length === other.seeds.length &&
    one.seeds.every((seed, index) => seed === other.seeds[index])
  )
}

watch(
  () => props.renders,
  (next) => {
    if (same(read(held.value), next)) return
    held.value = slots(next)
    refused.value = {}
  },
)

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

/* `j` `k` or ↓ ↑ walk the count and the slots; a slot takes digits alone, so
   the letters never type into one. */
function walk(event: KeyboardEvent): void {
  if (event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return
  const step = { j: 1, ArrowDown: 1, k: -1, ArrowUp: -1 }[event.key]
  if (!step || !panel.value) return
  const stops = [
    panel.value.querySelector<HTMLElement>('[data-renders-count]'),
    ...panel.value.querySelectorAll<HTMLElement>('[data-slot]'),
  ].filter((one): one is HTMLElement => one !== null)
  const at = stops.findIndex((one) => one.contains(document.activeElement))
  const next = stops[Math.min(Math.max(at + step, 0), stops.length - 1)]
  event.preventDefault()
  event.stopPropagation()
  next?.focus()
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
  <section ref="panel" class="renders-block" tabindex="-1" @keydown="walk">
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
