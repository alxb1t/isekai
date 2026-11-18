import { expect } from 'vitest'
import { committed, held, redone, reloaded, removed, undone } from './edits'
import { spec } from './test/spec'

const start = () => held({ hair: ['long hair', 'brown hair'], eyes: ['blue eyes'] })

spec('ui:save:an-edit-is-undone-and-redone', () => {
  // held
  const given = { hair: ['long hair'] }
  const kept = held(given)
  given.hair = ['short hair']
  expect(kept.fields).toEqual({ hair: ['long hair'] })
  expect(kept.past).toEqual([])
  expect(kept.future).toEqual([])

  // committed
  const added = committed(start(), 'hair', 'red hair', null)
  expect(added.fields.hair).toEqual(['long hair', 'brown hair', 'red hair'])
  expect(added.fields.eyes).toEqual(['blue eyes'])
  expect(added.past).toEqual([
    { field: 'hair', before: ['long hair', 'brown hair'], after: ['long hair', 'brown hair', 'red hair'] },
  ])

  const replaced = committed(start(), 'hair', 'red hair', 0)
  expect(replaced.fields.hair).toEqual(['red hair', 'brown hair'])
  expect(replaced.past).toEqual([
    { field: 'hair', before: ['long hair', 'brown hair'], after: ['red hair', 'brown hair'] },
  ])

  const same = start()
  const itself = committed(same, 'hair', 'long hair', 0)
  expect(itself).not.toBe(same)
  expect(itself.fields.hair).toEqual(['long hair', 'brown hair'])
  expect(itself.past).toHaveLength(1)

  expect(committed(start(), 'hair', 'red hair', 2).fields.hair).toEqual(['long hair', 'brown hair', 'red hair'])
  expect(committed(start(), 'hair', 'red hair', -1).fields.hair).toEqual(['long hair', 'brown hair', 'red hair'])
  const there = start()
  expect(committed(there, 'hair', 'long hair', 5)).toBe(there)
  expect(committed(there, 'hair', 'long hair', -1)).toBe(there)

  expect(committed(there, 'hair', 'brown hair', null)).toBe(there)

  const fresh = committed(start(), 'mouth', 'smile', null)
  expect(fresh.fields.mouth).toEqual(['smile'])
  expect(fresh.past[0]).toEqual({ field: 'mouth', before: [], after: ['smile'] })

  // removed
  const gone = removed(start(), 'hair', 0)
  expect(gone.fields.hair).toEqual(['brown hair'])
  expect(gone.past).toEqual([{ field: 'hair', before: ['long hair', 'brown hair'], after: ['brown hair'] }])

  const below = start()
  expect(removed(below, 'hair', -1)).toBe(below)
  expect(removed(below, 'hair', 2)).toBe(below)
  expect(removed(below, 'mouth', 0)).toBe(below)

  // undone and redone
  const edited = removed(committed(start(), 'hair', 'red hair', null), 'eyes', 0)
  expect(edited.fields.eyes).toEqual([])

  const back = undone(edited)
  expect(back.fields.eyes).toEqual(['blue eyes'])
  expect(back.fields.hair).toEqual(['long hair', 'brown hair', 'red hair'])
  expect(back.past).toHaveLength(1)
  expect(back.future).toHaveLength(1)
  expect(edited.fields.eyes).toEqual([])
  expect(edited.past).toHaveLength(2)
  expect(edited.future).toEqual([])

  const backAgain = undone(back)
  expect(backAgain.fields.hair).toEqual(['long hair', 'brown hair'])
  expect(backAgain.past).toEqual([])
  expect(backAgain.future).toHaveLength(2)

  const forth = redone(backAgain)
  expect(forth.fields.hair).toEqual(['long hair', 'brown hair', 'red hair'])
  expect(forth.past).toHaveLength(1)
  expect(forth.future).toHaveLength(1)
  expect(backAgain.fields.hair).toEqual(['long hair', 'brown hair'])
  expect(backAgain.future).toHaveLength(2)

  const opened = start()
  expect(undone(opened)).toBe(opened)
  expect(redone(opened)).toBe(opened)
  const firstEdit = undone(committed(start(), 'mouth', 'smile', null))
  expect(firstEdit.fields.mouth).toEqual([])

  const ended = committed(back, 'hair', 'grey hair', null)
  expect(ended.future).toEqual([])
  expect(redone(ended)).toBe(ended)
  expect(removed(back, 'hair', 0).future).toEqual([])

  // reloaded
  const history = committed(start(), 'hair', 'red hair', null)
  const undoneOnce = undone(history)
  const landed = reloaded(undoneOnce, { hair: ['white hair'] })
  expect(landed.fields).toEqual({ hair: ['white hair'] })
  expect(landed.past).toBe(undoneOnce.past)
  expect(landed.future).toBe(undoneOnce.future)
  expect(undoneOnce.fields.eyes).toEqual(['blue eyes'])
})
