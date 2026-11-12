import { expect } from 'vitest'
import panel from './components/ImagePanel.vue?raw'
import outline from './components/OutlineStep.vue?raw'
import picker from './components/TattooPicker.vue?raw'
import { spec } from './test/spec'
import large from './views/RenderLarge.vue?raw'
import place from './views/Place.vue?raw'

const SCREEN = {
  'Place.vue': place,
  'TattooPicker.vue': picker,
  'OutlineStep.vue': outline,
  'ImagePanel.vue': panel,
}

spec('ui:place-keys:the-screen-declares-no-command', () => {
  for (const [file, source] of Object.entries(SCREEN)) {
    expect(source, file).not.toMatch(/useKeys|useKeyStore|\.declare\(/)
    expect(source, file).not.toMatch(/keydown|keyup|keypress/)
  }
  // The read sees a declaration where there is one.
  expect(large).toContain('useKeys(')
})
