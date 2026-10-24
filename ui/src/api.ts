/* The endpoints, in one module.

   A URL here is a contract between this app and `isekai/interface/ui/app.py` in
   the same repository. Every path inside a batch names the batch, and a run by
   the twelve-character digest its identifier begins with. */

import type {
  Assigned,
  Billing,
  Budget,
  Committed,
  Comparison,
  FieldCandidates,
  HubInfo,
  InputDetail,
  JobSlot,
  LibraryInfo,
  Quote,
  RenderDetail,
  RenderOffer,
  Renders,
  RendersInfo,
  ReviseRefused,
  RevisedDraft,
  RevisedImage,
  TagMatches,
} from './types'

/** One run in one flow of one batch: what a review URL names. */
export interface Place {
  batch: string
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

export function hub(batch: string): Promise<HubInfo> {
  return get<HubInfo>(`/api/b/${encodeURIComponent(batch)}/hub`)
}

/* A tick or an untick, for each named source; an untick past assigned is refused
   on its own, beside the cells that changed. */
export function assign(
  batch: string,
  sources: string[],
  flow: string,
  remove: boolean,
): Promise<Assigned> {
  return send(`/api/b/${encodeURIComponent(batch)}/assign`, 'POST', { sources, flow, remove })
}

export function prepare(batch: string): Promise<{ job: JobSlot }> {
  return send(`/api/b/${encodeURIComponent(batch)}/prepare`, 'POST', {})
}

export function stopJob(): Promise<{ job: JobSlot | null }> {
  return send('/api/job/stop', 'POST', {})
}

/* How many images a batch lacks, why Render is disabled or null, and why a count
   is refused or null; it prices nothing. */
export function renderOffer(batch: string): Promise<RenderOffer> {
  return get(`/api/b/${encodeURIComponent(batch)}/render`)
}

/* The quote rents nothing; only `startRender` does. */
export function quoteRender(batch: string): Promise<Quote> {
  return send(`/api/b/${encodeURIComponent(batch)}/render/quote`, 'POST', {})
}

/* Carries the limit and the images the dialog showed: a quote grown since is refused. */
export function startRender(
  batch: string,
  keepOpen: boolean,
  limitS: number,
  images: number,
): Promise<{ job: JobSlot }> {
  return send(`/api/b/${encodeURIComponent(batch)}/render`, 'POST', {
    keep_open: keepOpen,
    limit_s: limitS,
    images,
  })
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
  const [batch, digest, flow] = [place.batch, place.digest, place.flow].map(encodeURIComponent)
  return `/api/b/${batch}/review/${digest}/${flow}`
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
   a copy, whose draft is null; anything made from it, or a render running for
   the batch, refuses. */
export function cancelApproval(place: Place): Promise<{ draft: string | null }> {
  return send(`${at(place)}/cancel`, 'POST', {})
}

/* Deletes the waiting draft, as `review --discard` does; an approval refuses.
   `saved` is the draft's precondition, so the page deletes only the draft it
   last read: one another tab moved since answers 409. */
export function discardDraft(place: Place, saved: number | null): Promise<{ discarded: string }> {
  return send(`${at(place)}/discard`, 'POST', { saved })
}

/* Every image's draft, or none: a refusal answers each image, and is returned
   rather than thrown so the page can offer to deselect the refused. */
export function revise(
  batch: string,
  images: RevisedImage[],
): Promise<{ drafts: RevisedDraft[] } | ReviseRefused> {
  return send(`/api/b/${encodeURIComponent(batch)}/revise`, 'POST', { images }, {}, (body) =>
    'images' in body,
  )
}

export function photoUrl(place: Place): string {
  return `${at(place)}/photo`
}

/* An import: a staging folder the chosen files are read into, then committed
   into a batch's `sources/` in one move, or cancelled. */
export function openStaging(): Promise<{ id: string }> {
  return send('/api/staging', 'POST', {})
}

export function cancelStaging(id: string): Promise<unknown> {
  return request(`/api/staging/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export function commitStaging(
  id: string,
  batch: string,
  asIs: string[],
  add: boolean,
): Promise<Committed> {
  return send(`/api/staging/${encodeURIComponent(id)}/commit`, 'POST', {
    batch,
    as_is: asIs,
    add,
  })
}

/* A staged file's preview, by the name it is staged as. */
export function stagedThumbAt(id: string, name: string): string {
  return `/api/staging/${encodeURIComponent(id)}/files/${encodeURIComponent(name)}/thumb`
}

/* A source under a batch's `sources/`, by its file's name, with or without a run. */
export function sourceAt(batch: string, name: string): string {
  return `/api/b/${encodeURIComponent(batch)}/sources/${encodeURIComponent(name)}`
}

/* The source's thumbnail, upright. */
export function sourceThumbAt(batch: string, name: string): string {
  return `${sourceAt(batch, name)}/thumb`
}

export function renders(batch: string): Promise<RendersInfo> {
  return get<RendersInfo>(`/api/b/${encodeURIComponent(batch)}/renders`)
}

/* One image of a source in a flow: `version` is the approval's number. */
export interface RenderPlace {
  batch: string
  digest: string
  flow: string
  version: number
  seed: string
}

export function renderAt(place: RenderPlace): string {
  const [batch, ...rest] = [place.batch, place.digest, place.flow, `v${place.version}`, place.seed]
  return `/api/b/${encodeURIComponent(batch)}/renders/${rest.map(encodeURIComponent).join('/')}`
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

export function comparison(place: RenderPlace): Promise<Comparison> {
  return get<Comparison>(`${renderAt(place)}/compare`)
}
