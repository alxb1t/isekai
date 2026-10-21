import { ref } from 'vue'
import { approve as post } from '../api'
import type { Place } from '../api'

/**
 * Approval: one `POST`, and the pipeline decides.
 *
 * **Validation is the server's answer, not the client's guess.** `approve()` is
 * the only writer of an approved artifact whatever calls it, so the only thing
 * this surface controls is what the draft contained when the button was pressed.
 *
 * A refused approve leaves the draft exactly as it was -- the failure is
 * confusing prose, never lost work.
 */
export function useApproval() {
  const at = ref<number | null>(null)
  const refusal = ref<string | null>(null)
  const working = ref(false)

  function forget(): void {
    at.value = null
    refusal.value = null
  }

  /** Approve the draft at `place`, as of the `saved` receipt the page holds. */
  async function approve(place: Place, saved: number | null): Promise<boolean> {
    working.value = true
    try {
      const receipt = await post(place, saved)
      at.value = receipt.at
      refusal.value = null
      return true
    } catch (reason) {
      refusal.value = (reason as Error).message
      return false
    } finally {
      working.value = false
    }
  }

  return { at, refusal, working, approve, forget }
}
