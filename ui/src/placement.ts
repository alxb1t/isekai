/** Return the side a list of `height` opens on, given the room `below` and `above`
    its input: below when it fits, else above when it fits, else the larger side.
    e.g. placement(100, 400, 300) -> 'above' */
export function placement(below: number, above: number, height: number): 'above' | 'below' {
  if (below >= height) return 'below'
  if (above >= height) return 'above'
  return above > below ? 'above' : 'below'
}
