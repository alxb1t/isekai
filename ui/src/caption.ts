/* What a caption's prose is, as the page reads it.

   Stated once because two components render it: the source column's panel and
   the photo overlay beside the enlarged photograph. A paragraph rule that lived
   in both could only drift. */

export function paragraphsOf(prose: string | null): string[] {
  return (prose ?? '')
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
}

export function wordsOf(prose: string | null): number {
  return (prose ?? '').split(/\s+/).filter(Boolean).length
}
