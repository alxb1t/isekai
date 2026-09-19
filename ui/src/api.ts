/* The six endpoints, in one module.

   A URL here is a contract between this app and `isekai/interface/ui/app.py` in
   the same repository, which is why the flow is in none of the paths: the batch
   has exactly one and `/api/batch` names it. Widening that later is a
   find-and-replace, not a migration. */

import type { TagMatches } from './types'

async function get<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { refusal?: string }
    throw new Error(body.refusal ?? `${url} answered ${response.status}`)
  }
  return (await response.json()) as T
}

export function tags(fragment: string, limit: number): Promise<TagMatches> {
  const query = new URLSearchParams({ q: fragment, limit: String(limit) })
  return get<TagMatches>(`/api/tags?${query}`)
}

export function photoUrl(id: string): string {
  return `/api/inputs/${encodeURIComponent(id)}/photo`
}
