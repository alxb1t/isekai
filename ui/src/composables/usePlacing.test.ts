import { expect } from 'vitest'
import { type Named, type Ports, usePlacing } from './usePlacing'
import { begun, closed, drawn, none as outlinesNone, regions } from '../outlines'
import { clicked, complete, held, none } from '../pairs'
import { drafted } from '../polygon'
import { answered, asked, due, keyOf, noAsks, stands } from '../propose'
import { spec } from '../test/spec'
import type { Outline, Pair, Point, Stage1 } from '../types'

const PLACE = { collection: 'wedding', digest: 'a1b2c3d4e5f6', flow: 'summon-anime-wai' }
const POINTS = 3

const named = (over: Partial<Named>): Named => ({
  name: 'bow',
  kind: 'image',
  size: [800, 600],
  kept: '2026-11-12T09:30:00.000000Z',
  outlined: true,
  downscaled_from: null,
  cut_from: null,
  outline: { points: [], closed: true, white: 1, neutral: false, depth: 1 },
  ...over,
})

const pairs = (count: number): Pair[] =>
  Array.from({ length: count }, (_, n): Pair => [[n * 50, 10], [n * 50, 400]])

/* A server that keeps what it is sent, and the saves it was sent. */
function server(start: Stage1 = { pairs: [], not_on_photo: false }, tattoo = named({})) {
  const saved: Stage1[] = []
  const reads: string[] = []
  const ports: Ports = {
    read: async (name) => {
      reads.push(name)
      return { ...tattoo, name }
    },
    stageOne: async () => start,
    save: async (_digest, _name, stage) => {
      saved.push(stage)
      return stage
    },
  }
  return { ports, saved, reads }
}

const click = (state: ReturnType<typeof held>, side: 'a' | 'b', at: Point) =>
  clicked(state, side, at, 1, 8)

spec('ui:pairs:the-pairs-stay-across-steps', async () => {
  const { ports, reads } = server({ pairs: pairs(6), not_on_photo: false })
  const placing = usePlacing(PLACE, ports)
  await placing.load('bow')

  // Pairs placed on the later stage, then the screen moves on and back: the same name is
  // not read again, so what the steps held stands.
  placing.editSecond(click(click(none, 'a', [30, 40]), 'b', [300, 400]))
  const ring: Point[] = [[10, 10], [200, 10], [200, 200]]
  placing.editOutlines(closed(drawn(begun(outlinesNone, 'limb'), drafted(ring, true))))
  await placing.load('bow')
  await placing.load('bow')

  expect(reads).toEqual(['bow'])
  expect(complete(placing.second.value)).toEqual([[[30, 40], [300, 400]]])
  expect(complete(placing.first.value)).toEqual(pairs(6))
  expect(regions(placing.outlines.value).limb).toEqual(ring)
  // Another tattoo starts clean.
  await placing.load('arm')
  expect(placing.second.value).toBe(none)
  expect(placing.outlines.value).toBe(outlinesNone)

  // A tattoo the library refuses is shown as its refusal, and none is held.
  const refusing = usePlacing(PLACE, {
    read: async () => {
      throw new Error('ghost is no tattoo; pick one the library lists')
    },
    stageOne: async () => ({ pairs: [], not_on_photo: false }),
    save: async (_digest, _name, stage) => stage,
  })
  await refusing.load('ghost')
  expect(refusing.refusal.value).toBe('ghost is no tattoo; pick one the library lists')
  expect(refusing.tattoo.value).toBeNull()
})

spec('tattoo:stage1:pairs-are-saved-as-they-are-sent', async () => {
  const { ports, saved } = server()
  const placing = usePlacing(PLACE, ports)
  await placing.load('bow')

  let state = placing.first.value
  state = click(state, 'a', [10, 10])
  placing.editFirst(state)
  await placing.settled()
  expect(saved).toEqual([])

  state = click(state, 'b', [500, 500])
  placing.editFirst(state)
  await placing.settled()

  expect(saved).toEqual([{ pairs: [[[10, 10], [500, 500]]], not_on_photo: false }])
  expect(placing.read.value?.pairs).toHaveLength(1)
  expect(placing.status.value).toBe('saved')
  // The moment of the last save is what the Leave dialog names.
  expect(placing.savedAt.value).toBeInstanceOf(Date)

  // A read made `after` a change waits for its save, so a list is never older than the file.
  const landed: Stage1[] = []
  const slow = usePlacing(PLACE, {
    ...ports,
    save: async (_digest, _name, stage) => {
      await new Promise((resolve) => setTimeout(resolve, 5))
      landed.push(stage)
      return stage
    },
  })
  await slow.load('bow')
  slow.editFirst(click(click(none, 'a', [10, 10]), 'b', [500, 500]))
  expect(await slow.after(async () => landed.length)).toBe(1)
})

spec('tattoo:stage1:pairs-are-saved-as-they-are-sent', async () => {
  const { ports, saved } = server({ pairs: pairs(7), not_on_photo: false })
  const placing = usePlacing(PLACE, ports)
  await placing.load('bow')

  // A lone point is held and not sent; a move of a point is a change of the complete pairs.
  const lone = click(placing.first.value, 'a', [900, 900])
  placing.editFirst(lone)
  placing.editFirst(lone)
  await placing.settled()
  expect(saved).toEqual([])
  expect(complete(placing.first.value)).toHaveLength(7)
  expect(placing.first.value.slots).toHaveLength(8)

  placing.editFirst(click(lone, 'b', [800, 800]))
  await placing.settled()
  expect(saved).toHaveLength(1)
  expect(saved[0].pairs).toHaveLength(8)
})

