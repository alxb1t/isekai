import { nextTick, ref, type Ref } from 'vue'
import { clamp, kept, type Focus } from '../grid'
import { at } from '../stores/collection'
import type { HubSource } from '../types'

type Named = Pick<HubSource, 'name' | 'digest'>

/** Return a cell's name in the store's focus: its source's and its flow's, the source column's flow empty.

    e.g. ([{ name: 'a' }], ['flat'], { row: 0, column: 1 }) -> 'a|flat' */
export function spotName(sources: Named[], flows: string[], spot: Focus): string {
  return at(sources[spot.row]?.name ?? '', flows[spot.column - 1] ?? '')
}

/** Return the spot a hub opens on: the cell a large view sent, else the one `held` names, else the first.

    A spot is a row of every source by a column of the source cell and every flow. */
export function restoredSpot(
  sources: Named[],
  flows: string[],
  sent: { digest: string; flow: string } | undefined,
  held: string | null,
): Focus | undefined {
  const spots = sources.flatMap((_, row) =>
    Array.from({ length: flows.length + 1 }, (_, column) => ({ row, column })),
  )
  const sentFrom = sent
    ? spots.find(
        ({ row, column }) =>
          sources[row]?.digest === sent.digest && flows[column - 1] === sent.flow,
      )
    : undefined
  return sentFrom ?? kept(spots, (spot) => spotName(sources, flows, spot), held)
}

/** Return the hub's focus and selection, with the moves that change them.

    `grid` holds the cells, `reveal` scrolls a key's move, and `remember` stores the focused cell's name. */
export function useHubFocus(options: {
  sources: Readonly<Ref<Named[]>>
  flows: Readonly<Ref<string[]>>
  grid: Readonly<Ref<HTMLElement | null>>
  reveal: (cell: HTMLElement, row: number, rows: number) => void
  remember: (name: string) => void
}) {
  const { sources, flows, grid, reveal, remember } = options
  const focus = ref<Focus>({ row: 0, column: 0 })
  const selected = ref<Set<number>>(new Set())

  function focusedCell(): HTMLElement | null | undefined {
    return grid.value?.querySelector<HTMLElement>(
      `[data-row="${focus.value.row}"][data-column="${focus.value.column}"]`,
    )
  }

  function place(
    row: number,
    column: number,
    how: ScrollIntoViewOptions | 'key' = { block: 'nearest' },
  ): void {
    const rows = sources.value.length
    if (rows === 0) return
    focus.value = {
      row: clamp(row, rows - 1),
      column: clamp(column, flows.value.length),
    }
    remember(spotName(sources.value, flows.value, focus.value))
    void nextTick(() => {
      const cell = focusedCell()
      if (!cell) return
      cell.focus({ preventScroll: true })
      if (how === 'key') reveal(cell, focus.value.row, rows)
      else cell.scrollIntoView(how)
    })
  }

  function select(step: number): void {
    const { row, column } = focus.value
    const target = Math.min(Math.max(row + step, 0), sources.value.length - 1)
    selected.value = new Set([...selected.value, row, target])
    place(target, column, 'key')
  }

  const moveBy = (rows: number, columns: number) => () =>
    place(focus.value.row + rows, focus.value.column + columns, 'key')

  return { focus, selected, place, select, moveBy }
}
