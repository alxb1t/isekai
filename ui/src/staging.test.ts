import { expect } from 'vitest'
import { after, discards, heir, orphans, removal, stepped, withheld } from './staging'
import { spec } from './test/spec'
import type { StagedFile } from './types'

spec('ui:sheet:leaving-mid-commit-keeps-the-folder', () => {
  expect(discards('s1', true, true, false)).toBe(false)
  // A closed sheet's open folder is discarded; a committed one, or none, is not.
  expect(discards('s1', true, false, false)).toBe(true)
  expect(discards('s1', true, false, true)).toBe(false)
  expect(discards(null, true, false, false)).toBe(false)
  // A commit refused while the sheet is open keeps the folder for the next Import.
  expect(discards('s1', false, false, false)).toBe(false)
})

spec('ui:sheet:a-chosen-file-is-removed-alone', () => {
  // A read file leaves the staging folder; a skipped one staged nothing, so only the sheet.
  expect(removal('read', 'ready')).toBe('staging')
  expect(removal('read', 'converted')).toBe('staging')
  expect(removal('read', 'not cleaned')).toBe('staging')
  expect(removal('read', 'skipped')).toBe('sheet')
  // A file still on its way offers no removal.
  for (const phase of ['queued', 'uploading', 'waiting', 'converting'])
    expect(removal(phase, undefined)).toBeNull()
  // The focus moves to the next tile, the previous one from the last, none once all are gone.
  expect(after(1, 4)).toBe(1)
  expect(after(3, 4)).toBe(2)
  expect(after(0, 1)).toBeNull()
  // Import waits, naming the removals in flight, until each is answered and its tile gone.
  const sheet = { committing: false, removing: 1, chosen: 2, read: 2, ready: 2, adding: false }
  expect(withheld(sheet)).toBe('Removing 1 file')
  expect(withheld({ ...sheet, removing: 2 })).toBe('Removing 2 files')
  expect(withheld({ ...sheet, removing: 0 })).toBeNull()
})

spec('ui:sheet:a-removed-files-copy-keeps-it', () => {
  const read: StagedFile = { name: 'b.jpg', state: 'ready', carries: [], copyOf: null }
  const copy: StagedFile = { name: 'again.jpg', state: 'skipped', carries: [], copyOf: 'b.jpg' }
  const other: StagedFile = { name: 'more.jpg', state: 'skipped', carries: [], copyOf: 'c.jpg' }
  // The first copy still chosen takes the staged file over, so it stays in the import.
  expect(heir([read, null, other, copy, copy], 'b.jpg')).toBe(3)
  // With no copy chosen, the file leaves the staging folder.
  expect(heir([read, other], 'b.jpg')).toBe(-1)
  // A copy heard as skipped while its file's removal is in flight is held by the
  // removed tile until it goes, then stands for bytes staged nowhere: it is sent again.
  expect(orphans([read, copy])).toEqual([])
  expect(orphans([copy])).toEqual([0])
  // So is a copy heard only after the removal, beside a tile still reading.
  expect(orphans([null, copy, other])).toEqual([1, 2])
  // A copy whose file another tile holds is not.
  expect(orphans([null, copy, { ...read, name: 'c.jpg' }, other])).toEqual([1])
})

spec('ui:sheet:the-tiles-take-the-keys', () => {
  // Five tiles, three to a row: 0 1 2 / 3 4.
  expect(stepped(0, 5, 3, 'column+')).toBe(1)
  expect(stepped(2, 5, 3, 'column+')).toBe(2)
  expect(stepped(1, 5, 3, 'row+')).toBe(4)
  // A row move keeps the column, held at the shorter row's end.
  expect(stepped(2, 5, 3, 'row+')).toBe(4)
  expect(stepped(4, 5, 3, 'row-')).toBe(1)
  expect(stepped(3, 5, 3, 'column-')).toBe(3)
  expect(stepped(0, 5, 0, 'column+')).toBe(1)
})
