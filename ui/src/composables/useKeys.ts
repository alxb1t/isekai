import { onMounted, onUnmounted } from 'vue'
import { type Command, type Scope, useKeyStore } from '../stores/keys'

/** Offer `commands` in `scope` while the calling component is mounted. */
export function useKeys(scope: Scope, commands: Command[]): void {
  const store = useKeyStore()
  let layer: number | null = null
  onMounted(() => {
    layer = store.declare(scope, commands)
  })
  onUnmounted(() => {
    if (layer !== null) store.drop(layer)
  })
}
