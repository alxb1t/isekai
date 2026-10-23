import { computed, ref, watch } from 'vue'
import { renderOffer } from '../api'
import type { RenderOffer } from '../types'
import { useLive } from './useLive'

/* A batch's Render offer, for every screen that draws the Render bar: the images
   it lacks, why Render is disabled or null, why a count is refused or null, and
   the dialog, which has no URL of its own (design spec §1 rule 8). An offer that
   cannot be read is refused, so its reason is shown. A job that starts or ends,
   or a pod alert raised or cleared, changes the offer, so each reads it again.
   `rendering` is a render session running for this batch, not another's. */
export function useRenderOffer(batch: string) {
  const { job, billing, renderRunning } = useLive()
  const rendering = computed(() => renderRunning.value && job.value?.batch === batch)
  const offer = ref<RenderOffer>({ disabled: null, images: 0, refused: null })
  const dialog = ref(false)

  async function check(): Promise<void> {
    try {
      offer.value = await renderOffer(batch)
    } catch (reason) {
      const message = (reason as Error).message
      offer.value = { disabled: message, images: offer.value.images, refused: message }
    }
  }

  function open(): void {
    if (offer.value.images > 0 && offer.value.disabled === null) dialog.value = true
  }

  function close(): void {
    dialog.value = false
    void check()
  }

  watch(job, (slot, before) => {
    if ((before?.state === 'running') !== (slot?.state === 'running')) void check()
  })
  watch(
    () => billing.value?.pod,
    () => void check(),
  )

  return { offer, dialog, rendering, check, open, close }
}
