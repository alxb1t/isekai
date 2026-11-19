/* Written by `tools/derive_wire.py` from `isekai/interface/ui/shapes.py`. */

export type ImportingState = 'ready' | 'converted' | 'not cleaned' | 'skipped'
export type ImportingUpload = ImportingState | 'waiting' | 'converting' | 'refused'
export type JobsKind = 'prepare' | 'render'
export type JobsState = 'running' | 'failed' | 'stopped' | 'done'
export type LibraryStage = 'assigned' | 'tagged' | 'sheet' | 'draft' | 'approved' | 'rendered' | 'unreadable'
export type ProposalSide = 'left' | 'right'
export type ReviewStatus = 'draft' | 'approved' | 're-opened'
export type TattoosKind = 'image' | 'cut'

export interface SchemaBlock {
  name: string
  version: number
}

export interface SessionImage {
  digest: string
  flow: string
  version: number
  seed: string
}

export interface SessionPlan {
  digest: string
  flow: string
  images: number
}

export interface SessionRecord {
  schema: SchemaBlock
  id: string
  started: string
  ended: string | null
  limit: number
  asked: Record<string, number>
  planned?: SessionPlan[]
  collections?: string[]
  collection_order?: string[]
  steps: Record<string, string>
  images: SessionImage[]
  outcome: string
  message: string | null
}

export interface FlowCount {
  flow: string
  approved: number
  rendered: number
  of: number
}

export interface LibraryRow {
  name: string
  collection: boolean
  sources: number
  thumbs: string[]
  flows: FlowCount[]
  without_flow: number
  newest: number | null
  kind: string | null
}

export interface LibraryInfo {
  rows: LibraryRow[]
}

export interface CellImage {
  version: number
  seed: string
}

export interface HubCell {
  stage: LibraryStage | null
  renders: number
  refusal: string | null
  status: ReviewStatus | null
  newest: CellImage | null
  short: number | null
  images: CellImage[]
}

export interface HubSource {
  name: string
  digest: string | null
  width: number | null
  height: number | null
  cells: Record<string, HubCell>
  carries: string[]
}

export interface HubInfo {
  collection: string
  flows: string[]
  sources: HubSource[]
}

export interface Assigned {
  cells: Record<string, HubCell>
  refused: Record<string, string>
}

export interface Opened {
  id: string
}

export interface Uploaded {
  upload: string
  file: string
  state: 'waiting'
}

export type Empty = Record<string, never>

export interface Committed {
  collection: string
  written: string[]
  skipped: string[]
  left_out: string[]
}

export interface TagMatch {
  tag: string
  posts: number
  rare: boolean
}

export interface TagMatches {
  matches: TagMatch[]
  total: number
}

export interface OfferedTag {
  tag: string
  posts: number
}

export interface FieldCandidates {
  fields: Record<string, OfferedTag[]>
}

export interface Renders {
  count: number
  seeds: string[]
}

export interface Bake {
  k: number
  placed_on: number | null
  baked_at: number | null
  edit: string | null
  state: 'baked' | 'queued' | 'damaged'
  reason: string | null
}

export interface SourceImages {
  flow: string
  images: CellImage[]
}

export interface RenderDetail {
  flow: string
  version: number
  seed: string
  fields: Record<string, string[]>
  approved_at: number | null
  came_from: number | null
  kind: 'revision' | 're-roll' | null
  count: number | null
  seeds: string[]
  damaged: string | null
  bakes: Bake[]
  compare: number | null
  targets: string[]
  source: SourceImages[]
}

export interface CompareSide {
  flow: string
  version: number
  approved_at: number | null
  renders: Renders
  tokens: number
  seed: string
}

export interface Comparison {
  left: CompareSide | null
  right: CompareSide
}

export interface Deleted {
  deleted: boolean
}

export interface Budget {
  total: number
  per_field: Record<string, number>
  overhead: number
  window: number
}

export interface ScoredTag {
  tag: string
  confidence: number
}

export interface Revision {
  version: number
  seed: string | null
  fields: Record<string, string[]>
}

export interface Drafted {
  fields: Record<string, string[]>
  version: number
}

export interface InputDetail {
  id: string
  run: string
  flow: string
  schema: string[]
  vocabulary: number
  width: number
  height: number
  caption: string | null
  caption_command: string | null
  wd14: ScoredTag[] | null
  tags: OfferedTag[] | null
  fields: Record<string, string[]>
  renders: Renders
  revision: Revision | null
  drafted: Drafted | null
  readonly: boolean
  draft: string | null
  approved: string | null
  saved: number | null
  approved_at: number | null
  cancel: string | null
  budget: Budget
}

