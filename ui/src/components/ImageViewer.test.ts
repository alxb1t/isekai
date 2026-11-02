import { createPinia, setActivePinia } from 'pinia'
import { effectScope, nextTick, ref } from 'vue'
import { beforeEach, expect, vi } from 'vitest'
import { spec } from '../test/spec'
import { type Press, useKeyStore } from '../stores/keys'
import { SCROLL, useViewer, viewerKeys } from '../composables/useViewer'

beforeEach(() => {
  setActivePinia(createPinia())
})

/* A keydown outside any field, as the listener reads it. */
function press(code: string, given: Partial<Press> = {}): Press {
  const event = {
    code,
    shiftKey: false,
    metaKey: false,
    ctrlKey: false,
    altKey: false,
    defaultPrevented: false,
    target: null,
    preventDefault: () => {
      event.defaultPrevented = true
    },
    ...given,
  }
  return event
}

/* A viewer over `count` images, its keys declared as the dialog declares them. */
function opened(count: number, pair = false, open?: () => void) {
  const images = Array.from({ length: count }, (_, index) => ({ src: `/${index}` }))
  const scope = effectScope()
  const viewer = scope.run(() => useViewer(() => images, 0, vi.fn()))!
  const scroll = vi.fn()
  const keys = useKeyStore()
  keys.declare(
    'overlay',
    viewerKeys(viewer, { close: vi.fn(), scroll, pair: () => pair, open }),
  )
  return { viewer, keys, scroll, scope }
}

spec('ui:sessions:the-viewer-follows-image-identity', async () => {
  const a = { src: '/a' }
  const b = { src: '/b' }
  const c = { src: '/c' }
  const images = ref([a, b])
  const closed = vi.fn()
  const scope = effectScope()
  const viewer = scope.run(() => useViewer(() => images.value, 1, closed))!
  try {
    expect(viewer.shown.value.src).toBe('/b')
    images.value = [b, a]
    await nextTick()
    expect(viewer.shown.value.src).toBe('/b')
    images.value = [b]
    await nextTick()
    expect(viewer.shown.value.src).toBe('/b')
    images.value = [a, b, c]
    await nextTick()
    expect(viewer.shown.value.src).toBe('/b')
    viewer.step(1)
    expect(viewer.shown.value.src).toBe('/c')
    images.value = [a]
    await nextTick()
    expect(viewer.shown.value.src).toBe('/a')
    images.value = []
    await nextTick()
    expect(closed).toHaveBeenCalledOnce()
  } finally {
    scope.stop()
  }
})

spec('ui:viewer:enter-toggles-full-size', () => {
  const open = vi.fn()
  const one = opened(1, false, open)
  expect(one.viewer.actual.value).toBe(false)
  expect(one.keys.press(press('Enter'))).toBe(true)
  expect(one.viewer.actual.value).toBe(true)
  one.keys.press(press('Enter'))
  expect(one.viewer.actual.value).toBe(false)
  // The opener's large view is ⇧↵, never ↵.
  expect(open).not.toHaveBeenCalled()
  one.keys.press(press('Enter', { shiftKey: true }))
  expect(open).toHaveBeenCalledOnce()
  one.scope.stop()

  // A pair is fitted alone: ↵ changes nothing.
  setActivePinia(createPinia())
  const pair = opened(2, true)
  expect(pair.keys.press(press('Enter'))).toBe(false)
  expect(pair.viewer.actual.value).toBe(false)
  pair.scope.stop()
})

spec('ui:viewer:full-size-scrolls-by-the-keys', async () => {
  const { viewer, keys, scroll, scope } = opened(2)
  // Fitted, there is nothing to scroll.
  expect(keys.press(press('KeyJ'))).toBe(false)
  keys.press(press('Enter'))
  keys.press(press('KeyJ'))
  keys.press(press('ArrowUp'))
  expect(scroll.mock.calls).toEqual([[SCROLL], [-SCROLL]])
  keys.press(press('KeyL'))
  await nextTick()
  expect(viewer.shown.value.src).toBe('/1')
  expect(viewer.actual.value).toBe(false)
  scope.stop()
})
