<script setup lang="ts">
import { noun } from '../words'
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import {
  cancelStaging,
  commitStaging,
  openStaging,
  removeStaged,
  stagedAt,
  stagedThumbAt,
} from '../api'
import { useKeys } from '../composables/useKeys'
import { useHeldFocus } from '../composables/useHeldFocus'
import type { Move } from '../grid'
import { isField, modded, plain } from '../stores/keys'
import { after, discards, heir, orphans, removal, stepped, withheld } from '../staging'
import { useLiveStore } from '../stores/live'
import ImageViewer, { type Shown } from './ImageViewer.vue'
import KeyHint from './KeyHint.vue'
import type { StagedFile } from '../types'

/* The New collection and Add sources sheet (design spec J1, J7): files chosen in the
   browser's dialog, each sent in its own request with its own bar, then read and
   cleaned by the server one at a time, each step reported on the page's stream,
   then imported in one move. With `collection`, the files join that collection; without
   it, the sheet names a new one. */
const props = defineProps<{ collection?: string }>()
const emit = defineEmits<{ close: []; imported: [collection: string] }>()

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
/* The removals whose tile has not gone yet: Import waits for each. */
const removing = ref(0)
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

const adding = computed(() => props.collection !== undefined)
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
const disabled = computed(() =>
  withheld({
    committing: committing.value,
    removing: removing.value,
    chosen: tiles.value.length,
    read: read.value.length,
    ready: ready.value.length,
    adding: adding.value,
  }),
)

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
watch(() => live.files, settle)

/* Put each tile's reported state on it, then send again each copy whose file no
   tile holds: removed as the copy was read, so the copy's bytes are staged nowhere. */
function settle(): void {
  for (const one of tiles.value) apply(one)
  const lost = orphans(tiles.value.map((tile) => tile.result))
  for (const index of lost) {
    const one = tiles.value[index]
    one.upload = null
    one.phase = 'queued'
    one.progress = 0
    one.result = null
  }
  if (lost.length > 0) pump()
}

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
    one.result = {
      name: reported.name ?? reported.file,
      state: reported.state,
      carries: reported.carries ?? [],
      copyOf: reported.copy_of ?? null,
    }
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
    settle()
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

/* The tiles' grid, the focused tile's place in `shown`, and the viewer's place in `viewable`. */
const grid = ref<HTMLElement | null>(null)
const focused = ref<number | null>(null)
const viewing = ref<number | null>(null)
let viewed: number | null = null

function focusTile(index: number | null): void {
  if (index === null) return
  void nextTick(() => grid.value?.querySelectorAll<HTMLElement>('.import__tile')[index]?.focus())
}

/* The grid's columns, as the browser lays them out. */
function columns(): number {
  const held = grid.value
  return held ? getComputedStyle(held).gridTemplateColumns.split(' ').filter(Boolean).length : 0
}

function move(to: Move): void {
  if (focused.value !== null) focusTile(stepped(focused.value, shown.value.length, columns(), to))
}

/* Take a chosen file out of the import, unasked: nothing is committed yet (D3). */
async function remove(one: Tile): Promise<void> {
  const from = removal(one.phase, one.result?.state)
  if (from === null || committing.value) return
  const next = after(shown.value.indexOf(one), shown.value.length)
  const results = tiles.value.map((tile) => tile.result)
  const copy = one.result ? tiles.value[heir(results, one.result.name)] : undefined
  removing.value += 1
  try {
    if (from === 'staging' && copy) {
      // A copy still chosen takes the file over, under the removed tile's upload.
      copy.upload = one.upload
      copy.result = one.result
      copy.asIs = one.asIs
    } else if (from === 'staging' && staging.value !== null && one.result) {
      try {
        await removeStaged(staging.value, one.result.name)
      } catch (reason) {
        refusal.value = (reason as Error).message
        return
      }
    }
    refusal.value = null
    tiles.value = tiles.value.filter((tile) => tile !== one)
    // A copy heard while the removal was in flight lost its file with it.
    settle()
    focusTile(next)
  } finally {
    // Only now may Import commit: a copy the removal left standing is queued again.
    removing.value -= 1
  }
}

