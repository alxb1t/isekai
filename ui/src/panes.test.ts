import { expect } from 'vitest'
import { nextPane, type Pane } from './panes'
import { spec } from './test/spec'

spec('ui:keys:review-moves-between-its-panes', () => {
  const visited: Pane[] = []
  let at: Pane = 'rail'
  for (let press = 0; press < 3; press += 1) {
    at = nextPane(at, 1)
    visited.push(at)
  }

  expect(visited).toEqual(['source', 'sheet', 'renders'])
  expect(nextPane('renders', 1)).toBe('renders')
  expect(nextPane('rail', -1)).toBe('rail')
})
