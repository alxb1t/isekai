import { expect } from 'vitest'
import confirmation from './components/ConfirmDialog.vue?raw'
import panel from './components/ImagePanel.vue?raw'
import leave from './components/LeaveDialog.vue?raw'
import outline from './components/OutlineStep.vue?raw'
import pairList from './components/PairList.vue?raw'
import pairPanel from './components/PairPanel.vue?raw'
import picker from './components/TattooPicker.vue?raw'
import review from './components/ReviewBake.vue?raw'
import stagePhoto from './components/StagePhoto.vue?raw'
import stageRender from './components/StageRender.vue?raw'
import { spec } from './test/spec'
import large from './views/RenderLarge.vue?raw'
import place from './views/Place.vue?raw'

const SCREEN = {
  'Place.vue': place,
  'TattooPicker.vue': picker,
  'OutlineStep.vue': outline,
  'ImagePanel.vue': panel,
  'PairPanel.vue': pairPanel,
  'PairList.vue': pairList,
  'StagePhoto.vue': stagePhoto,
  'StageRender.vue': stageRender,
  'ReviewBake.vue': review,
  'LeaveDialog.vue': leave,
}

/* The outline step and the stages that hold pairs declare the keys, through `placeCommands`
   alone: its three ids are `undo`, `redo` and `close`. The panel alone reads the keyboard. */
const DECLARES = ['OutlineStep.vue', 'StagePhoto.vue', 'StageRender.vue']
const LISTENS = ['ImagePanel.vue']

spec('ui:place-keys:the-screen-declares-only-undo-redo-and-close', () => {
  for (const [file, source] of Object.entries(SCREEN)) {
    expect(source, file).not.toMatch(/useKeyStore|\.declare\(/)
    expect(source, file).not.toMatch(/keypress/)
    if (!LISTENS.includes(file)) expect(source, file).not.toMatch(/keydown|keyup/)
    if (DECLARES.includes(file)) {
      expect(source, file).not.toMatch(/useKeys\((?!'screen', placeCommands\()/)
    } else {
      expect(source, file).not.toMatch(/useKeys/)
    }
  }
  // The confirmation dialog the picker opens declares its own overlay keys, and reads no keyboard.
  expect(confirmation.match(/useKeys\('overlay'/g)).toHaveLength(1)
  expect(confirmation).not.toMatch(/keydown|keyup|keypress/)
  // The read sees a declaration where there is one, and a listener.
  expect(large).toContain('useKeys(')
  expect(panel).toContain('keydown')
  expect(panel).toContain('keyup')
  expect('useKeys(`screen`, () => [])').toMatch(/useKeys\((?!'screen', placeCommands\()/)
})
