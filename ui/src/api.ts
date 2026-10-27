/* The endpoints, in one module.

   A URL here is a contract between this app and `isekai/interface/ui/app.py` in
   the same repository. Every path inside a collection names the collection, and a run by
   the twelve-character digest its identifier begins with. */

import type {
  Assigned,
  Billing,
  Budget,
  Committed,
  Comparison,
  DraftedImage,
  DraftRefused,
  FieldCandidates,
  HubInfo,
  ImageRef,
  InputDetail,
  JobKind,
  JobSlot,
  LibraryInfo,
  Quote,
  RenderDetail,
  RenderOffer,
  Renders,
  RendersInfo,
  SessionRecord,
  RunningSession,
  TagMatches,
} from './types'

/** One run in one flow of one collection: what a review URL names. */
export interface Place {
  collection: string
  digest: string
  flow: string
}

/* One place where a `Refusal` stops being HTTP and becomes an error carrying the
   pipeline's own string. `app.py` answers every refusal the same way, so this
   unwraps it the same way for every verb. */
async function request<T>(
  url: string,
  init?: RequestInit,
  answers?: (body: object) => boolean,
): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { refusal?: string }
    // A refusal that answers the request, as a revision's per-image one does.
    if (answers?.(body)) return body as T
    throw new Error(body.refusal ?? `${url} answered ${response.status}`)
  }
  return (await response.json()) as T
}

function get<T>(url: string): Promise<T> {
  return request<T>(url)
}

function send<T>(
  url: string,
  method: string,
  body: unknown,
  init: RequestInit = {},
  answers?: (body: object) => boolean,
): Promise<T> {
  return request<T>(
    url,
    { ...init, method, headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) },
    answers,
  )
}

export function tags(fragment: string, limit: number): Promise<TagMatches> {
  const query = new URLSearchParams({ q: fragment, limit: String(limit) })
  return get<TagMatches>(`/api/tags?${query}`)
}

export function library(): Promise<LibraryInfo> {
  return get<LibraryInfo>('/api/library')
}

export function hub(collection: string): Promise<HubInfo> {
  return get<HubInfo>(`/api/c/${encodeURIComponent(collection)}/hub`)
}

/* A tick or an untick, for each named source; an untick past assigned is refused
   on its own, beside the cells that changed. */
export function assign(
  collection: string,
  sources: string[],
  flow: string,
  remove: boolean,
): Promise<Assigned> {
  return send(`/api/c/${encodeURIComponent(collection)}/assign`, 'POST', { sources, flow, remove })
}

export function prepare(collection: string): Promise<{ job: JobSlot }> {
  return send(`/api/c/${encodeURIComponent(collection)}/prepare`, 'POST', {})
}

export function stopJob(kind: JobKind): Promise<{ job: JobSlot }> {
  return send(`/api/jobs/${kind}/stop`, 'POST', {})
}

/* How many images a collection lacks, why Render is disabled or null, and why a count
   is refused or null; it prices nothing. */
export function renderOffer(collection: string): Promise<RenderOffer> {
  return get(`/api/c/${encodeURIComponent(collection)}/render`)
}

/* One session's quote over `collections`, or, with none named, every collection
   short of images. It rents nothing; only `startRender` does. */
export function quoteRender(collections?: string[]): Promise<Quote> {
  return send('/api/render/quote', 'POST', collections ? { collections } : {})
}

/* Carries the limit and the images the dialog showed: a quote grown since is refused. */
export function startRender(
  collections: string[],
  keepOpen: boolean,
  limitS: number,
  images: number,
): Promise<{ job: JobSlot }> {
  return send('/api/render', 'POST', {
    collections,
    keep_open: keepOpen,
    limit_s: limitS,
    images,
  })
}

/* Live disk records across the library, including renders started in a terminal. */
export function runningSessions(): Promise<{ sessions: RunningSession[] }> {
  return get('/api/sessions/running')
}

/* One render session's record; an id no record holds is refused. */
export function session(collection: string, id: string): Promise<SessionRecord> {
  return get(`/api/c/${encodeURIComponent(collection)}/sessions/${encodeURIComponent(id)}`)
}

/* Ask gpunit again; an alert clears only when its records say gone. */
export function checkBilling(): Promise<{ billing: Billing }> {
  return send('/api/billing/check', 'POST', {})
}

/* The whole table for one flow, once, the first time the reference is opened.
   Tens of kilobytes, so the filter is instant with no round trip per keystroke. */
export function fieldCandidates(flow: string): Promise<FieldCandidates> {
  return get<FieldCandidates>(`/api/fields?${new URLSearchParams({ flow })}`)
}

function at(place: Place): string {
  const [collection, digest, flow] = [place.collection, place.digest, place.flow].map(encodeURIComponent)
  return `/api/c/${collection}/review/${digest}/${flow}`
}

export function inputDetail(place: Place): Promise<InputDetail> {
  return get<InputDetail>(at(place))
}

