/** Return a reveal for a key's move: the first of `rows` scrolls `page` to its top, the last to
    its foot, then the row's `cell` scrolls into view `nearest`. When `centred`, the first and
    the last only scroll `page`, and any other row's cell scrolls to the centre.
    e.g. (cell, 0, 3) -> page at top */
export function useEdges(
  page: () => HTMLElement | null | undefined,
  centred = false,
): (cell: HTMLElement, row: number, rows: number) => void {
  return (cell, row, rows) => {
    const held = page()
    if (row === 0) held?.scrollTo({ top: 0 })
    else if (row === rows - 1) held?.scrollTo({ top: held.scrollHeight })
    else if (centred) cell.scrollIntoView({ block: 'center' })
    if (!centred) cell.scrollIntoView({ block: 'nearest' })
  }
}
