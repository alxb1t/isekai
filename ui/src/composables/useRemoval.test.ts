import { effectScope } from 'vue'
import { expect } from 'vitest'
import { spec } from '../test/spec'
import { useRemoval } from './useRemoval'

/** A removal the case settles by hand, and the names the picker is told of. */
function removing() {
  let answer: () => void = () => undefined
  let refuse: () => void = () => undefined
  const remove = () =>
    new Promise<string>((resolve, reject) => {
      answer = () => resolve('gone')
      refuse = () => reject(new Error('refused'))
    })
  const told: string[] = []
  const scope = effectScope()
  const { asking, question } = scope.run(() =>
    useRemoval({ remove, removed: (name) => void told.push(name) }),
  )!
  return { scope, asking, question, told, answer: () => answer(), refuse: () => refuse() }
}

spec('ui:picker:a-dismissed-removal-still-lists-the-rest', async () => {
  // The dialog is dismissed while the request runs: the request that answers still tells the picker.
  const answered = removing()
  answered.asking.value = 'bow'
  const first = answered.question.value!.run()
  answered.asking.value = null
  answered.answer()
  expect(await first).toBe('gone')
  expect(answered.told).toEqual(['bow'])
  expect(answered.asking.value).toBeNull()
  answered.scope.stop()

  // A refusal tells nothing and is thrown on, for the dialog to show while it stays.
  const refused = removing()
  refused.asking.value = 'bow'
  const second = refused.question.value!.run()
  refused.asking.value = null
  refused.refuse()
  await expect(second).rejects.toThrow('refused')
  expect(refused.told).toEqual([])
  refused.scope.stop()

  // The dialog stays: the answer tells the picker once and closes the question.
  const kept = removing()
  kept.asking.value = 'bow'
  const third = kept.question.value!.run()
  kept.answer()
  await third
  expect(kept.told).toEqual(['bow'])
  expect(kept.asking.value).toBeNull()
  kept.scope.stop()
})
