<script setup lang="ts">
import { noun } from '../words'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { cancelStaging, commitStaging, openStaging, stagedThumbAt } from '../api'
import { useKeys } from '../composables/useKeys'
import { modded, plain } from '../stores/keys'
import { discards } from '../staging'
import { useLiveStore } from '../stores/live'
import KeyHint from './KeyHint.vue'
import type { StagedFile } from '../types'

/* The New batch and Add sources sheet (design spec J1, J7): files chosen in the
   browser's dialog, each sent in its own request with its own bar, then read and
   cleaned by the server one at a time, each step reported on the page's stream,
   then imported in one move. With `batch`, the files join that batch; without
   it, the sheet names a new one. */
const props = defineProps<{ batch?: string }>()
const emit = defineEmits<{ close: []; imported: [batch: string] }>()

/* `queued` before its upload starts; `waiting` and `converting` are the server's. */
type Phase = 'queued' | 'uploading' | 'waiting' | 'converting' | 'read' | 'refused'

interface Tile {
  key: number
  file: File
  /* The server's id for this upload, once its request is answered. */
  upload: string | null
  phase: Phase
  progress: number
  result: StagedFile | null
  refusal: string | null
  asIs: boolean
}

/* One file, one request, its body the file itself, answered with its upload id
   once its bytes land. `XMLHttpRequest` rather than `fetch`, because only it
   reports an upload's progress. */
function uploadFile(id: string, file: File, onProgress: (fraction: number) => void): Promise<string> {
  const url = `/api/staging/${encodeURIComponent(id)}/files/${encodeURIComponent(file.name)}`
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('PUT', url)
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(event.loaded / event.total)
    }
    xhr.onload = () => {
      let body: { refusal?: string; upload?: string } = {}
      try {
        body = JSON.parse(xhr.responseText) as typeof body
      } catch {
        body = {}
      }
      if (xhr.status >= 200 && xhr.status < 300 && body.upload) resolve(body.upload)
      else reject(new Error(body.refusal ?? `${file.name}: the server answered ${xhr.status}`))
    }
    xhr.onerror = () => reject(new Error(`${file.name}: the upload did not reach the server`))
    xhr.send(file)
  })
}

/* At most this many uploads in flight, so the first files finish first. */
const PARALLEL = 2

const picker = ref<HTMLInputElement | null>(null)
const staging = ref<string | null>(null)
const tiles = ref<Tile[]>([])
const name = ref(new Date().toISOString().slice(0, 10))
const refusal = ref<string | null>(null)
/* Import's commit is in flight: no file is added, nor Import pressed again. */
const committing = ref(false)
let committed = false
/* The sheet is gone: an import that opens after it is cancelled, never followed. */
let closed = false
let counter = 0
const live = useLiveStore()
const opening = openStaging().then(
  (opened) => {
    if (closed) {
      void cancelStaging(opened.id).catch(() => undefined)
      return null
    }
    staging.value = opened.id
    live.follow({ staging: opened.id })
    return opened.id
  },
  (reason: Error) => {
    refusal.value = reason.message
    return null
  },
)

const adding = computed(() => props.batch !== undefined)
const read = computed(() => tiles.value.filter((one) => one.phase === 'read' || one.phase === 'refused'))
const reading = computed(() => read.value.length < tiles.value.length)
const refused = computed(() => tiles.value.filter((one) => one.phase === 'refused'))
const ready = computed(() =>
  tiles.value.filter(
    (one) =>
      one.result !== null &&
      (one.result.state === 'ready' ||
        one.result.state === 'converted' ||
        (one.result.state === 'not cleaned' && one.asIs)),
  ),
)
const shown = computed(() => tiles.value.filter((one) => one.phase !== 'refused'))

/* Import's reason for being disabled, or null when it is not (rule 4). */
const disabled = computed(() => {
  if (committing.value) return 'Importing'
  if (tiles.value.length === 0) return 'Choose files to import'
  if (reading.value) return `Reading ${read.value.length} of ${tiles.value.length}`
  if (ready.value.length === 0)
    return adding.value ? 'Nothing new to add' : "None of the chosen files could be read."
  return null
})

function choose(event: Event): void {
  const input = event.target as HTMLInputElement
  for (const file of input.files ?? []) {
    tiles.value.push({
      key: counter++,
      file,
      upload: null,
      phase: 'queued',
      progress: 0,
      result: null,
      refusal: null,
      asIs: false,
    })
  }
  input.value = ''
  pump()
}

