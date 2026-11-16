export const clock = (at: number | null) =>
  at === null ? null : new Date(at * 1000).toLocaleTimeString('en-GB', { hour12: false })

/* The draft's time to the minute. It is rewritten every few seconds while the
   operator types, and a seconds field that ticks under the eye is noise; the
   approved time keeps its seconds, because it is written once. */
export const minute = (at: number | null) =>
  at === null
    ? null
    : new Date(at * 1000).toLocaleTimeString('en-GB', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
      })

export interface Standing {
  drafted: boolean
  approved: boolean
  readonly: boolean
  approvedAt: string | null
  revision: { seed: string | null; version: number } | null
}

/* `③ sheet — approved` once it is, which is also when the fields go read-only.
   The reading is taken from disk rather than from anything held here. It is NOT
   "has no draft": `review --new-version` writes a draft beside the approved
   artifact, and that input is re-opened -- editable, and carrying a correction
   the tagger did not write. */
export function kickerOf(held: Standing): string {
  if (held.drafted && !held.approved) return 'draft'
  // No approved artifact is the tagger's draft, whether or not the payload has
  // arrived -- `readonly` defaults to true while `detail` is null, so testing
  // it first would call an unloaded sheet approved.
  if (!held.approved) return 'draft from the tagger'
  if (held.readonly) return held.approvedAt ? `approved ${held.approvedAt}` : 'approved'
  const { revision } = held
  if (revision?.seed) return `revision of render ${revision.seed}`
  return revision ? `revision of v${revision.version}` : 're-opened'
}
