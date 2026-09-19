/* The static fixture the shell is built against.

   Scaffolding, and deliberately temporary: the build order puts the shell and
   the read-only sheet ahead of any data loading, so that the four status marks
   and most of the pixels are right before anything can be blamed on a fetch.
   `useBatch` and `useSheet` replace it, and it is deleted with them.

   The schema below is `flows/summon-v1/schema.json`'s, verbatim and in order. */

import type { BatchInfo, InputDetail } from './types'

export const SCHEMA = [
  'count',
  'age_band',
  'skin_ancestry',
  'hair_colour',
  'hair_silhouette',
  'eye_colour',
  'eyebrows',
  'marks',
  'clothes',
  'accessories',
  'expression',
  'gaze',
  'pose',
  'framing',
  'body_shape',
  'background',
]

export const BATCH: BatchInfo = {
  flow: 'summon-v1',
  schema: SCHEMA,
  vocabulary: 8106,
  approved: 0,
  inputs: [
    { id: 'e831676b7ccf_cowboy-shoot-1', width: 832, height: 1216, status: 'draft' },
    { id: '147ea6d5604b_full-height-1', width: 832, height: 1216, status: 'draft' },
    { id: '4965a5b47b45_cowboy-shoot-3', width: 1216, height: 832, status: 'draft' },
  ],
}

const FIELDS: Record<string, string[]> = {
  count: [],
  age_band: [],
  skin_ancestry: [],
  hair_colour: ['blonde hair'],
  hair_silhouette: ['long hair', 'waves'],
  eye_colour: ['light blue eyes'],
  eyebrows: [],
  marks: [],
  clothes: ['blouse', 'collar', 'v hanging sleeves', 'short sleeves', 'vest', 'sleeveless'],
  accessories: [],
  expression: ['smile', 'parted lips', 'teeth'],
  gaze: ['looking at viewer'],
  pose: ['standing'],
  framing: ['portrait'],
  body_shape: [],
  background: ['green background', 'grey background', 'shadow', 'white background'],
}

const PER_FIELD: Record<string, number> = Object.fromEntries(
  SCHEMA.map((name) => [
    name,
    (FIELDS[name] ?? []).reduce((sum, tag) => sum + tag.split(' ').length + 1, 0),
  ]),
)

export const DETAIL: InputDetail = {
  id: BATCH.inputs[0].id,
  width: 832,
  height: 1216,
  caption:
    'One person is in the picture, a young woman who looks to be in her early ' +
    'to mid twenties. She has long blonde hair, falling to roughly the middle ' +
    'of her ribcage, worn loose and parted slightly off centre.\n\n' +
    'She is wearing two layers. Underneath is a cream or off-white blouse with ' +
    'a small stand collar edged in lace.\n\n' +
    'The framing is a three-quarter portrait that cuts off at the waist. Her ' +
    'hands rest at her sides and the light comes from the left, fairly soft.',
  fields: FIELDS,
  readonly: false,
  draft: '001.draft.json',
  approved: null,
  saved: Date.now() / 1000,
  budget: {
    total: Object.values(PER_FIELD).reduce((a, b) => a + b, 0) + 19,
    per_field: PER_FIELD,
    overhead: 19,
  },
}