spec(['ui:direct:the-flag-skips-stage-1', 'tattoo:stage1:the-flag-keeps-the-pairs'], async () => {
  const { ports, saved } = server({ pairs: pairs(6), not_on_photo: false })
  const placing = usePlacing(PLACE, ports)
  await placing.load('bow')
  expect(placing.mode.value).toBe('two-stage')

  placing.setNotOnPhoto(true)
  await placing.settled()

  expect(placing.mode.value).toBe('direct')
  expect(saved).toEqual([{ pairs: pairs(6), not_on_photo: true }])
  placing.setNotOnPhoto(false)
  await placing.settled()
  expect(saved[1]).toEqual({ pairs: pairs(6), not_on_photo: false })
  expect(placing.mode.value).toBe('two-stage')
})

spec('ui:proposal:a-stage-with-no-pairs-asks-once', async () => {
  const { ports } = server({ pairs: pairs(6), not_on_photo: false })
  const placing = usePlacing(PLACE, ports)
  await placing.load('bow')
  const key = keyOf('bow', 'v1', '7')

  // The first opening of stage 2 is due and records its ask.
  expect(due(placing.mode.value, placing.second.value, placing.proposalAsked.value, key, POINTS, false)).toBe(true)
  placing.proposalAsked.value = answered(asked(placing.proposalAsked.value, key), key, 0)

  // A step change holds the same tattoo, which is not read again: its ask stays.
  await placing.load('bow')
  expect(due(placing.mode.value, placing.second.value, placing.proposalAsked.value, key, POINTS, false)).toBe(false)
  // Another tattoo has its own key, and is due.
  const other = keyOf('arm', 'v1', '7')
  await placing.load('arm')
  expect(due(placing.mode.value, placing.second.value, placing.proposalAsked.value, other, POINTS, false)).toBe(true)
  // Its own ask is recorded once and not made again while the tattoo is held.
  placing.proposalAsked.value = answered(asked(placing.proposalAsked.value, other), other, 2)
  expect(due(placing.mode.value, placing.second.value, placing.proposalAsked.value, other, POINTS, false)).toBe(false)
  await placing.load('arm')
  expect(due(placing.mode.value, placing.second.value, placing.proposalAsked.value, other, POINTS, false)).toBe(false)
  // A fresh placing, as after a reload of the page, holds no ask.
  expect(usePlacing(PLACE, ports).proposalAsked.value).toBe(noAsks)
})

spec('ui:proposal:returning-to-a-tattoo-asks-again', async () => {
  const { ports } = server({ pairs: pairs(6), not_on_photo: false })
  const placing = usePlacing(PLACE, ports)
  await placing.load('bow')
  const key = keyOf('bow', 'v1', '7')
  const dueNow = () => due(placing.mode.value, placing.second.value, placing.proposalAsked.value, key, POINTS, false)

  // Answered, then another tattoo, then back: the pairs were cleared, so the ask goes too.
  placing.proposalAsked.value = answered(asked(placing.proposalAsked.value, key), key, 3)
  expect(dueNow()).toBe(false)
  await placing.load('arm')
  await placing.load('bow')
  expect(placing.proposalAsked.value).toBe(noAsks)
  expect(dueNow()).toBe(true)

  // An answer still on its way when another tattoo is held no longer stands.
  placing.proposalAsked.value = asked(placing.proposalAsked.value, key)
  const coming = placing.proposalAsked.value[key]
  expect(stands(placing.proposalAsked.value, key, coming)).toBe(true)
  await placing.load('arm')
  expect(stands(placing.proposalAsked.value, key, coming)).toBe(false)
  await placing.load('bow')
  expect(dueNow()).toBe(true)
})

spec('ui:proposal:an-ask-waits-for-the-saved-outline', async () => {
  const open: Outline = { points: [[10, 10], [200, 10]], closed: false, white: 1, neutral: true, depth: 1.6 }
  const shut: Outline = { ...open, points: [[10, 10], [200, 10], [200, 200]], closed: true }
  const { ports } = server(undefined, named({ kind: 'cut', cut_from: PLACE.digest, outlined: false, outline: open }))
  const placing = usePlacing(PLACE, ports)
  await placing.load('bow')
  expect(placing.reading.value).toBe(false)

  // A save on its way is work in flight, and the tattoo still holds the outline read.
  let answer: (outline: Outline) => void = () => undefined
  const saving = placing.track(new Promise<Outline>((resolve) => (answer = resolve)))
  expect(placing.reading.value).toBe(true)
  expect(placing.tattoo.value?.outline).toEqual(open)

  // Its answer is adopted once the work is counted down.
  answer(shut)
  placing.adopt('bow', await saving)
  expect(placing.reading.value).toBe(false)
  expect(placing.tattoo.value?.outline).toEqual(shut)
  expect(placing.tattoo.value?.outlined).toBe(true)

  // An answer for another tattoo changes nothing held.
  placing.adopt('arm', open)
  expect(placing.tattoo.value?.outline).toEqual(shut)

  // Work that fails is counted down too.
  await expect(placing.track(Promise.reject(new Error('refused')))).rejects.toThrow('refused')
  expect(placing.reading.value).toBe(false)
})

spec('ui:direct:a-cut-does-not-offer-the-flag', async () => {
  const { ports, saved } = server(undefined, named({ kind: 'cut', cut_from: PLACE.digest }))
  const placing = usePlacing(PLACE, ports)
  await placing.load('arm')

  placing.setNotOnPhoto(true)
  await placing.settled()

  expect(saved).toEqual([])
  expect(placing.mode.value).toBe('cut')
})

