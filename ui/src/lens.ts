import type { Shown } from './components/ImageViewer.vue'

export type Lens = 'photo' | 'render' | 'pair' | 'cheatsheet'

/* What the viewer shows: the rail's photographs from the open one, the image a
   draft came from alone, or the photograph and that image side by side. */
export function viewedOf(
  lens: Lens | null,
  photos: Shown[],
  opened: number,
  revised: { src: string; seed: string | null } | null,
): { images: Shown[]; start: number } | null {
  if (lens === 'photo') return { images: photos, start: opened }
  if (!revised) return null
  const { src, seed } = revised
  const render = { src, name: seed === null ? 'the image it was drafted from' : `render · seed ${seed}` }
  if (lens === 'render') return { images: [render], start: 0 }
  const photo = photos[opened]
  if (lens === 'pair' && photo) return { images: [photo, render], start: 0 }
  return null
}

/* `⌃P`: the photograph, on a revision or a draft from an image the pair; in the
   pair, the photograph alone and back. */
export function photographStep(lens: Lens | null, revised: boolean): 'photo' | 'pair' | 'close' {
  if (lens === 'pair') return 'photo'
  if (lens === 'photo' && revised) return 'pair'
  if (lens === 'photo') return 'close'
  return revised ? 'pair' : 'photo'
}
