<script setup lang="ts">
import { computed, onUnmounted, reactive, ref } from 'vue'
import {
  type Place,
  cancelStaging,
  cutTattoo,
  designAt,
  imageAt,
  keepTattoo,
  openStaging,
  photoUrl,
  removeTattoo,
  saveStageOne,
  stageFile,
  versionOf,
} from '../api'
import { removal } from '../confirm'
import type { Step } from '../stages'
import { useLiveStore } from '../stores/live'
import { card, formLine, refusalField, uploadName } from '../tattoos'
import type { Stage1, TattooList } from '../types'
import ConfirmDialog from './ConfirmDialog.vue'
import CutImage from './CutImage.vue'

/* The placement screen's first step: the render and its photograph, every kept tattoo as a
   card, an upload through the import's staging under a name, and a cut of this render's
   photograph under a name. It shows state and the way forward; a card opens the step its
   state asks, an upload's card offers *not on this photo*, which keeps the tattoo's stage-1
   pairs, and every card offers *Remove*, which asks in a dialog. */
const props = defineProps<{
  place: Place
  version: string
  seed: string
  list: TattooList
  instead: string | null
}>()
const emit = defineEmits<{
  choose: [name: string, step: Step]
  kept: [name: string]
  flagged: []
  removed: [name: string]
}>()

interface Chosen {
  file: File
  upload: string | null
  name: string
  refusal: string | null
  keeping: boolean
}

const renderUrl = computed(() =>
  imageAt({ ...props.place, version: versionOf(props.version), seed: props.seed }),
)
const live = useLiveStore()
const picker = ref<HTMLInputElement | null>(null)
const chosen = ref<Chosen | null>(null)
const staging = ref<string | null>(null)

/* The chosen file as the page's stream reports it: read, converted, refused. */
const reported = computed(() => {
  const upload = chosen.value?.upload
  return upload ? live.files[upload] : undefined
})
const reading = computed(
  () =>
    chosen.value !== null &&
    chosen.value.refusal === null &&
    (reported.value === undefined ||
      reported.value.state === 'waiting' ||
      reported.value.state === 'converting'),
)
/* Where each refusal is shown: beside the name when it asks for another, else on the file. */
const fileRefusal = computed(() => {
  const held = chosen.value
  if (!held) return null
  if (reported.value?.state === 'refused')
    return reported.value.refusal ?? `${held.file.name}: refused`
  return held.refusal !== null && refusalField(held.refusal) === 'file' ? held.refusal : null
})
const nameRefusal = computed(() => {
  const held = chosen.value?.refusal ?? null
  return held !== null && refusalField(held) === 'name' ? held : null
})
/* Keep's reason for being disabled, or null when it is not. */
const keepWait = computed(() => {
  const held = chosen.value
  if (!held) return null
  if (held.keeping) return 'keeping'
  if (reading.value) return 'reading the file'
  if (reported.value?.state === 'refused') return 'the file is refused'
  if (held.name.trim() === '') return 'name the tattoo'
  return null
})

async function dropStaging(): Promise<void> {
  const id = staging.value
  if (id === null) return
  staging.value = null
  live.follow({ staging: null })
  await cancelStaging(id).catch(() => undefined)
}

async function choose(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  await dropStaging()
  const mine = reactive<Chosen>({
    file,
    upload: null,
    name: uploadName(file.name, props.instead),
    refusal: null,
    keeping: false,
  })
  chosen.value = mine
  try {
    const opened = await openStaging()
    staging.value = opened.id
    live.follow({ staging: opened.id })
    mine.upload = (await stageFile(opened.id, file)).upload
  } catch (reason) {
    mine.refusal = (reason as Error).message
  }
}

async function keep(): Promise<void> {
  const held = chosen.value
  const file = reported.value
  if (!held || !file || staging.value === null || keepWait.value !== null) return
  held.refusal = null
  held.keeping = true
  try {
    const made = await keepTattoo(staging.value, file.name ?? file.file, held.name.trim())
    // The server cancelled the staging with the keep.
    staging.value = null
    live.follow({ staging: null })
    chosen.value = null
    emit('kept', made.name)
  } catch (reason) {
    held.refusal = (reason as Error).message
  } finally {
    held.keeping = false
  }
}

async function discard(): Promise<void> {
  chosen.value = null
  await dropStaging()
}

const cutName = ref('')
const cutRefusal = ref<string | null>(null)
const cutting = ref(false)
const cutWait = computed(() =>
  cutting.value ? 'keeping' : cutName.value.trim() === '' ? 'name the cut' : null,
)

async function cut(): Promise<void> {
  if (cutWait.value !== null) return
  cutRefusal.value = null
  cutting.value = true
  try {
    const made = await cutTattoo(props.place, cutName.value.trim())
    emit('kept', made.name)
  } catch (reason) {
    cutRefusal.value = (reason as Error).message
  } finally {
    cutting.value = false
  }
}

const cards = computed(() =>
  props.list.tattoos.map((tattoo) => {
    const held = props.list.stage1?.[tattoo.name]
    return {
      tattoo,
      held,
      ...card(tattoo, props.place.digest, held, props.list.limits.floor_stage1),
      src: designAt(props.place.digest, tattoo.name),
    }
  }),
)

/* The tattoo *Remove* was pressed on, while the dialog asks about it. */
const asking = ref<string | null>(null)
const question = computed(() => {
  const name = asking.value
  return name === null
    ? null
    : { ...removal(name), run: () => removeTattoo(props.place.digest, name) }
})

function removed(): void {
  const name = asking.value
  asking.value = null
  if (name !== null) emit('removed', name)
}

