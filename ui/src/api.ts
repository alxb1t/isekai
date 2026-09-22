/* The seven endpoints, in one module.

   A URL here is a contract between this app and `isekai/interface/ui/app.py` in
   the same repository, which is why the flow is in none of the paths: the batch
   has exactly one and `/api/batch` names it. Widening that later is a
   find-and-replace, not a migration. */

import type {
  BatchInfo,
  Budget,
  FieldCandidates,
  InputDetail,
  TagMatches,
} from './types'

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

function send<T>(url: string, method: string, body: unknown): Promise<T> {
  return request<T>(url, {
    method,
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function tags(fragment: string, limit: number): Promise<TagMatches> {
  const query = new URLSearchParams({ q: fragment, limit: String(limit) })
  return get<TagMatches>(`/api/tags?${query}`)
}

export function batch(): Promise<BatchInfo> {
  return get<BatchInfo>('/api/batch')
}

/* The whole table, once, the first time the reference is opened. Tens of
   kilobytes, so the filter is instant with no round trip per keystroke — and a
   sitting that never opens it pays nothing, because this is not on `/api/batch`'s
   payload. */
export function fieldCandidates(): Promise<FieldCandidates> {
  return get<FieldCandidates>('/api/fields')
}

export function inputDetail(id: string): Promise<InputDetail> {
  return get<InputDetail>(`/api/inputs/${encodeURIComponent(id)}`)
}

/* The whole draft, every time. There is no Save control on the page and no
   partial update here: a debounced PUT of everything is what makes the receipt
   the page shows true. */
/* `saved` is the receipt this page last received, echoed back as a precondition:
   the server compares it to the draft's own mtime and answers 409 on a mismatch.
   It is the only monotonic fact on disk -- the draft carries no timestamp, no
   revision counter and no digest. */
export function saveDraft(
  id: string,
  fields: Record<string, string[]>,
  saved: number | null,
): Promise<{ draft: string; saved: number; budget: Budget }> {
  return send(`/api/inputs/${encodeURIComponent(id)}/draft`, 'PUT', { fields, saved })
}

export function approve(
  id: string,
): Promise<{ approved: string | null; warnings: string[]; at: number | null }> {
  return send(`/api/inputs/${encodeURIComponent(id)}/approve`, 'POST', {})
}

export function photoUrl(id: string): string {
  return `/api/inputs/${encodeURIComponent(id)}/photo`
}
