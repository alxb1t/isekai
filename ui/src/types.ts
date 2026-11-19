/* The page's names for the wire: the re-exports of `wire.ts`, the overlays that
   narrow a pair, and the types only the page holds. */

import type {
  ImportingState as StagedState,
  Job,
  JobsKind,
  ReviewStatus as InputStatus,
  Outline as WireOutline,
  Proposed,
  QuotedSource,
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

export type { ServedSession as SessionRecord } from './wire'
export type { RunningSession } from './wire'

/* A running render: its id, its start, and every collection holding its record. */
export interface RunningRender {
  collections: string[]
  id: string
  started: string
}

/* Each kind's slot: its job, running or ended, or null. */
export type JobSlots = Record<JobsKind, Job | null>

export type { Billing } from './wire'

export type QuoteSource = Omit<QuotedSource, 'images'>

/* A photograph the Render dialog takes out of its quote: its run's flow. */
export interface TakenOut {
  collection: string
  run: string
  flow: string
}

export type { CellEvent } from './wire'

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
