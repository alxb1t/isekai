import { expect } from 'vitest'
import { deletion, removal } from './confirm'
import { spec } from './test/spec'

spec('ui:picker:remove-asks-in-a-dialog', () => {
  expect(removal('bow')).toEqual({ title: 'Remove this tattoo?', name: 'bow' })
  expect(deletion).toEqual({ title: 'Delete this render?', name: null })
  // The name is the tattoo's own, so two removals differ.
  expect(removal('arm').name).toBe('arm')
})