/* The read files, each full size from staging, that `↵` opens in the viewer. */
const viewable = computed(() => shown.value.filter((one) => preview(one) !== null))
const images = computed<Shown[]>(() =>
  viewable.value.map((one) => ({
    src: stagedAt(staging.value ?? '', one.result?.name ?? ''),
    name: one.result?.name ?? one.file.name,
  })),
)

function view(): void {
  const one = focused.value === null ? undefined : shown.value[focused.value]
  const index = one ? viewable.value.indexOf(one) : -1
  if (index < 0) return
  viewed = focused.value
  viewing.value = index
}

function closeViewer(): void {
  viewing.value = null
  focusTile(viewed)
}

/* Once every file is read, the first tile takes the focus unless a field or a tile holds it. */
watch(reading, (now) => {
  if (!now && shown.value.length > 0 && focused.value === null && !isField(document.activeElement))
    focusTile(0)
})

async function importAll(): Promise<void> {
  if (disabled.value !== null || staging.value === null) return
  refusal.value = null
  const target = props.collection ?? name.value.trim()
  const asIs = tiles.value
    .filter((one) => one.result?.state === 'not cleaned' && one.asIs)
    .map((one) => one.result?.name ?? '')
  committing.value = true
  try {
    const done = await commitStaging(staging.value, target, asIs, adding.value)
    committed = true
    emit('imported', done.collection)
  } catch (reason) {
    refusal.value = (reason as Error).message
  } finally {
    committing.value = false
    // A commit refused after the sheet closed leaves a folder no one will import.
    leave()
  }
}

/* Cancel the staging folder if the sheet has closed and no commit holds it. */
function leave(): void {
  const id = staging.value
  if (id !== null && discards(id, closed, committing.value, committed))
    void cancelStaging(id).catch(() => undefined)
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
  ...(
    [
      ['tile-left', plain('KeyH', 'ArrowLeft'), 'column-'],
      ['tile-right', plain('KeyL', 'ArrowRight'), 'column+'],
      ['tile-up', plain('KeyK', 'ArrowUp'), 'row-'],
      ['tile-down', plain('KeyJ', 'ArrowDown'), 'row+'],
    ] as const
  ).map(([id, keys, to]) => ({
    id,
    keys: [...keys],
    label: 'move',
    run: () => move(to),
    when: onTile,
  })),
  {
    id: 'remove-file',
    keys: plain('Backspace'),
    label: 'remove the file',
    run: () => {
      const one = focused.value === null ? undefined : shown.value[focused.value]
      if (one) void remove(one)
    },
    when: () => onTile() && !committing.value,
  },
  { id: 'view-file', keys: plain('Enter'), label: 'full size', run: view, when: onTile },
])

function onTile(): boolean {
  return focused.value !== null
}

/* A modal dialog, on its first control. */
const dialog = ref<HTMLDialogElement | null>(null)
useHeldFocus(dialog)

onMounted(() => {
  dialog.value?.showModal()
  picker.value?.click()
})

onUnmounted(() => {
  closed = true
  live.follow({ staging: null })
  leave()
})
</script>

<template>
  <dialog
    ref="dialog"
    class="import"
    :aria-label="adding ? 'Add sources' : 'New collection'"
    @cancel.prevent
  >
    <header class="import__head">
      <h2 class="import__title">{{ adding ? 'Add sources' : 'New collection' }}</h2>
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
        <div ref="grid" class="import__tiles">
          <div
            v-for="(one, index) in shown"
            :key="one.key"
            class="import__tile"
            :class="{ 'import__tile--dim': one.result?.state === 'skipped' }"
            :tabindex="index === (focused ?? 0) ? 0 : -1"
            :data-file="one.file.name"
            :data-phase="one.phase"
            :data-state="one.result?.state ?? ''"
            @focusin="focused = index"
            @focusout="focused = null"
          >
            <button
              v-if="removal(one.phase, one.result?.state) !== null"
              class="import__remove"
              type="button"
              tabindex="-1"
              :disabled="committing"
              :aria-label="`Remove ${one.result?.name ?? one.file.name}`"
              @click="remove(one)"
            >
              ×
            </button>
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
        <input v-model="name" class="input import__collection mono" type="text" aria-label="Collection name" />
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
    <ImageViewer v-if="viewing !== null" :images="images" :start="viewing" @close="closeViewer" />
  </dialog>
</template>
