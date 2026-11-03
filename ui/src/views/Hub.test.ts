import { expect } from 'vitest'
import { spec } from '../test/spec'
import { prepareButton, toPrepare } from './Hub.vue'

spec('ui:prepare:the-bar-names-its-photographs', () => {
  // Two photographs, each assigned to two flows.
  const changes = ['ada.jpg', 'ada.jpg', 'bea.jpg', 'bea.jpg']
  expect(toPrepare(changes, 'b')).toBe('2 photographs to prepare in b')
  expect(prepareButton(changes.length)).toBe('4 changes · Prepare')
  expect(toPrepare(['ada.jpg'], 'b')).toBe('1 photograph to prepare in b')
  expect(prepareButton(1)).toBe('1 change · Prepare')
})
