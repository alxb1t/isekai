import { computed, ref, watch } from 'vue'
import { inputDetail, saveDraft } from '../api'
import type { Budget, InputDetail } from '../types'

/* Long enough that a burst of typing is one write rather than ten, short enough
   that the receipt is true by the time the operator looks up from the row. */
const DEBOUNCE = 400

/** One edit, recorded so it can be taken back. */
interface Edit {
  field: string
  before: string[]
  after: string[]
}

/**
 * The draft under correction: its fields, its autosave, its undo stack.
 *
 * **The server is the source of truth and there is no Save control anywhere.**
 * Every edit mutates local state and schedules a debounced `PUT` of the whole
 * draft; the last-saved timestamp comes back from the server rather than from
 * the client clock, because the receipt has to be true. If a Save button ever
 * appears, the design has been broken.
 *
 * **Undo is a stack of edit operations, not sheet snapshots.** It crosses every
 * field and behaves like a text editor's: one commit, one removal or one
 * replacement is one step. It is cleared when the operator changes input,
 * because an undo that reached back into a different photograph would be a
 * surprise rather than a convenience.
 */
export function useSheet() {
  const detail = ref<InputDetail | null>(null)
  const fields = ref<Record<string, string[]>>({})
  const budget = ref<Budget | null>(null)
  const saved = ref<number | null>(null)
  const dirty = ref(false)
  /* A save is in flight. The receipt is the only thing on the page that talks
     about saving, so it is also the only place an in-flight save can show. */
  const saving = ref(false)
  const refusal = ref<string | null>(null)
  const loading = ref(true)

  const done: Edit[] = []
  const undone: Edit[] = []
  // Counted, not a flag: a second PUT can start before the first has answered,
  // and the spinner must go when the last one lands rather than the first.
  let inFlight = 0
  let timer: ReturnType<typeof setTimeout> | undefined
  let current = ''

  const readonly = computed(() => detail.value?.readonly ?? true)

  async function open(id: string): Promise<void> {
    current = id
    loading.value = true
    done.length = 0
    undone.length = 0
    const body = await inputDetail(id)
    if (current !== id) return
    detail.value = body
    fields.value = { ...body.fields }
    budget.value = body.budget
    saved.value = body.saved
    dirty.value = false
    loading.value = false
    inFlight = 0
    saving.value = false
  }

  function flush(): void {
    if (timer !== undefined) clearTimeout(timer)
    timer = undefined
    if (detail.value === null || detail.value.readonly) return
    const id = current
    const payload = { ...fields.value }
    inFlight += 1
    saving.value = true
    saveDraft(id, payload)
      .then((receipt) => {
        if (current !== id) return
        budget.value = receipt.budget
        // The server's clock, never the browser's: a receipt the client wrote
        // for itself is a claim about a save rather than a record of one.
        saved.value = receipt.saved
        dirty.value = false
        refusal.value = null
      })
      .catch((reason: Error) => {
        if (current !== id) return
        refusal.value = reason.message
      })
      .finally(() => {
        inFlight -= 1
        if (inFlight === 0) saving.value = false
      })
  }

  function schedule(): void {
    dirty.value = true
    if (timer !== undefined) clearTimeout(timer)
    timer = setTimeout(flush, DEBOUNCE)
  }

  function apply(edit: Edit): void {
    fields.value = { ...fields.value, [edit.field]: edit.after }
    schedule()
  }

  function record(field: string, after: string[]): void {
    const before = [...(fields.value[field] ?? [])]
    done.push({ field, before, after })
    undone.length = 0
    apply({ field, before, after })
  }

  function commit(field: string, tag: string, replacing: number | null): void {
    const tags = [...(fields.value[field] ?? [])]
    // Replacing a selected chip by typing is the single commonest edit in the
    // job -- three keystrokes, not delete-then-add.
    if (replacing !== null && replacing >= 0 && replacing < tags.length) tags[replacing] = tag
    else if (!tags.includes(tag)) tags.push(tag)
    else return
    record(field, tags)
  }

  function remove(field: string, index: number): void {
    const tags = [...(fields.value[field] ?? [])]
    if (index < 0 || index >= tags.length) return
    tags.splice(index, 1)
    record(field, tags)
  }

  function undo(): void {
    const edit = done.pop()
    if (!edit) return
    undone.push(edit)
    apply({ ...edit, after: edit.before })
  }

  function redo(): void {
    const edit = undone.pop()
    if (!edit) return
    done.push(edit)
    apply(edit)
  }

  const edited = computed(() => done.length > 0)

  watch(fields, () => {}, { deep: true })

  return {
    detail,
    fields,
    budget,
    saved,
    dirty,
    saving,
    edited,
    refusal,
    loading,
    readonly,
    open,
    commit,
    remove,
    undo,
    redo,
    flush,
  }
}
