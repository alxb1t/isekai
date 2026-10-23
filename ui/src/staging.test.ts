import { expect } from 'vitest'
import { discards } from './staging'
import { spec } from './test/spec'

spec('ui:sheet:leaving-mid-commit-keeps-the-folder', () => {
  expect(discards('s1', true, true, false)).toBe(false)
  // A closed sheet's open folder is discarded; a committed one, or none, is not.
  expect(discards('s1', true, false, false)).toBe(true)
  expect(discards('s1', true, false, true)).toBe(false)
  expect(discards(null, true, false, false)).toBe(false)
  // A commit refused while the sheet is open keeps the folder for the next Import.
  expect(discards('s1', false, false, false)).toBe(false)
})
