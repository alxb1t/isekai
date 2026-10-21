<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { cancelStaging, commitStaging, openStaging } from '../api'
import type { StagedFile } from '../types'

/* The New batch and Add sources sheet (design spec J1, J7): files chosen in the
   browser's dialog, each sent in its own request with its own bar, read and
   cleaned by the server, then imported in one move. With `batch`, the files
   join that batch; without it, the sheet names a new one. */
const props = defineProps<{ batch?: string }>()
const emit = defineEmits<{ close: []; imported: [batch: string] }>()

type Phase = 'waiting' | 'uploading' | 'reading' | 'read' | 'refused'

interface Tile {
  key: number
  file: File
  phase: Phase
  progress: number
  result: StagedFile | null
  refusal: string | null
  asIs: boolean
}

/* One file, one request, its body the file itself. `XMLHttpRequest` rather than
   `fetch`, because only it reports an upload's progress. */
function uploadFile(
  id: string,
  file: File,
  onProgress: (fraction: number) => void,
): Promise<StagedFile> {
  const url = `/api/staging/${encodeURIComponent(id)}/files/${encodeURIComponent(file.name)}`
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('PUT', url)
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(event.loaded / event.total)
    }
    xhr.onload = () => {
      let body: { refusal?: string } & Partial<StagedFile> = {}
      try {
        body = JSON.parse(xhr.responseText) as typeof body
      } catch {
        body = {}
      }
      if (xhr.status >= 200 && xhr.status < 300) resolve(body as StagedFile)
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
let committed = false
let counter = 0
const opening = openStaging().then(
  (opened) => {
    staging.value = opened.id
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
      phase: 'waiting',
      progress: 0,
      result: null,
      refusal: null,
      asIs: false,
    })
  }
  input.value = ''
  pump()
}

/* Start the next waiting uploads, up to `PARALLEL` at once. */
function pump(): void {
  const running = tiles.value.filter((one) => one.phase === 'uploading' || one.phase === 'reading')
  const waiting = tiles.value.filter((one) => one.phase === 'waiting')
  for (const one of waiting.slice(0, Math.max(PARALLEL - running.length, 0))) void send(one)
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
    one.result = await uploadFile(id, one.file, (fraction) => {
      one.progress = fraction
      if (fraction >= 1) one.phase = 'reading'
    })
    one.phase = 'read'
  } catch (reason) {
    one.phase = 'refused'
    one.refusal = (reason as Error).message
  }
  pump()
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
  try {
    const done = await commitStaging(staging.value, target, asIs, adding.value)
    committed = true
    emit('imported', done.batch)
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
}

async function cancel(): Promise<void> {
  if (staging.value !== null && !committed) {
    committed = true
    await cancelStaging(staging.value).catch(() => undefined)
  }
  emit('close')
}

/* ⌘↵ imports, esc cancels. */
function onKey(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault()
    void cancel()
  } else if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
    event.preventDefault()
    void importAll()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKey)
  picker.value?.click()
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
  if (staging.value !== null && !committed) void cancelStaging(staging.value).catch(() => undefined)
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
          {{ tiles.length }} files chosen · {{ ready.length }} sources · {{ refused.length }} refused
        </span>
        <button class="btn btn-secondary import__add" type="button" @click="picker?.click()">
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
              <span class="import__name mono">{{ one.result?.name ?? one.file.name }}</span>
              <span class="import__size mono">{{ size(one.file.size) }}</span>
              <span v-if="one.phase === 'waiting'" class="import__word mono">waiting</span>
              <span v-else-if="one.phase === 'uploading'" class="import__bar">
                <span class="import__fill" :style="{ width: `${Math.round(one.progress * 100)}%` }" />
              </span>
              <span v-else-if="one.phase === 'reading'" class="import__word import__word--running mono"
                >converting…</span
              >
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
        <button class="btn btn-secondary" type="button" @click="cancel">
          Cancel<span class="appbar__key">esc</span>
        </button>
        <button
          class="btn btn-primary"
          type="button"
          :disabled="disabled !== null"
          @click="importAll"
        >
          {{ adding ? `Import ${ready.length}` : 'Import' }}<span class="appbar__key">⌘↵</span>
        </button>
      </footer>
    </section>
  </div>
</template>
