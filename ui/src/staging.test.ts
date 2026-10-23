import { expect } from 'vitest'
import { discards } from './staging'
import { spec } from './test/spec'

spec('ui:sheet:leaving-mid-commit-keeps-the-folder', () => {
  expect(discards('s1', true, false)).toBe(false)
  // An open folder is discarded; a committed one, or none, is not.
  expect(discards('s1', false, false)).toBe(true)
  expect(discards('s1', false, true)).toBe(false)
  expect(discards(null, false, false)).toBe(false)
})