export interface DraftSaved {
  draft: string
  saved: number
  budget: Budget
}

export interface Approval {
  approved: string | null
  warnings: string[]
  at: number | null
}

export interface Cancellation {
  back: string | null
  cancelled: boolean
}

export interface Discarded {
  discarded: string
}

export interface DraftedImage {
  digest: string
  flow: string
  version: number
  seed: string
  draft: string | null
  waiting: string | null
}

export interface Drafts {
  drafts: DraftedImage[]
}

export interface Tattoo {
  name: string
  kind: TattoosKind
  size: number[]
  kept: string
  outlined: boolean
  downscaled_from: number[] | null
  cut_from: string | null
}

export interface Outline {
  points: number[][]
  closed: boolean
  white: number
  neutral: boolean
  depth: number
}

export interface OutlinedTattoo extends Tattoo {
  outline: Outline
}

export interface TattooLimits {
  long_side: number
  outline_min: number
  outline_max: number
  floor_stage1: number
  floor_stage2: number
  floor_direct: number
  preview_floor: number
  preview_margin: number
  preview_wait_ms: number
  pair_radius: number
  region_min: number
  depth_min: number
  depth_max: number
  photo_depth: number
  image_depth: number
}

export interface Stage1 {
  pairs: number[][][]
  not_on_photo: boolean
}

export interface Tattoos {
  tattoos: Tattoo[]
  limits: TattooLimits
  stage1: Record<string, Stage1>
}

export interface BakeQueued {
  edit: number
}

export interface Proposed {
  arm: ProposalSide | null
  pairs: number[][][]
}

export interface RenderOffer {
  disabled: string | null
  images: number
  others: number
  bakes: number
  other_bakes: number
  refused: string | null
}

export interface QuotedSource {
  name: string
  digest: string
  run: string
  version: number | null
  images: number
}

export interface QuotedFlow {
  flow: string
  images: number
  sources: QuotedSource[]
}

export interface QuotedBake {
  flow: string
  name: string
  digest: string
  run: string
  version: number
  seed: string
  k: number
}

export interface QuotedRow {
  collection: string
  images: number
  flows: QuotedFlow[]
  bakes: QuotedBake[]
  refused: string | null
}

export interface QuoteEstimate {
  seconds: number
  limit_s: number
  boot_s: number
  teardown_s: number
}

export interface QuotePrice {
  about: number
  at_most: number
  keep_open: number
}

export interface Quote {
  collections: QuotedRow[]
  estimate: QuoteEstimate
  price: QuotePrice
  ceiling_s: number
  disabled: string | null
}

export interface BillingVolume {
  state: string
  ends: string | null
}

export interface Billing {
  pod: boolean
  volume: BillingVolume | null
}

export interface BillingChecked {
  billing: Billing
}

export interface JobStage {
  stage: string
  done: number
  of: number
}

export interface JobProgress {
  started: string
  stages: JobStage[]
}

export interface JobSession {
  id: string
  started: string
  limit: number
  of: number
  ended: string | null
  steps: Record<string, string>
  images: SessionImage[]
}

export interface Job {
  kind: JobsKind
  collection: string
  state: JobsState
  flow: string | null
  stage: string | null
  message: string | null
  progress?: JobProgress
  collections?: string[]
  session?: JobSession
}

export interface JobStarted {
  job: Job
}

export interface ServedSession {
  schema: SchemaBlock
  id: string
  started: string
  ended: string | null
  limit: number
  asked: Record<string, number>
  planned?: SessionPlan[]
  collections?: string[]
  collection_order?: string[]
  steps: Record<string, string>
  images: SessionImage[]
  outcome: string | null
  message: string | null
}

export interface RunningSession extends SessionRecord {
  collection: string
}

export interface RunningSessions {
  sessions: RunningSession[]
}

export interface RefusedImage {
  digest: string
  flow: string
  version: number
  seed: string
  refusal: string | null
}

export interface Refused {
  refusal: string
}

export interface DraftRefused extends Refused {
  images: RefusedImage[]
}

export interface FileState {
  file: string
  state: ImportingUpload
  name?: string
  carries?: string[]
  copy_of?: string | null
  refusal?: string
}

export interface FileEvent extends FileState {
  staging: string
  upload: string
}

export interface Snapshot {
  jobs: Record<JobsKind, Job | null>
  billing: Billing
  hub?: HubInfo
  files?: Record<string, FileState>
}

export interface CellEvent {
  collection: string
  source: string
  flow: string
  stage: string | null
  state: string | null
  message: string | null
  cell: HubCell
}

export interface Events {
  snapshot: Snapshot
  job: Job
  billing: Billing
  cell: CellEvent
  file: FileEvent
}
