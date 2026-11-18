import { computed, ref } from 'vue'
import { removal, reporting } from '../confirm'

/** Return the tattoo *Remove* was pressed on, and the question asked about it. */
export function useRemoval(page: {
  remove: (name: string) => Promise<unknown>
  removed: (name: string) => void
}) {
  const asking = ref<string | null>(null)
  const question = computed(() => {
    const name = asking.value
    return name === null
      ? null
      : {
          ...removal(name),
          run: reporting(() => page.remove(name), () => removed(name)),
        }
  })

  /* The picker is told of a removal by its own request, not through the dialog: a dialog dismissed
     while the request ran is gone when it settles, and the tattoo is still removed. */
  function removed(name: string): void {
    if (asking.value === name) asking.value = null
    page.removed(name)
  }

  return { asking, question }
}
