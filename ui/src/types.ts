/* The shapes the endpoints return. One file, because a type that disagreed
   with `app.py` would be wrong in every component at once. */

import type {
  HubCell,
  ImportingState as StagedState,
  Job,
  JobsKind,
  Renders,
  ReviewStatus as InputStatus,
  Outline as WireOutline,
  Proposed,
  SessionImage,
  Stage1 as WireStage1,
  Tattoo as WireTattoo,
  Tattoos,
} from './wire'

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

export type { SessionImage } from './wire'
export type { JobSession as RenderSession } from './wire'
export type { JobsKind as JobKind } from './wire'
export type { Job as JobSlot } from './wire'
export type { JobStage as StageCount } from './wire'

export type { QuotedBake as QuoteBake } from './wire'
export type { QuotedRow as QuotedCollection } from './wire'
export type { Quote } from './wire'
export type { RenderOffer } from './wire'

export type { RenderDetail } from './wire'
export type { Bake } from './wire'
export type { BakeQueued as Baked } from './wire'

export type { TattooLimits } from './wire'
export type { CompareSide } from './wire'
export type { Comparison } from './wire'

export interface StagedFile {
  name: string
  state: StagedState
  carries: string[]
  copyOf: string | null
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

/* Each kind's slot: its job, running or ended, or null. */
export type JobSlots = Record<JobsKind, Job | null>

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

/* One image a draft is written from, its seed a decimal string. */
export interface ImageRef {
  digest: string
  flow: string
  version: number
  seed: string
}

/* A point in an image's own pixels, `[x, y]`; a cut's image is its photograph. */
export type Point = [number, number]

export interface Tattoo extends Omit<WireTattoo, 'size' | 'downscaled_from'> {
  size: [number, number]
  downscaled_from: [number, number] | null
}

export interface Outline extends Omit<WireOutline, 'points'> {
  points: Point[]
}

/* A tattoo point and the point it matches on the other image: `[a, b]`, `a` first. */
export type Pair = [Point, Point]

export interface Stage1 extends Omit<WireStage1, 'pairs'> {
  pairs: Pair[]
}

export interface Proposal extends Omit<Proposed, 'pairs'> {
  pairs: Pair[]
}

export interface TattooList extends Omit<Tattoos, 'tattoos' | 'stage1'> {
  tattoos: Tattoo[]
  stage1: Record<string, Stage1>
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