/* Start the next queued uploads, up to `PARALLEL` at once. */
function pump(): void {
  const running = tiles.value.filter((one) => one.phase === 'uploading')
  const queued = tiles.value.filter((one) => one.phase === 'queued')
  for (const one of queued.slice(0, Math.max(PARALLEL - running.length, 0))) void send(one)
}

/* The import's files, from the page's stream, each on the tile holding its upload. */
watch(
  () => live.files,
  () => {
    for (const one of tiles.value) apply(one)
  },
)

/* Put its upload's reported state on a tile. Its upload's answer, not the
   stream, says it waits: the stream can report it first. */
function apply(one: Tile): void {
  const reported = one.upload === null ? undefined : live.files[one.upload]
  if (!reported || reported.state === 'waiting') return
  if (reported.state === 'converting') {
    one.phase = 'converting'
  } else if (reported.state === 'refused') {
    one.phase = 'refused'
    one.refusal = reported.refusal ?? `${reported.file}: refused`
  } else {
    one.phase = 'read'
    one.result = { name: reported.name ?? reported.file, state: reported.state, carries: reported.carries ?? [] }
  }
}

async function send(one: Tile): Promise<void> {
  one.phase = 'uploading'
  const id = await opening
  if (id === null) {
    one.phase = 'refused'
    one.refusal = refusal.value
    return
  }
  try {
    one.upload = await uploadFile(id, one.file, (fraction) => {
      one.progress = fraction
    })
    if (one.phase === 'uploading') one.phase = 'waiting'
    apply(one)
  } catch (reason) {
    one.phase = 'refused'
    one.refusal = (reason as Error).message
  }
  pump()
}

/* A read file's preview, served from staging; a skipped file has none of its own. */
function preview(one: Tile): string | null {
  const result = one.result
  if (staging.value === null || !result || result.state === 'skipped') return null
  return stagedThumbAt(staging.value, result.name)
}

/* `HEIC → JPEG`, from the chosen name's suffix to the staged one's. */
function badge(one: Tile): string | null {
  const result = one.result
  if (!result || result.state !== 'converted') return null
  const from = one.file.name.split('.').pop()?.toUpperCase() ?? ''
  const to = result.name.split('.').pop()?.toUpperCase() ?? ''
  const kind = (suffix: string) => (suffix === 'JPG' ? 'JPEG' : suffix)
  return kind(from) === kind(to) ? 're-encoded' : `${kind(from)} → ${kind(to)}`
}

