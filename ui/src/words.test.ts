import { expect } from 'vitest'
import { spec } from './test/spec'
import { noun } from './words'

spec('ui:batch-folder:count-labels-use-singular-at-one', () => {
  for (const count of [0, 1, 3]) {
    for (const word of ['source', 'flow', 'input', 'file', 'image', 'field']) {
      expect(noun(count, word)).toBe(count === 1 ? word : `${word}s`)
    }
    expect(noun(count, 'batch', 'batches')).toBe(count === 1 ? 'batch' : 'batches')
  }
})
