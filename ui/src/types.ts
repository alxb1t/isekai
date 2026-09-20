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
  vocabulary: number
  approved: number
  inputs: BatchInput[]
}

export interface Budget {
  total: number
  per_field: Record<string, number>
  overhead: number
}

/* One scored tag from the local tagger. The confidence is shown on the chip
   because a wrong tag sorted below a right one refutes itself -- `black hair
   0.31` under `brown hair 0.91` needs no explanation. */
export interface ScoredTag {
  tag: string
  confidence: number
}

/* One tag from the hosted tagger, marked server-side for what can actually be
   committed. `posts` is null where the tag is outside the vocabulary, and the
   missing number is the signal: a chip with no count reads as the model's word
   rather than Danbooru's. */
export interface OfferedTag {
  tag: string
  in_vocabulary: boolean
  posts: number | null
}

export interface InputDetail {
  id: string
  width: number
  height: number
  caption: string | null
  /* Null where the artifact is absent, which is never a failure: a run
     captioned before v0.20, a flow with no hosted block, or a tagger that
     failed. The panel simply is not drawn. */
  wd14: ScoredTag[] | null
  tags: OfferedTag[] | null
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
