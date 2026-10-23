import { ref, watch } from 'vue'
import { renderOffer } from '../api'
import { useLive } from './useLive'

/* A batch's Render offer, for every screen that draws the Render bar: the images
   it lacks, why Render is disabled or null, and the dialog, which has no URL of
   its own (design spec §1 rule 8). A job that ends, or a pod alert raised or
   cleared, changes the offer, so either reads it again. */
export function useRenderOffer(batch: string) {
  const { job, billing } = useLive()
  const offer = ref<{ disabled: string | null; images: number }>({ disabled: null, images: 0 })
  const dialog = ref(false)

  async function check(): Promise<void> {
    try {
      offer.value = await renderOffer(batch)
    } catch (reason) {
      offer.value = { disabled: (reason as Error).message, images: offer.value.images }
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
    if (before?.state === 'running' && slot?.state !== 'running') void check()
  })
  watch(
    () => billing.value?.pod,
    () => void check(),
  )

  return { offer, dialog, check, open, close }
}
