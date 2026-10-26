import { type Ref, onBeforeMount, onMounted, onUnmounted } from 'vue'

const CONTROLS = 'button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])'

/** Return the controls `Tab` reaches in `root`, in order: enabled and drawn. */
function controls(root: Element): HTMLElement[] {
  return [...root.querySelectorAll<HTMLElement>(CONTROLS)].filter(
    (one) => !one.matches(':disabled') && one.getClientRects().length > 0,
  )
}

/** Hold the focus inside `dialog` while the calling component is mounted — `Tab`
    past its last control wraps to its first, `⇧Tab` the other way — run `outside`
    on a click on its backdrop, and give the focus back, on unmount, to where it
    was before the component mounted (design spec §1). */
export function useHeldFocus(dialog: Ref<HTMLDialogElement | null>, outside?: () => void): void {
  let found: Element | null = null

  function wrap(event: KeyboardEvent): void {
    if (event.key !== 'Tab' || !dialog.value) return
    const held = controls(dialog.value)
    if (!held.length) return
    const [first, last] = [held[0], held[held.length - 1]]
    const at = document.activeElement
    if (event.shiftKey && at === first) last.focus()
    else if (!event.shiftKey && at === last) first.focus()
    else return
    event.preventDefault()
  }

  /* The dialog itself is the backdrop's target: a click inside lands on its content. */
  function click(event: MouseEvent): void {
    if (event.target === dialog.value) outside?.()
  }

  onBeforeMount(() => {
    found = document.activeElement
  })
  onMounted(() => {
    dialog.value?.addEventListener('keydown', wrap)
    dialog.value?.addEventListener('click', click)
  })
  onUnmounted(() => {
    if (found instanceof HTMLElement && found.isConnected) found.focus()
  })
}
