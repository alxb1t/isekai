<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import TagChip from './TagChip.vue'
import type { FieldCandidates } from '../types'

/* A reference, not a step. It answers one question the autocomplete cannot:
   *what does Danbooru call the thing I am looking at*. The autocomplete needs a
   fragment the operator already has, and a fragment that matches nothing commits
   nothing — so not knowing the word is a dead end rather than a bad tag.

   **Read-only.** Clicking a tag does not insert it. Inserting would make a
   reference surface own a target field and commit into it, which is a different
   feature; the operator reads a tag, closes, and types it with the autocomplete
   he already has.

   **Nothing is cut.** A post-count cutoff was measured against the operator's own
   approved sheets and refused — `>10,000` hides ten of the 113 tags he approved,
   and the ones he reaches for are in the tail. The filter is what makes length the
   point rather than the problem.

   It composes `PhotoOverlay`'s ground rather than introducing one: the same
   `Teleport`, the same `.overlay` block below the app header, `.overlay__controls`
   / `.overlay__exit` / `.overlay__foot` for chrome, `.source__head` + `.kicker`
   for section heads, `.row__tags` + `TagChip` for the grid, `.input` for the
   filter and `.drop__posts` for the counts. Not one new component, colour, space
   or type step. */
const props = defineProps<{ candidates: FieldCandidates; field: string | null }>()

defineEmits<{ close: [] }>()

const fragment = ref('')
const box = ref<HTMLInputElement | null>(null)

/* The overlay takes the focus on open, because it owns an input of its own and
   the field it was opened from must stop receiving keys. `ReviewApp` gives the
   field back on close. */
onMounted(() => box.value?.focus())

/* Normalised the way `isekai/shared/vocabulary.py`'s `normalise()` is, so a
   fragment typed here matches what the same fragment matches in the autocomplete:
   Danbooru writes `blue_eyes` and this vocabulary reads `blue eyes`. */
const needle = computed(() =>
  fragment.value.trim().toLowerCase().replace(/[_\s]+/g, ' '),
)

/* Every declared criterion stays in the list, including one the filter empties
   and one the table holds nothing for: a row saying *nothing here* is a fact
   about the vocabulary, and a row that vanished under a fragment would read as
   one the operator had already passed. */
const groups = computed(() =>
  Object.entries(props.candidates.fields).map(([name, tags]) => ({
    name,
    total: tags.length,
    tags: needle.value ? tags.filter((one) => one.tag.includes(needle.value)) : tags,
  })),
)

/* Out of the same pass rather than a second reduce over 3,000 rows: the groups
   are already in hand when this is asked for. */
const shown = computed(() => groups.value.reduce((sum, one) => sum + one.tags.length, 0))
</script>

<template>
  <Teleport to="body">
    <div class="overlay" @click.self="$emit('close')">
      <div class="overlay__side overlay__side--wide" @click.stop>
        <div class="overlay__controls">
          <input
            ref="box"
            v-model="fragment"
            class="input"
            type="text"
            placeholder="filter"
            autocomplete="off"
            spellcheck="false"
          />
          <span class="overlay__exit mono">esc · click anywhere</span>
          <button class="btn btn-secondary btn-icon" type="button" @click="$emit('close')">
            ×
          </button>
        </div>

        <div v-for="group in groups" :key="group.name" class="cheatsheet__group">
          <div class="source__head">
            <span class="kicker">{{ group.name }}</span>
            <span class="drop__posts mono">
              {{ group.tags.length === group.total ? group.total : `${group.tags.length} of ${group.total}` }}
            </span>
          </div>
          <div v-if="group.tags.length" class="row__tags">
            <template v-for="one in group.tags" :key="one.tag">
              <TagChip :tag="one.tag" readonly />
              <span class="drop__posts mono">{{ one.posts }}</span>
            </template>
          </div>
          <div v-else class="cheatsheet__empty mono">nothing here</div>
        </div>

        <footer class="overlay__foot mono">
          <div>
            Reference only — a tag here is not inserted. Read it, close, and type it.
          </div>
          <div>
            {{ shown }} tags shown{{ field ? ` · opened from ${field}` : '' }} · ⌥space
            closes
          </div>
        </footer>
      </div>
    </div>
  </Teleport>
</template>
