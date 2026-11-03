import { effectScope, nextTick, ref } from 'vue'
import { expect, vi } from 'vitest'
import { spec } from '../test/spec'
import { useCentred } from './useCentred'

spec('ui:review:a-stepped-sheet-stays-in-view', async () => {
  const current = ref('a')
  const cards: Record<string, { scrollIntoView: ReturnType<typeof vi.fn> }> = {
    a: { scrollIntoView: vi.fn() },
    b: { scrollIntoView: vi.fn() },
  }
  const scope = effectScope()
  scope.run(() =>
    useCentred(
      () => current.value,
      () => cards[current.value] as unknown as Element,
    ),
  )
  // ⇧J steps the rail to a sheet past its visible end.
  current.value = 'b'
  await nextTick()
  await nextTick()
  expect(cards.b.scrollIntoView).toHaveBeenCalledExactlyOnceWith({ block: 'center' })
  expect(cards.a.scrollIntoView).not.toHaveBeenCalled()
  scope.stop()
})
