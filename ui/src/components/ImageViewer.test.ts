import { effectScope, nextTick, ref } from 'vue'
import { expect, vi } from 'vitest'
import { spec } from '../test/spec'
import { useViewer } from '../composables/useViewer'

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
