<script setup lang="ts">
import { computed, ref } from 'vue'
import CaptionPanel from './CaptionPanel.vue'
import PhotoFrame from './PhotoFrame.vue'
import TagChip from './TagChip.vue'
import { grouped } from '../caption'
import type { OfferedTag, ScoredTag } from '../types'

/* Owns the 492/620px width rule: one rule, two shapes, no second layout. The
   photo always fills its column's width and the form column absorbs the
   difference, so a wide photograph never letterboxes. */
const props = defineProps<{
  id: string
  width: number
  height: number
  photo: string
  caption: string | null
  /* Both null where the artifact is absent, and an absent list draws nothing --
     no panel, no message. Three ways it is legitimately missing (a run
     captioned before v0.20, a flow with no hosted block, a failed tagger) and
     none of them may interrupt a review; a line explaining an absence the
     operator caused is chrome on the busiest pane in the surface
     (design.md D20). */
  wd14?: ScoredTag[] | null
  tags?: OfferedTag[] | null
  loading?: boolean
}>()

defineEmits<{ open: [] }>()

const landscape = computed(() => props.width > props.height)

/* WD14 first, JoyCaption second: the order the pipeline produces them in, and
   it puts the usable list nearer the prose. The local tagger's tags are in the
   vocabulary by construction -- the CSV it is scored against IS the vocabulary
   -- while roughly three-quarters of the hosted list cannot be committed at all
   (design.md D1). */
const scored = computed(() => props.wd14 ?? [])

const offered = computed(() => props.tags ?? [])

/* Two digits, because the panel's job is to make `black hair 0.31` sitting
   under `brown hair 0.91` self-refuting, and a third digit adds nothing to that
   comparison. */
const confidence = (value: number): string => value.toFixed(2)

/* `ref="source"` on a component hands back the component, not its element, and
   `Alt+→` has to focus and scroll the real one. */
const element = ref<HTMLElement | null>(null)

defineExpose({
  focus: () => element.value?.focus(),
  scrollBy: (options: ScrollToOptions) => element.value?.scrollBy(options),
})
</script>

<template>
  <aside
    class="source"
    :class="landscape ? 'source--landscape' : 'source--portrait'"
    tabindex="0"
    ref="element"
  >
    <div class="source__head">
      <span class="kicker">① photograph</span>
      <span class="source__meta mono">
        {{ id }} · {{ width }}×{{ height }} ·
        {{ loading ? 'reading…' : 'click to fill window' }}
      </span>
    </div>
    <PhotoFrame
      :src="photo"
      :alt="id"
      :loading="loading"
      :ratio="`${width} / ${height}`"
      @open="$emit('open')"
    />
    <CaptionPanel :prose="caption" :loading="loading" />
    <section v-if="scored.length" class="caption">
      <div class="source__head">
        <span class="kicker">scored tags</span>
        <!-- The count, not the floor. `FLOOR` lives in `boundary/wd14.py` and
             its comment says to move it the day a flow wants a different one;
             printing the number here would have the panel state a threshold no
             artifact was filtered at, with nothing failing. -->
        <span class="source__meta mono">{{ scored.length }} above the floor</span>
      </div>
      <!-- `row__tags` is the sheet row's own chip layout, reused rather than
           restated: D21's constraint is no new component, colour, spacing or
           type step outside what v0.18 shipped, and a second flex-wrap rule
           five pixels apart is exactly the drift it forbids. -->
      <div class="row__tags">
        <TagChip
          v-for="one in scored"
          :key="one.tag"
          :tag="`${one.tag} ${confidence(one.confidence)}`"
          readonly
        />
      </div>
    </section>
    <section v-if="offered.length" class="caption">
      <div class="source__head">
        <span class="kicker">offered tags</span>
        <span class="source__meta mono">
          {{ offered.filter((one) => one.in_vocabulary).length }} of
          {{ offered.length }} in vocabulary
        </span>
      </div>
      <div class="row__tags">
        <!-- A chip with no count is a tag the vocabulary does not carry, so it
             cannot be committed to any field. The missing number is the mark:
             it reads as the model's word rather than Danbooru's. -->
        <TagChip
          v-for="one in offered"
          :key="one.tag"
          :tag="one.posts === null ? one.tag : `${one.tag} ${grouped(one.posts)}`"
          readonly
        />
      </div>
    </section>
  </aside>
</template>
