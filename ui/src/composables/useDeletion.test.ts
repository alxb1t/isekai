import { effectScope } from 'vue'
import { expect } from 'vitest'
import { spec } from '../test/spec'
import { useDeletion } from './useDeletion'

/** A read the case settles by hand, and the Hub opens it counts. */
function held() {
  let answer: () => void = () => undefined
  let refuse: () => void = () => undefined
  const reload = () =>
    new Promise<void>((resolve, reject) => {
      answer = resolve
      refuse = () => reject(new Error('refused'))
    })
  const opened: string[] = []
  const scope = effectScope()
  const { deleted } = scope.run(() => useDeletion({ reload, open: () => opened.push('hub') }))!
  return { scope, deleted, opened, answer: () => answer(), refuse: () => refuse() }
}

/** A deletion the case settles by hand, with no dialog to carry its word; the Hub's read answers at once. */
function deleting() {
  let answer: () => void = () => undefined
  let refuse: () => void = () => undefined
  const remove = () =>
    new Promise<string>((resolve, reject) => {
      answer = () => resolve('gone')
      refuse = () => reject(new Error('refused'))
    })
  const opened: string[] = []
  const scope = effectScope()
  const { through } = scope.run(() =>
    useDeletion({ reload: () => Promise.resolve(), open: () => opened.push('hub') }),
  )!
  return { scope, run: through(remove), opened, answer: () => answer(), refuse: () => refuse() }
}

const afterTheRead = () => new Promise<void>((resolve) => setTimeout(resolve, 0))

spec('ui:delete-render:a-reload-that-lands-after-leaving-moves-nothing', async () => {
  // The view is left before the read answers: nothing opens, answered or refused.
  const answered = held()
  const first = answered.deleted()
  answered.scope.stop()
  answered.answer()
  await first
  expect(answered.opened).toEqual([])

  const refused = held()
  const second = refused.deleted()
  refused.scope.stop()
  refused.refuse()
  await second
  expect(refused.opened).toEqual([])

  // The view is kept: the Hub opens once, answered or refused.
  const kept = held()
  const third = kept.deleted()
  kept.answer()
  await third
  expect(kept.opened).toEqual(['hub'])
  kept.scope.stop()

  const keptRefused = held()
  const fourth = keptRefused.deleted()
  keptRefused.refuse()
  await fourth
  expect(keptRefused.opened).toEqual(['hub'])
  keptRefused.scope.stop()
})

spec('ui:delete-render:a-dismissed-dialog-still-opens-the-hub', async () => {
  // No dialog carries the word: the request that answers reports, and the Hub opens once.
  const answered = deleting()
  const first = answered.run()
  answered.answer()
  expect(await first).toBe('gone')
  await afterTheRead()
  expect(answered.opened).toEqual(['hub'])
  answered.scope.stop()

  // A refusal opens nothing and is thrown on, for the dialog to show while it stays.
  const refused = deleting()
  const second = refused.run()
  refused.refuse()
  await expect(second).rejects.toThrow('refused')
  await afterTheRead()
  expect(refused.opened).toEqual([])
  refused.scope.stop()
})
