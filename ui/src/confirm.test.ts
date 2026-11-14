import { expect } from 'vitest'
import { deletion, removal, reporting } from './confirm'
import { spec } from './test/spec'

spec('ui:picker:remove-asks-in-a-dialog', async () => {
  expect(removal('bow')).toEqual({ title: 'Remove this tattoo?', name: 'bow' })
  expect(deletion).toEqual({ title: 'Delete this render?', name: null })
  // The name is the tattoo's own, so two removals differ.
  expect(removal('arm').name).toBe('arm')
  // The removal reports itself done when its request succeeds, with no dialog to carry the word:
  // one dismissed while the request ran must not leave the removed tattoo on the picker.
  const told: string[] = []
  let finish: () => void = () => undefined
  const slow = new Promise<void>((resolve) => {
    finish = resolve
  })
  const pending = reporting(() => slow, () => told.push('bow'))()
  expect(told).toEqual([])
  finish()
  await pending
  expect(told).toEqual(['bow'])
  // A refusal reports nothing, and is still thrown for the dialog to show.
  const refused = reporting(() => Promise.reject(new Error('no such tattoo')), () => told.push('arm'))
  await expect(refused()).rejects.toThrow('no such tattoo')
  expect(told).toEqual(['bow'])
})
