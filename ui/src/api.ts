/* The endpoints, in one module.

   A URL here is a contract between this app and `isekai/interface/ui/app.py` in
   the same repository. Every path inside a batch names the batch, and a run by
   the twelve-character digest its identifier begins with. */

import type {
  Budget,
  Committed,
  FieldCandidates,
  HubInfo,
  InputDetail,
  LibraryInfo,
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
async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { refusal?: string }
    throw new Error(body.refusal ?? `${url} answered ${response.status}`)
  }
  return (await response.json()) as T
}

function get<T>(url: string): Promise<T> {
  return request<T>(url)
}

function send<T>(url: string, method: string, body: unknown, init: RequestInit = {}): Promise<T> {
  return request<T>(url, {
    ...init,
    method,
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
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
  saved: number | null,
): Promise<{ draft: string; saved: number; budget: Budget }> {
  return send(`${at(place)}/draft`, 'PUT', { fields, saved }, { keepalive: true })
}

/* `saved` is the precondition the draft's `PUT` states, so the page approves
   only the draft it last read: one another tab moved since answers 409. */
export function approve(
  place: Place,
  saved: number | null,
): Promise<{ approved: string | null; warnings: string[]; at: number | null }> {
  return send(`${at(place)}/approve`, 'POST', { saved })
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
