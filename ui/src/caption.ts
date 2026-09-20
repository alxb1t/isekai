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

/* One sentence to a block, which is the whole of ④.

   Split on sentence-ending punctuation followed by whitespace, keeping the
   punctuation with the sentence it ends. **Naive against abbreviations, and
   knowingly so**: the prose this renders is constrained by briefing to plain
   description of a person, so "Dr." and "e.g." are not the register it is
   written in. The edge is named in the acceptance rather than guarded against
   here, because a guard would be a list of exceptions nobody can test. */
export function sentencesOf(prose: string | null): string[] {
  return (prose ?? '')
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean)
}

export function wordsOf(prose: string | null): number {
  return (prose ?? '').split(/\s+/).filter(Boolean).length
}

/* One spelling of a Danbooru post count, because two panes show them: the
   autocomplete dropdown and the offered-tag chips beside the prose. Raw in one
   and grouped in the other made the same number read as `6000000` and
   `6,000,000` two panes apart. */
export function grouped(posts: number): string {
  return posts.toLocaleString('en-GB')
}
