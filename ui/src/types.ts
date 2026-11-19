/* The shapes the endpoints return. One file, because a type that disagreed
   with `app.py` would be wrong in every component at once. */

import type { HubCell, ImportingState as StagedState, Renders, ReviewStatus as InputStatus } from './wire'

export type MarkKind = 'filled' | 'hollow' | 'dashed' | 'half' | 'ring'

export interface CollectionInput {
  /* The run's digest. */
  id: string
  name: string
  width: number
  height: number
  status: InputStatus
}

export type { FlowCount } from './wire'
export type { LibraryRow } from './wire'
export type { LibraryInfo } from './wire'
export type { LibraryStage as Stage } from './wire'

export type { HubCell } from './wire'
export type { HubSource } from './wire'
export type { HubInfo } from './wire'
export type { Assigned } from './wire'

export type { Budget } from './wire'
export type { ScoredTag } from './wire'
export type { OfferedTag } from './wire'
export type { FieldCandidates } from './wire'
export type { Renders } from './wire'
export type { InputDetail } from './wire'
export type { Revision } from './wire'
export type { Drafted } from './wire'
export type { TagMatch as VocabEntry } from './wire'
export type { TagMatches } from './wire'
export type { ReviewStatus as InputStatus } from './wire'
export type { DraftedImage } from './wire'
export type { RefusedImage } from './wire'
export type { DraftRefused } from './wire'

export type { ImportingState as StagedState } from './wire'
export type { FileState } from './wire'
export type { Committed } from './wire'

export interface StagedFile {
  name: string
  state: StagedState
  carries: string[]
  copyOf: string | null
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

/* The pairs the server proposes for a render, and the arm they lie on, `null` with no pair:
   each a point on the photograph and the point it matches on the render. */
export interface Proposal {
  arm: 'left' | 'right' | null
  pairs: Pair[]
}

export interface TattooList {
  tattoos: Tattoo[]
  limits: TattooLimits
  /* With a photograph's digest asked: the state of each tattoo placed on it, by name. */
  stage1?: Record<string, Stage1>
}

/* A bake's answer: the number of the edit it queued. */
export interface Baked {
  edit: number
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