/* The whole draft, every time. There is no Save control on the page and no
   partial update here: a debounced PUT of everything is what makes the receipt
   the page shows true.

   `saved` is the receipt this page last received, echoed back as a precondition:
   the server compares it to the draft's own mtime and answers 409 on a mismatch.
   It is the only monotonic fact on disk -- the draft carries no timestamp, no
   revision counter and no digest. Kept alive, so the flush a leaving page starts
   outlives the page. */
export function saveDraft(
  place: Place,
  fields: Record<string, string[]>,
  renders: Renders,
  saved: number | null,
): Promise<{ draft: string; saved: number; budget: Budget }> {
  return send(`${at(place)}/draft`, 'PUT', { fields, renders, saved }, { keepalive: true })
}

/* `saved` is the precondition the draft's `PUT` states, so the page approves
   only the draft it last read: one another tab moved since answers 409. */
export function approve(
  place: Place,
  saved: number | null,
): Promise<{ approved: string | null; warnings: string[]; at: number | null }> {
  return send(`${at(place)}/approve`, 'POST', { saved })
}

/* Turns the approval back into its draft, as `approve --cancel` does, or deletes
   a copy; `back` names what the flow is left on, a draft or the approval beneath
   a copy, null where nothing is. Anything made from it, or a render running for
   the collection, refuses. */
export function cancelApproval(place: Place): Promise<{ back: string | null }> {
  return send(`${at(place)}/cancel`, 'POST', {})
}

/* Deletes the waiting draft, as `review --discard` does; an approval refuses.
   `saved` is the draft's precondition, so the page deletes only the draft it
   last read: one another tab moved since answers 409. */
export function discardDraft(place: Place, saved: number | null): Promise<{ discarded: string }> {
  return send(`${at(place)}/discard`, 'POST', { saved })
}

/* Drafts `flow` from every image, as `draft --flow` does: an image's own flow a
   revision, another from its approval. Each image's draft, written or an edited
   one already waiting, or none: a refusal answers each image, and is returned
   rather than thrown so the page can offer to deselect the refused. */
export function draft(
  collection: string,
  flow: string,
  images: ImageRef[],
): Promise<{ drafts: DraftedImage[] } | DraftRefused> {
  return send(
    `/api/c/${encodeURIComponent(collection)}/draft`,
    'POST',
    { flow, images },
    {},
    (body) => 'images' in body,
  )
}

export function photoUrl(place: Place): string {
  return `${at(place)}/photo`
}

/* An import: a staging folder the chosen files are read into, then committed
   into a collection's `sources/` in one move, or cancelled. */
export function openStaging(): Promise<{ id: string }> {
  return send('/api/staging', 'POST', {})
}

export function cancelStaging(id: string): Promise<unknown> {
  return request(`/api/staging/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export function commitStaging(
  id: string,
  collection: string,
  asIs: string[],
  add: boolean,
): Promise<Committed> {
  return send(`/api/staging/${encodeURIComponent(id)}/commit`, 'POST', {
    collection,
    as_is: asIs,
    add,
  })
}

/* A staged file's preview, by the name it is staged as. */
export function stagedThumbAt(id: string, name: string): string {
  return `/api/staging/${encodeURIComponent(id)}/files/${encodeURIComponent(name)}/thumb`
}

/* A source under a collection's `sources/`, by its file's name, with or without a run. */
export function sourceAt(collection: string, name: string): string {
  return `/api/c/${encodeURIComponent(collection)}/sources/${encodeURIComponent(name)}`
}

/* The source's thumbnail, upright. */
export function sourceThumbAt(collection: string, name: string): string {
  return `${sourceAt(collection, name)}/thumb`
}

export function renders(collection: string): Promise<RendersInfo> {
  return get<RendersInfo>(`/api/c/${encodeURIComponent(collection)}/renders`)
}

/* One image of a source in a flow: `version` is the approval's number. */
export interface RenderPlace {
  collection: string
  digest: string
  flow: string
  version: number
  seed: string
}

/** Return the number an address's version spells. e.g. "v2" -> 2 */
export const versionOf = (version: string) => Number(version.replace(/^v/, ''))

export function renderAt(place: RenderPlace): string {
  const [collection, ...rest] = [place.collection, place.digest, place.flow, `v${place.version}`, place.seed]
  return `/api/c/${encodeURIComponent(collection)}/renders/${rest.map(encodeURIComponent).join('/')}`
}

export function thumbAt(place: RenderPlace): string {
  return `${renderAt(place)}/thumb`
}

export function imageAt(place: RenderPlace): string {
  return `${renderAt(place)}/image`
}

export function renderDetail(place: RenderPlace): Promise<RenderDetail> {
  return get<RenderDetail>(renderAt(place))
}

/** Return `place` beside `other`, another image of its cell, else the newest older of its seed. */
export function comparison(
  place: RenderPlace,
  other?: { version: number; seed: string },
): Promise<Comparison> {
  const pair = other ? `/v${other.version}/${encodeURIComponent(other.seed)}` : ''
  return get<Comparison>(`${renderAt(place)}/compare${pair}`)
}
