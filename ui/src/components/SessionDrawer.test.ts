import { createPinia, setActivePinia, storeToRefs } from 'pinia'
import { computed, effectScope, nextTick } from 'vue'
import { expect, vi } from 'vitest'
import { useSessionViewer } from '../composables/useSessionViewer'
import { grid } from '../sessions'
import { spec } from '../test/spec'
import { useDrawerStore } from '../stores/drawer'
import { useLiveStore } from '../stores/live'

spec('ui:sessions:the-viewer-closes-for-a-replacement-session', async () => {
  setActivePinia(createPinia())
  // Leave the terminal session's record pending between its poll and the answer.
  vi.stubGlobal('fetch', () => new Promise(() => undefined))
  const scope = effectScope()
  const { drawer, live, viewer } = scope.run(() => {
    const drawer = useDrawerStore()
    const live = useLiveStore()
    drawer.shown = { id: 'finished', collections: ['b'] }
    drawer.records = {
      b: {
      id: 'finished',
      started: '',
      ended: '',
      limit: 1200,
      asked: {},
      steps: {},
      outcome: 'done',
      message: null,
      images: [{ digest: 'a', flow: 'summon-anime-wai', version: 1, seed: '7' }],
      },
    }
    const { shown, record } = storeToRefs(drawer)
    const layout = computed(() =>
      record.value ? grid(record.value) : { digests: [], flows: [], cells: [] },
    )
    const viewer = useSessionViewer(
      () => shown.value,
      () => layout.value,
      () => layout.value.digests.map((digest) => ({ src: `/photo/${digest}`, name: digest })),
      () => 'b',
    )
    return { drawer, live, viewer }
  })!
  try {
    viewer.open({ row: 1, column: 0 })
    expect(viewer.viewed.value).toEqual([{ src: '/photo/a', name: 'a' }])

    // A temporarily absent record also leaves no row to show.
    const finished = drawer.record!
    drawer.records = null
    expect(viewer.viewed.value).toEqual([])
    drawer.records = { b: finished }
    expect(viewer.viewed.value).toHaveLength(1)

    live.activeSessions = [{ collection: 'b', id: 'terminal', started: '' }]
    await nextTick()
    expect(drawer.shown).toEqual({ id: 'terminal', collections: ['b'] })
    expect(drawer.record).toBeNull()
    expect(viewer.viewed.value).toEqual([])
    expect(viewer.viewing.value).toBeNull()
    drawer.records = { b: { ...finished, id: 'terminal', outcome: 'running' } }
    expect(viewer.viewed.value).toEqual([])
    expect(viewer.viewing.value).toBeNull()
  } finally {
    scope.stop()
    vi.unstubAllGlobals()
  }
})
