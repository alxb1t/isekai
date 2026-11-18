/* The sheet's history in `ui/src/edits.ts`: a stack of edit operations, not sheet
   snapshots. It crosses every field and behaves like a text editor's: one commit, one
   removal or one replacement is one step. The sheet clears it when the operator changes
   input, because an undo that reached back into a different photograph would be a surprise
   rather than a convenience. Every function returns a new state and leaves its argument as
   it was; a call that changes nothing returns the state it was given. */

/** One edit, recorded so it can be taken back. */
export interface Edit {
  field: string
  before: string[]
  after: string[]
}

/** The draft's fields, the edits done, and the edits undone that a redo brings back. */
export interface Edits {
  fields: Record<string, string[]>
  past: Edit[]
  future: Edit[]
}

/** Return a state holding `fields`, with nothing to undo or redo. */
export function held(fields: Record<string, string[]>): Edits {
  return { fields: { ...fields }, past: [], future: [] }
}

/** Return the state holding `fields` in place of its own, its history as it was. */
export function reloaded(state: Edits, fields: Record<string, string[]>): Edits {
  return { ...state, fields: { ...fields } }
}

function recorded(state: Edits, field: string, after: string[]): Edits {
  const before = [...(state.fields[field] ?? [])]
  return { fields: { ...state.fields, [field]: after }, past: [...state.past, { field, before, after }], future: [] }
}

/** Return the state with `tag` committed to `field`: it replaces the chip at `replacing`, else it is added unless it is there. */
export function committed(state: Edits, field: string, tag: string, replacing: number | null): Edits {
  const tags = [...(state.fields[field] ?? [])]
  // Replacing a selected chip by typing is the single commonest edit in the
  // job -- three keystrokes, not delete-then-add.
  if (replacing !== null && replacing >= 0 && replacing < tags.length) tags[replacing] = tag
  else if (!tags.includes(tag)) tags.push(tag)
  else return state
  return recorded(state, field, tags)
}

/** Return the state without the tag at `index` of `field`; unchanged when `index` is out of range. */
export function removed(state: Edits, field: string, index: number): Edits {
  const tags = [...(state.fields[field] ?? [])]
  if (index < 0 || index >= tags.length) return state
  tags.splice(index, 1)
  return recorded(state, field, tags)
}

/** Return the state as it was before its last edit, which `redone` brings back; unchanged with nothing to undo. */
export function undone(state: Edits): Edits {
  const edit = state.past.at(-1)
  if (!edit) return state
  return {
    fields: { ...state.fields, [edit.field]: edit.before },
    past: state.past.slice(0, -1),
    future: [...state.future, edit],
  }
}

/** Return the state as it was before its last undo; unchanged with nothing to redo. */
export function redone(state: Edits): Edits {
  const edit = state.future.at(-1)
  if (!edit) return state
  return {
    fields: { ...state.fields, [edit.field]: edit.after },
    past: [...state.past, edit],
    future: state.future.slice(0, -1),
  }
}
