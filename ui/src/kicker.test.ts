import { expect } from 'vitest'
import { kickerOf } from './kicker'
import { spec } from './test/spec'

spec('ui:conjure-from:conjure-from-this-opens-review', () => {
  const held = {
    drafted: true,
    approved: false,
    readonly: false,
    approvedAt: null,
    revision: null,
  }
  expect(kickerOf(held)).toBe('draft')
  expect(kickerOf({ ...held, approvedAt: '09:30:00' })).not.toContain('approved')
})