const flagRefusal = ref<{ name: string; reason: string } | null>(null)

/* Choose or clear *not on this photo*: the pairs the tattoo holds are sent with the flag. */
async function flag(name: string, held: Stage1 | undefined, event: Event): Promise<void> {
  const box = event.target as HTMLInputElement
  const on = box.checked
  flagRefusal.value = null
  try {
    await saveStageOne(props.place.digest, name, { pairs: held?.pairs ?? [], not_on_photo: on })
    emit('flagged')
  } catch (reason) {
    flagRefusal.value = { name, reason: (reason as Error).message }
    box.checked = !on
  }
}

onUnmounted(() => {
  const id = staging.value
  if (id === null) return
  live.follow({ staging: null })
  void cancelStaging(id).catch(() => undefined)
})
</script>

<template>
  <section class="picker">
    <div class="picker__images" data-picker-images>
      <figure class="picker__shown">
        <img :src="renderUrl" :alt="`seed ${seed}`" />
        <figcaption class="picker__note mono">the render</figcaption>
      </figure>
      <figure class="picker__shown">
        <img :src="photoUrl(place)" alt="the photograph" />
        <figcaption class="picker__note mono">the photograph</figcaption>
      </figure>
    </div>
    <div class="picker__make">
      <div class="picker__form" data-upload>
        <p class="section-label">upload a tattoo</p>
        <p class="picker__note mono">{{ formLine('upload') }}</p>
        <p v-if="instead" class="picker__note mono">
          instead of {{ instead }}, which stays kept
        </p>
        <button class="btn btn-secondary" type="button" @click="picker?.click()">
          Upload a tattoo…
        </button>
        <input
          ref="picker"
          class="import__picker"
          type="file"
          accept="image/*,.heic,.heif,.nef,.cr2,.arw,.dng"
          @change="choose"
        />
        <template v-if="chosen">
          <span class="picker__file mono">{{ chosen.file.name }}</span>
          <span v-if="reading" class="picker__note mono">reading…</span>
          <span v-else-if="reported && reported.state === 'converted'" class="picker__note mono">
            converted
          </span>
          <p v-if="fileRefusal" class="picker__refusal" data-file-refusal>
            <span class="refusal__mark" />{{ fileRefusal }}
          </p>
          <label class="picker__name">
            <span class="section-label">name</span>
            <input
              v-model="chosen.name"
              class="input mono"
              type="text"
              aria-label="Tattoo name"
              :disabled="chosen.keeping"
            />
          </label>
          <p v-if="nameRefusal" class="picker__refusal" data-name-refusal>
            <span class="refusal__mark" />{{ nameRefusal }}
          </p>
          <div class="picker__row">
            <span v-if="keepWait" class="picker__note mono">{{ keepWait }}</span>
            <button class="btn btn-secondary" type="button" @click="discard">Cancel</button>
            <button class="btn btn-primary" type="button" :disabled="keepWait !== null" @click="keep">
              Keep
            </button>
          </div>
        </template>
      </div>
      <div class="picker__form" data-cut>
        <p class="section-label">cut from this photo</p>
        <p class="picker__note mono">{{ formLine('cut') }}</p>
        <label class="picker__name">
          <span class="section-label">name</span>
          <input
            v-model="cutName"
            class="input mono"
            type="text"
            aria-label="Cut name"
            :disabled="cutting"
          />
        </label>
        <p v-if="cutRefusal" class="picker__refusal" data-cut-refusal>
          <span class="refusal__mark" />{{ cutRefusal }}
        </p>
        <div class="picker__row">
          <span v-if="cutWait" class="picker__note mono">{{ cutWait }}</span>
          <button class="btn btn-secondary" type="button" :disabled="cutWait !== null" @click="cut">
            Cut from this photo
          </button>
        </div>
      </div>
    </div>
    <p class="section-label">kept tattoos · {{ cards.length }}</p>
    <p v-if="cards.length === 0" class="picker__note mono">none kept yet</p>
    <div class="picker__cards">
      <div v-for="one in cards" :key="one.tattoo.name" class="picker__item">
        <button
          class="picker__card"
          type="button"
          :data-tattoo="one.tattoo.name"
          @click="emit('choose', one.tattoo.name, one.opens)"
        >
          <CutImage v-if="one.tattoo.kind === 'cut'" :place="place" :tattoo="one.tattoo" />
          <img v-else class="picker__image" :src="one.src" :alt="one.tattoo.name" loading="lazy" />
          <span class="picker__title mono">{{ one.tattoo.name }}</span>
          <span class="picker__state mono" :data-state="one.state">{{ one.state }}</span>
          <span class="picker__source mono">{{ one.source }}</span>
          <span v-if="one.stage" class="picker__source mono" data-stage>{{ one.stage }}</span>
        </button>
        <label v-if="one.offers" class="picker__flag mono">
          <input
            type="checkbox"
            :checked="one.held?.not_on_photo === true"
            @change="flag(one.tattoo.name, one.held, $event)"
          />not on this photo
        </label>
        <p v-if="flagRefusal && flagRefusal.name === one.tattoo.name" class="picker__refusal" data-flag-refusal>
          <span class="refusal__mark" />{{ flagRefusal.reason }}
        </p>
        <button
          class="btn btn-secondary picker__remove"
          type="button"
          :data-remove="one.tattoo.name"
          @click="asking = one.tattoo.name"
        >
          Remove
        </button>
      </div>
    </div>
    <ConfirmDialog
      v-if="question"
      marker="remove"
      :title="question.title"
      :name="question.name"
      :run="question.run"
      @close="asking = null"
      @done="removed"
    />
  </section>
</template>
