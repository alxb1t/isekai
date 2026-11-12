/* The shapes the endpoints return. One file, because a type that disagreed
   with `app.py` would be wrong in every component at once. */

export type MarkKind = 'filled' | 'hollow' | 'dashed' | 'half' | 'ring'

/* `re-opened` is approved *and* carrying a later draft -- the state
   `review --flow F --new-version` writes, and the only one in which an
   approved input is editable again. */
export type InputStatus = 'approved' | 're-opened' | 'draft'

export interface CollectionInput {
  /* The run's digest. */
  id: string
  name: string
  width: number
  height: number
  status: InputStatus
}

/* One flow's figures in a collection, out of the sources whose runs hold it. */
export interface FlowCount {
  flow: string
  approved: number
  rendered: number
  of: number
}

/* One folder of the library. A folder that is not a collection carries only its
   name: it is listed and never opened. `newest` is the server's clock. */
export interface LibraryRow {
  name: string
  collection: boolean
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
  /* Every approved version's images, oldest to newest; each seed a decimal string. */
  images: { version: number; seed: string }[]
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
  collection: string
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
   server sends only these: on v0.20's acceptance collection roughly nine in ten of
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
  /* For a draft or approval written from another flow's image: its own sheet's
     fields, and the number of its source copy; null for any other. */
  drafted: Drafted | null
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

export interface Drafted {
  fields: Record<string, string[]>
  /* The number its source copy is held under: the image it was drafted from. */
  version: number
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
   as: the file's own name, converted, or `<stem>-2`. A skipped file names in
   `copyOf` the staged file that holds its bytes. */
export type StagedState = 'ready' | 'converted' | 'not cleaned' | 'skipped'

export interface StagedFile {
  name: string
  state: StagedState
  carries: string[]
  copyOf: string | null
}

/* One upload's name and state, as the page's stream reports it. */
export interface FileState {
  file: string
  state: 'waiting' | 'converting' | 'refused' | StagedState
  name?: string
  carries?: string[]
  copy_of?: string | null
  refusal?: string
}

export interface Committed {
  collection: string
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

/* A render session's record, `<collection>/sessions/<id>.json`, as the server reads
   it: `outcome` is null for a record still reading running whose render process no longer holds its lifetime lock. */
export interface SessionRecord {
  id: string
  started: string
  ended: string | null
  limit: number
  /* The images each flow was asked to render. */
  asked: Record<string, number>
  /* The images planned for each run, by its digest, and flow; absent from an older record. */
  planned?: { digest: string; flow: string; images: number }[]
  /* `pod` and `teardown`, each by its state. */
  steps: Record<string, string>
  images: SessionImage[]
  outcome: 'running' | 'done' | 'stopped' | 'failed' | null
  message: string | null
}

/* A running render discovered from disk, wherever it was started. */
export interface RunningSession {
  collection: string
  collection_order?: string[]
  id: string
  started: string
}

/* A running render: its id, its start, and every collection holding its record. */
export interface RunningRender {
  collections: string[]
  id: string
  started: string
}

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

export type JobKind = 'prepare' | 'render'

/* One kind's job: running, or the last one's end. A render names every
   collection it renders in `collections`, `collection` first. */
export interface JobSlot {
  kind: JobKind
  collection: string
  collections?: string[]
  state: 'running' | 'done' | 'stopped' | 'failed'
  flow: string | null
  stage: string | null
  /* Why a failed job ended, naming the collection's log; null otherwise. */
  message: string | null
  progress?: { started: string; stages: StageCount[] }
  session?: RenderSession
}

/* One Prepare stage's cells done, against the cells it was asked to run. */
export interface StageCount {
  stage: string
  done: number
  of: number
}

/* Each kind's slot: its job, running or ended, or null. */
export type JobSlots = Record<JobKind, JobSlot | null>

/* What gpunit's records say may be billing: a pod with no session running, and
   the window volume — `open` until its end, `band` past it or unanswered. */
export interface Billing {
  pod: boolean
  volume: { state: 'open' | 'band'; ends: string | null } | null
}

export interface QuoteSource {
  name: string
  digest: string
  run: string
  version: number | null
}

/* A photograph the Render dialog takes out of its quote: its run's flow. */
export interface TakenOut {
  collection: string
  run: string
  flow: string
}

/* A queued bake in a quote: its photograph's run and flow, the approval's version, the
   seed as text and the edit's number. */
export interface QuoteBake extends QuoteSource {
  flow: string
  version: number
  seed: string
  k: number
}

/* One collection's row of a quote: per flow what renders, its queued bakes, and a count
   it refuses, or null. */
export interface QuotedCollection {
  collection: string
  images: number
  flows: { flow: string; images: number; sources: (QuoteSource & { images: number })[] }[]
  bakes: QuoteBake[]
  refused: string | null
}

/* The Render dialog's quote: a row per collection, one session's estimate and
   limit in seconds against `gpunit.toml`'s ceiling, and the price in dollars. */
export interface Quote {
  collections: QuotedCollection[]
  estimate: { seconds: number; limit_s: number; boot_s: number; teardown_s: number }
  price: { about: number; at_most: number; keep_open: number }
  ceiling_s: number
  disabled: string | null
}

/* A stage's report about one cell, its stage read again from disk. */
export interface CellEvent {
  collection: string
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

/* A collection's Render offer: the images and the queued bakes it holds and every other
   collection holds, why Render is disabled, and why an approval's count is refused, each
   null when there is none. */
export interface RenderOffer {
  disabled: string | null
  images: number
  others: number
  bakes: number
  other_bakes: number
  refused: string | null
}

/* One edit request of a render's seed: `placed_on` is the number of the bake whose image it
   edits, null for the render's own; `baked_at` the image's time, null while queued; `edit` its
   name, and `reason` the refusal naming the file of a damaged record, each null otherwise. */
export interface Bake {
  k: number
  state: 'baked' | 'queued' | 'damaged'
  placed_on: number | null
  baked_at: number | null
  edit: string | null
  reason: string | null
}

/* An image's large view: the approval it was rendered from, filled fields only. */
export interface RenderDetail {
  flow: string
  version: number
  seed: string
  fields: Record<string, string[]>
  approved_at: number | null
  /* The version this one was copied from, and what changed: a field, or only
     the count and seeds. Null for an approval of a sheet. */
  came_from: number | null
  kind: 'revision' | 're-roll' | null
  /* Null where the approval is damaged. */
  count: number | null
  seeds: string[]
  /* Why the approval's `renders` is refused, naming the file, or null. */
  damaged: string | null
  /* The newest older version that rendered this seed, or null. */
  compare: number | null
  /* The source's images, a row per offered flow holding any, each oldest version
     first, then by seed. */
  source: { flow: string; images: { version: number; seed: string }[] }[]
  /* Every offered flow, this one first, assigned or not. */
  targets: string[]
  /* The seed's bakes by number, each with what it was placed on. */
  bakes: Bake[]
}

/* One image a draft is written from, its seed a decimal string. */
export interface ImageRef {
  digest: string
  flow: string
  version: number
  seed: string
}

/* An image a draft answered: the draft it wrote, or the edited draft already
   waiting in the target, by name; the other is null. */
export interface DraftedImage extends ImageRef {
  draft: string | null
  waiting: string | null
}

/* An image of a refused draft: its refusal, or null where it could be drafted. */
export interface RefusedImage extends ImageRef {
  refusal: string | null
}

/* A draft the server refused, answering each image. Nothing was written. */
export interface DraftRefused {
  refusal: string
  images: RefusedImage[]
}

/* A point in an image's own pixels, `[x, y]`; a cut's image is its photograph. */
export type Point = [number, number]

/* A kept tattoo. `kind` is `image` for an upload and `cut` for a tattoo with no image of
   its own; `cut_from` is a cut's run digest, `downscaled_from` an upload's first size. */
export interface Tattoo {
  name: string
  kind: 'image' | 'cut'
  size: [number, number]
  /* When it was kept: an ISO time in UTC. */
  kept: string
  outlined: boolean
  downscaled_from: [number, number] | null
  cut_from: string | null
}

/* A tattoo's outline and ink tone as the server keeps them; `white` is a scale on the
   automatic white point, 1 being automatic. */
export interface Outline {
  points: Point[]
  closed: boolean
  white: number
  neutral: boolean
  depth: number
}

/* The bounds the page and the server both read. */
export interface TattooLimits {
  long_side: number
  outline_min: number
  outline_max: number
  depth_min: number
  depth_max: number
  /* The depth a cut and an upload start at, which *Reset* returns to. */
  photo_depth: number
  image_depth: number
  /* The pairs a stage goes forward with, and the least a preview is asked with. */
  floor_stage1: number
  floor_stage2: number
  floor_direct: number
  preview_floor: number
  /* The preview's crop margin in pixels, and the wait after the last change in ms. */
  preview_margin: number
  preview_wait_ms: number
  /* The selection radius in screen pixels, and the least points of a limb or exclusion. */
  pair_radius: number
  region_min: number
}

/* A tattoo point and the point it matches on the other image: `[a, b]`, `a` first. */
export type Pair = [Point, Point]

/* A tattoo's pairs with one photograph, and whether it is *not on this photo*. */
export interface Stage1 {
  pairs: Pair[]
  not_on_photo: boolean
}

export interface TattooList {
  tattoos: Tattoo[]
  limits: TattooLimits
  /* With a photograph's digest asked: the state of each tattoo placed on it, by name. */
  stage1?: Record<string, Stage1>
}

/* The placement preview: the ink on white as a JPEG, its crop in the target's pixels,
   and the automatic white point as a grey from 0 to 255. */
export interface Preview {
  image: Blob
  box: { x: number; y: number; width: number; height: number }
  white: number
}

/* The ink on an outline's crop: a JPEG, its box in the image's pixels, and the
   automatic white point as a grey from 0 to 255. */
export interface InkView {
  image: Blob
  box: { x: number; y: number; width: number; height: number }
  white: number
}

/* One side of a comparison: a render, headed by its flow, version and seed. */
export interface CompareSide {
  flow: string
  version: number
  seed: string
  approved_at: number | null
  renders: Renders
  tokens: number
}

/* The image picked, left — a render, or the photograph where null — beside the
   render compare started from, right. */
export interface Comparison {
  left: CompareSide | null
  right: CompareSide
}
