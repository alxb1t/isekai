/** Return a reveal for a key's move: the first of `rows` scrolls `page` to its top, the last to
    its foot, then the row's `cell` scrolls into view `nearest`. e.g. (cell, 0, 3) -> page at top */
export function useEdges(
  page: () => HTMLElement | null | undefined,
): (cell: HTMLElement, row: number, rows: number) => void {
  return (cell, row, rows) => {
    const held = page()
    if (row === 0) held?.scrollTo({ top: 0 })
    else if (row === rows - 1) held?.scrollTo({ top: held.scrollHeight })
    cell.scrollIntoView({ block: 'nearest' })
  }
}
