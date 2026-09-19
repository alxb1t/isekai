/* The six endpoints, in one module.

   A URL here is a contract between this app and `isekai/interface/ui/app.py` in
   the same repository, which is why the flow is in none of the paths: the batch
   has exactly one and `/api/batch` names it. Widening that later is a
   find-and-replace, not a migration. */

export function photoUrl(id: string): string {
  return `/api/inputs/${encodeURIComponent(id)}/photo`
}
