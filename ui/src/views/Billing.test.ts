import { expect } from 'vitest'
import { spec } from '../test/spec'
import { billingState } from '../stores/live'

spec('ui:billing:clearance-requires-known-absence', () => {
  expect(billingState(null, false)).toBe('pending')
  expect(billingState({ pod: false, volume: { state: 'open', ends: null } }, false)).toBe('open')
  expect(billingState({ pod: false, volume: null }, false)).toBe('quiet')
  expect(billingState({ pod: true, volume: null }, false)).toBe('alert')
})
