/* The six endpoints, in one module.

   A URL here is a contract between this app and `isekai/interface/ui/app.py` in
   the same repository, which is why the flow is in none of the paths: the batch
   has exactly one and `/api/batch` names it. Widening that later is a
   find-and-replace, not a migration. */

import type { BatchInfo, Budget, InputDetail, TagMatches } from './types'

async function get<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { refusal?: string }
    throw new Error(body.refusal ?? `${url} answered ${response.status}`)
  }
  return (await response.json()) as T
}

async function send<T>(url: string, method: string, body: unknown): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    const failed = (await response.json().catch(() => ({}))) as { refusal?: string }
    throw new Error(failed.refusal ?? `${url} answered ${response.status}`)
  }
  return (await response.json()) as T
}

export function tags(fragment: string, limit: number): Promise<TagMatches> {
  const query = new URLSearchParams({ q: fragment, limit: String(limit) })
  return get<TagMatches>(`/api/tags?${query}`)
}

export function batch(): Promise<BatchInfo> {
  return get<BatchInfo>('/api/batch')
}

export function inputDetail(id: string): Promise<InputDetail> {
  return get<InputDetail>(`/api/inputs/${encodeURIComponent(id)}`)
}

/* The whole draft, every time. There is no Save control on the page and no
   partial update here: a debounced PUT of everything is what makes the receipt
   the page shows true. */
export function saveDraft(
  id: string,
  fields: Record<string, string[]>,
): Promise<{ draft: string; saved: number; budget: Budget }> {
  return send(`/api/inputs/${encodeURIComponent(id)}/draft`, 'PUT', { fields })
}

export function approve(
  id: string,
): Promise<{ approved: string | null; warnings: string[]; at: number | null; count: number }> {
  return send(`/api/inputs/${encodeURIComponent(id)}/approve`, 'POST', {})
}

export function photoUrl(id: string): string {
  return `/api/inputs/${encodeURIComponent(id)}/photo`
}
