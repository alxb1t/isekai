import { type MaybeRefOrGetter, onUnmounted, ref, toValue, watch } from 'vue'

/* The pixel size of the image at a URL, read once it loads, or null until then and while the
   URL is null. A panel needs it to place the image and its points. */
export function useNatural(src: MaybeRefOrGetter<string | null>) {
  const size = ref<{ width: number; height: number } | null>(null)
  let loading: HTMLImageElement | null = null

  function release(): void {
    if (loading) loading.onload = null
    loading = null
  }

  watch(
    () => toValue(src),
    (url) => {
      release()
      size.value = null
      if (url === null) return
      const image = new Image()
      loading = image
      image.onload = () => {
        if (loading === image) size.value = { width: image.naturalWidth, height: image.naturalHeight }
      }
      image.src = url
    },
    { immediate: true },
  )

  onUnmounted(release)
  return size
}
