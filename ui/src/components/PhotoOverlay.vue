<script setup lang="ts">
import { computed, ref } from 'vue'
import { paragraphsOf, wordsOf } from '../caption'

/* A lens over the review screen, not a step in it. Nothing here can change the
   sheet, so leaving is never a decision -- esc, a click anywhere, or the ×.

   **This is the one place the `.lighten` blend is not applied.** Everywhere else
   a photograph goes through it so dark values fall away into the page; here the
   photograph is what colour is being judged on, so it is shown as it is, on a
   ground one shade below the app's.

   Frame delta 4: the caption shows paragraphs only. The design tinted the phrase
   a field mapped from, and there is nothing on disk to tint. */
const props = defineProps<{
  id: string
  width: number
  height: number
  photo: string
  caption: string | null
}>()

defineEmits<{ close: [] }>()

const actual = ref(false)

/* Stated, because a judgement made at 72% is not the same judgement. */
const available = 860
const percent = computed(() => Math.round((available / props.height) * 100))

const paragraphs = computed(() => paragraphsOf(props.caption))

const words = computed(() => wordsOf(props.caption))
</script>

<template>
  <Teleport to="body">
    <div class="overlay" @click.self="$emit('close')">
      <figure class="overlay__figure" @click.stop>
        <img
          class="overlay__photo"
          :class="{ 'overlay__photo--actual': actual }"
          :src="photo"
          :alt="id"
        />
        <figcaption class="overlay__meta mono">
          <div>{{ id }}</div>
          <div>
            {{ width }} × {{ height }} ·
            {{ actual ? '1:1 pixels' : `fit to height (${percent}%)` }}
          </div>
        </figcaption>
      </figure>

      <div class="overlay__side" @click.stop>
        <div class="overlay__controls">
          <button
            class="btn"
            :class="actual ? 'btn-secondary' : 'btn-primary'"
            type="button"
            @click="actual = false"
          >
            Fit
          </button>
          <button
            class="btn"
            :class="actual ? 'btn-primary' : 'btn-secondary'"
            type="button"
            @click="actual = true"
          >
            1:1 pixels
          </button>
          <span class="overlay__exit mono">esc · ⌥f · click anywhere</span>
          <button class="btn btn-secondary btn-icon" type="button" @click="$emit('close')">
            ×
          </button>
        </div>

        <div class="source__head">
          <span class="kicker">② caption</span>
          <span class="source__meta mono">{{ words }} words</span>
        </div>
        <div class="overlay__caption">
          <p v-for="(paragraph, index) in paragraphs" :key="index">{{ paragraph }}</p>
        </div>

        <footer class="overlay__foot mono">
          <div>
            Editing is suspended while the photo is open — the sheet is behind this,
            untouched.
          </div>
          <div>← → move through the batch without closing</div>
        </footer>
      </div>
    </div>
  </Teleport>
</template>
