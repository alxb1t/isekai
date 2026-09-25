<script setup lang="ts">
import { computed } from 'vue'
import type { ApprovedSheet } from '../types'

/* The closing screen. It states the artifact and gives no order: the operator
   wrote the CLI, and they do not need to be told to run `generate`.

   Frame delta 9: the design's `runs/2026-09-17/` and `.sheet.json` are invented.
   The real paths are `<run>/<flow>/review/` and `NNN.approved.json`. */
const props = defineProps<{
  flow: string
  sheets: ApprovedSheet[]
  total: number
}>()

defineEmits<{ again: [] }>()

const over = computed(() => props.sheets.filter((s) => s.tokens > s.window))
</script>

<template>
  <section class="manifest">
    <h3 class="manifest__title">{{ sheets.length }} of {{ total }} approved</h3>
    <p class="manifest__where mono">
      sheets written to &lt;run&gt;/{{ flow }}/review/
    </p>

    <table class="table manifest__table">
      <thead>
        <tr>
          <th>sheet</th>
          <th class="manifest__right">tokens</th>
          <th class="manifest__right">approved</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="sheet in sheets" :key="sheet.id">
          <td class="mono">{{ sheet.id }}/{{ sheet.name }}</td>
          <td class="mono manifest__right" :class="{ 'manifest__over': sheet.tokens > sheet.window }">
            {{ sheet.tokens }}
          </td>
          <td class="mono manifest__right">{{ sheet.at }}</td>
        </tr>
      </tbody>
    </table>

    <template v-if="over.length">
      <p class="manifest__note">
        {{ over.length === 1 ? 'One sheet is' : `${over.length} sheets are` }} over the
        {{ over[0].window }}-token budget:
        <span class="mono">{{ over.map((s) => `${s.id} at ${s.tokens}`).join(', ') }}</span
        >.
      </p>
      <p class="manifest__aside">
        Approved deliberately. Stated here so it is not a surprise after the render.
      </p>
    </template>

    <footer class="manifest__foot">
      <button class="btn btn-secondary" type="button" @click="$emit('again')">
        Review again
      </button>
      <span class="manifest__aside">The server keeps running until you stop the CLI.</span>
    </footer>
  </section>
</template>