function size(bytes: number): string {
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.ceil(bytes / 1024)} KB`
}

function total(): string {
  return size(ready.value.reduce((sum, one) => sum + one.file.size, 0))
}

async function importAll(): Promise<void> {
  if (disabled.value !== null || staging.value === null) return
  refusal.value = null
  const target = props.batch ?? name.value.trim()
  const asIs = tiles.value
    .filter((one) => one.result?.state === 'not cleaned' && one.asIs)
    .map((one) => one.result?.name ?? '')
  committing.value = true
  try {
    const done = await commitStaging(staging.value, target, asIs, adding.value)
    committed = true
    emit('imported', done.batch)
  } catch (reason) {
    refusal.value = (reason as Error).message
  } finally {
    committing.value = false
  }
}

async function cancel(): Promise<void> {
  live.follow({ staging: null })
  if (staging.value !== null && !committed) {
    committed = true
    await cancelStaging(staging.value).catch(() => undefined)
  }
  emit('close')
}

/* While a commit is in flight Esc does nothing: a cancel then would delete the
   folder the commit is moving. */
useKeys('overlay', [
  {
    id: 'cancel',
    keys: plain('Escape'),
    label: 'cancel',
    run: () => void cancel(),
    when: () => !committing.value,
  },
  {
    id: 'import',
    keys: [modded('Enter')],
    label: 'import',
    run: () => void importAll(),
    inField: true,
  },
])

onMounted(() => picker.value?.click())

onUnmounted(() => {
  closed = true
  live.follow({ staging: null })
  if (discards(staging.value, committing.value, committed))
    void cancelStaging(staging.value).catch(() => undefined)
})
</script>

<template>
  <div class="scrim">
    <section class="import" role="dialog" :aria-label="adding ? 'Add sources' : 'New batch'">
      <header class="import__head">
        <h2 class="import__title">{{ adding ? 'Add sources' : 'New batch' }}</h2>
        <span v-if="reading" class="import__count import__count--reading mono">
          reading {{ read.length }} of {{ tiles.length }}
        </span>
        <span v-else class="import__count mono">
          {{ tiles.length }} {{ noun(tiles.length, 'file') }} chosen ·
          {{ ready.length }} {{ noun(ready.length, 'source') }} · {{ refused.length }} refused
        </span>
        <button
          class="btn btn-secondary import__add"
          type="button"
          :disabled="committing"
          @click="picker?.click()"
        >
          Add files…
        </button>
        <input
          ref="picker"
          class="import__picker"
          type="file"
          multiple
          accept="image/*,.heic,.heif,.nef,.cr2,.arw,.dng"
          @change="choose"
        />
      </header>
      <div class="import__body">
        <div class="import__files">
          <p class="section-label">sources · {{ ready.length }} · {{ total() }}</p>
          <div class="import__tiles">
            <div
              v-for="one in shown"
              :key="one.key"
              class="import__tile"
              :class="{ 'import__tile--dim': one.result?.state === 'skipped' }"
              :data-file="one.file.name"
              :data-phase="one.phase"
              :data-state="one.result?.state ?? ''"
            >
              <img v-if="preview(one)" class="import__preview" :src="preview(one) ?? ''" alt="" />
              <span class="import__name mono">{{ one.result?.name ?? one.file.name }}</span>
              <span class="import__size mono">{{ size(one.file.size) }}</span>
              <span v-if="one.phase === 'queued'" class="import__word mono">queued</span>
              <template v-else-if="one.phase === 'uploading'">
                <span class="import__bar">
                  <span class="import__fill" :style="{ width: `${Math.round(one.progress * 100)}%` }" />
                </span>
                <span class="import__word mono">uploading {{ Math.round(one.progress * 100) }}%</span>
              </template>
              <span v-else-if="one.phase === 'waiting'" class="import__word mono">waiting</span>
              <template v-else-if="one.phase === 'converting'">
                <span class="import__bar import__bar--running"><span class="import__fill" /></span>
                <span class="import__word import__word--running mono">converting…</span>
              </template>
              <template v-else-if="one.result">
                <span v-if="badge(one)" class="import__badge mono">{{ badge(one) }}</span>
                <span v-if="one.result.state === 'skipped'" class="import__word mono">already chosen</span>
                <span
                  v-else-if="one.result.name !== one.file.name && !badge(one)"
                  class="import__word mono"
                  >chosen as {{ one.file.name }}</span
                >
                <span v-if="one.result.state === 'ready'" class="import__word mono">ready</span>
                <template v-if="one.result.state === 'not cleaned'">
                  <span class="import__warn mono">⚠ not cleaned · {{ one.result.carries.join(', ') }}</span>
                  <label class="import__asis mono">
                    <input v-model="one.asIs" type="checkbox" />import as it is
                  </label>
                </template>
              </template>
            </div>
          </div>
          <template v-if="refused.length">
            <p class="section-label">refused · {{ refused.length }}</p>
            <p
              v-for="one in refused"
              :key="one.key"
              class="import__refused"
              :data-file="one.file.name"
            >
              <span class="refusal__mark" /><span class="mono">{{ one.file.name }}</span>
              <span class="import__reason">{{ one.refusal }}</span>
            </p>
          </template>
        </div>
        <div v-if="!adding" class="import__side">
          <p class="section-label">name</p>
          <input v-model="name" class="input import__batch mono" type="text" aria-label="Batch name" />
        </div>
      </div>
      <p v-if="refusal" class="import__refused import__refused--commit">
        <span class="refusal__mark" /><span class="import__reason">{{ refusal }}</span>
      </p>
      <footer class="import__foot">
        <span v-if="disabled" class="import__disabled">{{ disabled }}</span>
        <button class="btn btn-secondary" type="button" :disabled="committing" @click="cancel">
          Cancel<KeyHint command="cancel" />
        </button>
        <button
          class="btn btn-primary"
          type="button"
          :disabled="disabled !== null"
          @click="importAll"
        >
          {{ adding ? `Import ${ready.length}` : 'Import' }}<KeyHint command="import" />
        </button>
      </footer>
    </section>
  </div>
</template>
