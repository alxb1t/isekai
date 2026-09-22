/* The shapes the seven endpoints return. One file, because a type that disagreed
   with `app.py` would be wrong in every component at once. */

export type MarkKind = 'filled' | 'hollow' | 'dashed' | 'half' | 'reopened'

/* `re-opened` is approved *and* carrying a later draft -- the state
   `review --flow F --new-version` writes, and the only one in which an
   approved input is editable again. */
export type InputStatus = 'approved' | 're-opened' | 'draft'

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

/* One tag from the hosted tagger that the vocabulary actually carries. The
   server sends only these: on v0.20's acceptance batch roughly nine in ten of
   this model's tags were committable to no field, and reading nine to find the
   tenth is attention spent on the busiest pane in the surface.

   So `posts` is never null here, and there is no membership flag — every tag
   that reaches the page is in the vocabulary by construction. The artifact on
   disk still holds the ones that were dropped. */
export interface OfferedTag {
  tag: string
  posts: number
}

/* Every candidate tag for every criterion the acting flow declares — the same
   table the router fills a sheet from, read the other way. A declared criterion
   the table holds nothing for is present with an empty array rather than absent,
   because a missing row is indistinguishable from one nobody has authored yet.
   The excluded list is never here: it is an assertion about the table, not
   material to browse. */
export interface FieldCandidates {
  fields: Record<string, OfferedTag[]>
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
