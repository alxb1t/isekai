/* The shapes the six endpoints return. One file, because a type that disagreed
   with `app.py` would be wrong in every component at once. */

export type MarkKind = 'filled' | 'hollow' | 'dashed' | 'half'

export type InputStatus = 'approved' | 'draft'

export interface BatchInput {
  id: string
  width: number
  height: number
  status: InputStatus
}

export interface BatchInfo {
  flow: string
  schema: string[]
  /* Per field, the word the schema says its tags are spelled with -- `hair` for
     `hair_colour`, `eyebrows` for `eyebrows` -- or null where it declares none. */
  suffixes: Record<string, string | null>
  vocabulary: number
  approved: number
  inputs: BatchInput[]
}

export interface Budget {
  total: number
  per_field: Record<string, number>
  overhead: number
}

export interface InputDetail {
  id: string
  width: number
  height: number
  caption: string | null
  fields: Record<string, string[]>
  readonly: boolean
  draft: string | null
  approved: string | null
  saved: number | null
  approved_at: number | null
  budget: Budget
}

export interface VocabEntry {
  tag: string
  posts: number
  rare: boolean
}

export interface TagMatches {
  matches: VocabEntry[]
  total: number
}

/** One approved sheet, as the manifest lists it. */
export interface ApprovedSheet {
  id: string
  name: string
  tokens: number
  at: string
}

/* SDXL's text encoders read 77 tokens at a time. The number is the pipeline's --
   `review.ENCODER_WINDOW` -- and it is restated here only because the bar has to
   draw it; nothing in the browser decides it. */
export const ENCODER_WINDOW = 77
