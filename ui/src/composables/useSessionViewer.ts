import { computed, ref, watch } from 'vue'
import { imageAt } from '../api'
import type { Shown } from '../components/ImageViewer.vue'
import type { Focus } from '../grid'
import type { Grid } from '../sessions'

/** The drawer's row viewer, following the shown session and its live grid. */
export function useSessionViewer(
  target: () => { collection: string; id: string } | null,
  layout: () => Grid,
  photographs: () => Shown[],
) {
  const viewing = ref<{ row: number; start: number } | null>(null)
  const viewed = computed<Shown[]>(() => (viewing.value ? row(viewing.value.row) : []))
  // A row belongs to one session; close before its replacement's grid is read.
  watch(target, () => (viewing.value = null), { flush: 'sync' })

  function row(at: number): Shown[] {
    if (at === layout().flows.length) return photographs()
    return (layout().cells[at] ?? []).flatMap((cell) =>
      cell.images.map((one) => ({
        src: imageAt({ collection: target()?.collection ?? '', ...one }),
        name: `${one.flow} · v${one.version} · seed ${one.seed}`,
      })),
    )
  }

  function open(at: Focus, index = 0): void {
    if (at.row === layout().flows.length) {
      viewing.value = { row: at.row, start: at.column }
      return
    }
    const before = layout().cells[at.row]
      .slice(0, at.column)
      .reduce((sum, cell) => sum + cell.images.length, 0)
    const cell = layout().cells[at.row][at.column]
    if (!cell.images.length) return
    viewing.value = { row: at.row, start: before + index }
  }

  return { viewing, viewed, open }
}
