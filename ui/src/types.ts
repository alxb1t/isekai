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
  /* The first sources' names, in the hub's order: the row's thumbnails. */
  thumbs: string[]
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
  /* The last-written image of the newest version holding any; its seed a decimal string. */
  newest: { version: number; seed: string } | null
  /* How many images the newest approval lacks, as the render stage counts; null while unapproved. */
  short: number | null
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
  /* The approval a draft was copied from, its fields, and the seed of the image
     being revised; null for a draft of a sheet. */
  revision: Revision | null
  readonly: boolean
  draft: string | null
  approved: string | null
  saved: number | null
  approved_at: number | null
  /* Why *Cancel approve* is disabled, or null while it can run. */
  cancel: string | null
  budget: Budget
}

export interface Revision {
  version: number
  seed: string | null
  fields: Record<string, string[]>
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

/* One upload's name and state, as the page's stream reports it. */
export interface FileState {
  file: string
  state: 'waiting' | 'converting' | 'refused' | StagedState
  name?: string
  carries?: string[]
  refusal?: string
}

export interface Committed {
  batch: string
  written: string[]
  skipped: string[]
  left_out: string[]
}

/* One image a render session landed. The seed is a string: a 64-bit seed is past
   what a JavaScript number holds exactly. */
export interface SessionImage {
  digest: string
  flow: string
  version: number
  seed: string
}

/* A render session's record, `<batch>/sessions/<id>.json`, as the server reads
   it: `outcome` is null for a record still reading running whose render process no longer holds its lifetime lock. */
export interface SessionRecord {
  id: string
  started: string
  ended: string | null
  limit: number
  /* The images each flow was asked to render. */
  asked: Record<string, number>
  /* `pod` and `teardown`, each by its state. */
  steps: Record<string, string>
  images: SessionImage[]
  outcome: 'running' | 'done' | 'stopped' | 'failed' | null
  message: string | null
}

/* A running render discovered from disk, wherever it was started. */
export interface RunningSession {
  batch: string
  id: string
  started: string
}

/* The one job slot: Prepare running, or the last one's end. */
/* A render's session as the job reports it: its record's id, each step's state by
   name — `volume up`, `pod`, `teardown`, `volume down` — and each image as it lands. */
export interface RenderSession {
  id: string
  started: string
  /* When the job ended; null while it runs. */
  ended: string | null
  limit: number
  of: number
  steps: Record<string, string>
  images: SessionImage[]
}

export interface JobSlot {
  kind: 'prepare' | 'render'
  batch: string
  state: 'running' | 'done' | 'stopped' | 'failed'
  flow: string | null
  stage: string | null
  /* Why a failed job ended, naming the batch's log; null otherwise. */
  message: string | null
  progress?: { started: string; of: number; done: number }
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
  estimate: { seconds: number; limit_s: number; boot_s: number; teardown_s: number }
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

/* One approval of a source in a flow: when, its count and seeds, and the seeds
   rendered under it, each a decimal string as in `Renders`. An approval no hand
   can read carries its refusal in `damaged`, and no count. */
export interface RenderVersion {
  version: number
  at: number
  count: number | null
  seeds: string[]
  rendered: string[]
  damaged: string | null
  /* The version this one was copied from, and what changed: a field, or only
     the count and seeds. Null for an approval of a sheet. */
  came_from: number | null
  kind: 'revision' | 're-roll' | null
}

export interface RendersInfo {
  flows: string[]
  sources: {
    name: string
    digest: string | null
    /* How many images each flow's newest approval lacks, as the render stage counts. */
    ready: Record<string, number>
    cells: Record<string, RenderVersion[]>
  }[]
}

/* A batch's Render offer: the images it lacks, why Render is disabled, and why
   an approval's count is refused, each null when there is none. */
export interface RenderOffer {
  disabled: string | null
  images: number
  refused: string | null
}

/* An image's large view: the approval it was rendered from, filled fields only. */
export interface RenderDetail {
  flow: string
  version: number
  seed: string
  fields: Record<string, string[]>
  approved_at: number | null
  /* The version this one was copied from and what changed, as `RenderVersion`'s. */
  came_from: number | null
  kind: 'revision' | 're-roll' | null
  /* Null where the approval is damaged. */
  count: number | null
  seeds: string[]
  /* Why the approval's `renders` is refused, naming the file, or null. */
  damaged: string | null
  /* The newest older version that rendered this seed, or null. */
  compare: number | null
}

/* One image a revision names, its seed a decimal string. */
export interface RevisedImage {
  digest: string
  flow: string
  version: number
  seed: string
}

/* An image a revision wrote a draft for, by the draft's name. */
export interface RevisedDraft extends RevisedImage {
  draft: string
}

/* An image of a refused revision: its refusal, or null where it could be revised. */
export interface RefusedImage extends RevisedImage {
  refusal: string | null
}

/* A revision the server refused, answering each image. Nothing was written. */
export interface ReviseRefused {
  refusal: string
  images: RefusedImage[]
}

/* One side of a comparison. */
export interface CompareSide {
  version: number
  approved_at: number | null
  renders: Renders
  tokens: number
}

export interface Comparison {
  seed: string
  before: CompareSide
  after: CompareSide
  changed: { field: string; before: string[]; after: string[] }[]
}
