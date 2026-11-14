import { expect } from 'vitest'
import { spec } from '../test/spec'
import { latest } from './RenderLarge.vue'

spec('ui:delete-render:the-hub-opens-without-the-deleted-render', async () => {
  // The post-deletion Hub read is pending, the operator leaves, then the read ends: no push.
  const pending = latest()
  const pushed: string[] = []
  let finish: () => void = () => undefined
  const reload = new Promise<void>((resolve) => (finish = resolve))
  const opening = (async () => {
    const still = pending.begin()
    await reload
    if (still()) pushed.push('hub')
  })()
  pending.drop()
  finish()
  await opening
  expect(pushed).toEqual([])

  // A read that ends while the view stays pushes once.
  const kept = latest()
  const still = kept.begin()
  await Promise.resolve()
  expect(still()).toBe(true)
})
