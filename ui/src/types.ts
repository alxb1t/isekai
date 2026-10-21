/* The shapes the endpoints return. One file, because a type that disagreed
   with `app.py` would be wrong in every component at once. */

export type MarkKind = 'filled' | 'hollow' | 'dashed' | 'half' | 'ring'

/* `re-opened` is approved *and* carrying a later draft -- the state
   `review --flow F --new-version` writes, and the only one in which an
   approved input is editable again. */
export type InputStatus = 'approved' | 're-opened' | 'draft'

export interface BatchInput {
  /* The run's digest. */
  id: string
  name: string
  width: number
  height: number
  status: InputStatus
}

/* One flow's figures in a batch, out of the sources whose runs hold it. */
export interface FlowCount {
  flow: string
  approved: number
  rendered: number
  of: number
}

/* One folder of the library. A folder that is not a batch carries only its
   name: it is listed and never opened. `newest` is the server's clock. */
export interface LibraryRow {
  name: string
  batch: boolean
  sources: number
  flows: FlowCount[]
  without_flow: number
  newest: number | null
  kind: string | null
}

export interface LibraryInfo {
  rows: LibraryRow[]
}

/* A cell's stage, read from the run's directory; null is no flow. */
export type Stage =
  | 'assigned'
  | 'tagged'
  | 'sheet'
  | 'draft'
  | 'approved'
  | 'rendered'
  | 'unreadable'

export interface HubCell {
  stage: Stage | null
  renders: number
  refusal: string | null
  /* Where stage ③ stands, where the cell has a sheet; null otherwise. */
  status: InputStatus | null
}

export interface HubSource {
  name: string
  digest: string | null
  width: number | null
  height: number | null
  cells: Record<string, HubCell>
  /* What the file carries beyond its pixels and orientation: empty once cleaned. */
  carries: string[]
}

export interface HubInfo {
  batch: string
  flows: string[]
  sources: HubSource[]
}

/* `window` is how many tokens SDXL's text encoders read at a time. It is declared
   in `isekai/pipeline/review.py` and sent here, so the browser decides nothing. */
export interface Budget {
  total: number
  per_field: Record<string, number>
  overhead: number
  window: number
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

/* How many images an approval renders, and the seeds it renders first. Seeds
   are decimal strings: a 64-bit seed is past what a number holds exactly. */
export interface Renders {
  count: number
  seeds: string[]
}

export interface InputDetail {
  /* The run's digest, which the URL names it by. */
  id: string
  run: string
  flow: string
  schema: string[]
  vocabulary: number
  width: number
  height: number
  caption: string | null
  /* The command that writes a missing caption, built by the server; null
     beside a caption. The browser never spells a command. */
  caption_command: string | null
  /* Null where the artifact is absent, which is never a failure: a run
     captioned before v0.20, a flow that declares no tagger, or a tagger that
     failed. The panel simply is not drawn. */
  wd14: ScoredTag[] | null
  tags: OfferedTag[] | null
  fields: Record<string, string[]>
  renders: Renders
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

/* What reading one uploaded file left in staging. `name` is what it is staged
   as: the file's own name, converted, or `<stem>-2`. */
export type StagedState = 'ready' | 'converted' | 'not cleaned' | 'skipped'

export interface StagedFile {
  name: string
  state: StagedState
  carries: string[]
}

export interface Committed {
  batch: string
  written: string[]
  skipped: string[]
  left_out: string[]
}

/* The one job slot: Prepare running, or the last one's end. */
/* A render's session as the job reports it: each step's state by name —
   `volume up`, `pod`, `teardown`, `volume down` — and each image as it lands. */
export interface RenderSession {
  started: string
  limit: number
  of: number
  keep_open: boolean
  steps: Record<string, string>
  images: { n: number; of: number; run: string; flow: string }[]
}

export interface JobSlot {
  kind: 'prepare' | 'render'
  batch: string
  state: 'running' | 'done' | 'stopped' | 'failed'
  flow: string | null
  stage: string | null
  /* Why a failed job ended, naming the batch's log; null otherwise. */
  message: string | null
  session?: RenderSession
}

/* What gpunit's records say may be billing: a pod with no session running, and
   the window volume — `open` until its end, `band` past it or unanswered. */
export interface Billing {
  pod: boolean
  volume: { state: 'open' | 'band'; ends: string | null } | null
}

export interface QuoteSource {
  name: string
  digest: string
  version: number | null
}

/* The Render dialog's quote: per flow what renders, what is left out and why,
   the estimate and limit in seconds, and the price in dollars. */
export interface Quote {
  flows: { flow: string; images: number; sources: (QuoteSource & { images: number })[] }[]
  left_out: (QuoteSource & { flow: string; reason: string })[]
  estimate: {
    seconds: number
    limit_s: number
    per_image: Record<string, number>
    boot_s: number
    teardown_s: number
    limit_factor: number
  }
  price: { about: number; at_most: number; keep_open: number }
  disabled: string | null
}

/* A stage's report about one cell, its stage read again from disk. */
export interface CellEvent {
  batch: string
  source: string
  flow: string
  stage: string
  state: 'start' | 'done' | 'refused'
  message: string | null
  cell: HubCell
}

export interface Assigned {
  cells: Record<string, HubCell>
  /* Each refused source's refusal, by its name. */
  refused: Record<string, string>
}
