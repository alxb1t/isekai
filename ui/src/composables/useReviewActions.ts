import { computed, ref, watch } from 'vue'
import { cancelApproval, discardDraft } from '../api'
import { rereads } from '../cancel'
import { useLiveStore } from '../stores/live'
import type { useApproval } from './useApproval'
import type { useSheet } from './useSheet'

/** What the actions read of the page, and the callback they hand back to it. */
export interface ReviewActionsPage {
  collection: () => string
  flow: () => string
  digest: () => string
  sheet: ReturnType<typeof useSheet>
  queue: { load: () => Promise<unknown> }
  approval: ReturnType<typeof useApproval>
  settled: () => void
}

/**
 * The actions an operator takes on the open sheet: read it again, approve, cancel
 * the approval, discard the draft, with the refusal they share.
 */
export function useReviewActions(page: ReviewActionsPage) {
  const live = useLiveStore()
  /* A refusal reading the sheet again after an approval, a cancel or a discard,
     or of the cancel or the discard itself: the bar says what could not be done. */
  const refused = ref<string | null>(null)
  const cancelling = ref(false)

  /* Every refusal the page meets, in the approve bar. */
  const refusal = computed(
    () =>
      page.approval.refusal.value ?? page.sheet.refusal.value ?? refused.value,
  )

  /* Read the collection and the open sheet again, staying on it; a refusal shows in
     the approve bar. */
  async function reread(id: string): Promise<void> {
    refused.value = null
    const [read] = await Promise.allSettled([page.queue.load(), page.sheet.open(id)])
    page.settled()
    if (read.status === 'rejected') refused.value = (read.reason as Error).message
  }

  /* Delete this draft, as `review --discard` does, and stay on the sheet. A save
     still in flight lands first, so the discard states the draft it moved to
     rather than racing it. */
  async function discard(): Promise<void> {
    refused.value = null
    if (!(await page.sheet.flush())) return
    try {
      await discardDraft(
        { collection: page.collection(), digest: page.digest(), flow: page.flow() },
        page.sheet.saved.value,
      )
    } catch (reason) {
      refused.value = (reason as Error).message
      return
    }
    await reread(page.digest())
  }

  async function approve(): Promise<void> {
    const id = page.digest()
    if (!id || page.sheet.readonly.value) return
    // Awaited, not merely started: the debounced write has to be ON DISK before
    // the approve `POST` goes out, or the artifact is built from the previous
    // draft and the last correction is unlinked along with it.
    //
    // **And read, not merely awaited.** A refused `PUT` used to mean a network
    // error and nothing else; it now means 409 too -- an approved input, or a
    // `saved` the disk has moved past -- so waiting for an answer nobody looks at
    // would approve the draft as of the last write that *did* land and discard
    // everything typed after it, behind a banner the operator has no reason to
    // read as "your approval is about to be wrong". `flush()` leaves the refusal
    // in the approve bar; stopping here is what makes it true.
    if (!(await page.sheet.flush())) return
    const place = { collection: page.collection(), digest: id, flow: page.flow() }
    if (!(await page.approval.approve(place, page.sheet.saved.value))) return
    // Approving is an act, not a navigation: the sheet stays, read-only.
    await reread(id)
  }

  /* Take the approval back, as `approve --cancel` does, and stay on the sheet:
     editable again, or, for a copy, on the draft open above what lies beneath,
     else the approval beneath, read-only. */
  async function cancelApprove(): Promise<void> {
    const id = page.digest()
    if (!id) return
    cancelling.value = true
    try {
      await cancelApproval({ collection: page.collection(), digest: id, flow: page.flow() })
    } catch (reason) {
      refused.value = (reason as Error).message
      return
    } finally {
      cancelling.value = false
    }
    page.approval.forget()
    await reread(id)
  }

  /* The input changed: the approval's and the refusal's answers belong to the one left. */
  function forget(): void {
    page.approval.forget()
    refused.value = null
  }

  /* The server's reason for Cancel approve follows the render slot, so an approved sheet is
     read again when a render for its collection starts or ends, or once the read in flight lands. */
  const follow = rereads(page.collection, page.sheet, () => void reread(page.digest()))
  watch(() => live.jobs.render, (after, before) => follow.moved(before, after))
  watch(() => page.sheet.loading.value, () => follow.landed())

  return { refusal, cancelling, approve, cancelApprove, discard, forget }
}
