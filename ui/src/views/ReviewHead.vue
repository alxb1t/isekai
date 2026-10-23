<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import KeyHint from '../components/KeyHint.vue'
import LoadingSkeleton from '../components/LoadingSkeleton.vue'
import RefusalPage from '../components/RefusalPage.vue'
import { head } from '../composables/useQueue'
import { useBatchStore } from '../stores/batch'

/* A batch's Review: its head's URL takes this one's place, so the address bar
   names the sheet (design spec §4). With no head, the way to the hub. */
const props = defineProps<{ batch: string }>()
const router = useRouter()
const store = useBatchStore()
const refusal = ref<string | null>(null)
const empty = ref(false)

onMounted(async () => {
  let info
  try {
    info = await store.reloadHub()
  } catch (reason) {
    refusal.value = (reason as Error).message
    return
  }
  const at = head(info)
  if (at) void router.replace({ name: 'review', params: { batch: props.batch, ...at } })
  else empty.value = true
})
</script>

<template>
  <RefusalPage v-if="refusal" :refusal="refusal" />
  <section v-else-if="empty" class="review-head" data-review-head>
    <p>No sheet waits for review.</p>
    <RouterLink :to="{ name: 'hub', params: { batch } }" class="btn btn-secondary"
      >Hub<KeyHint command="hub" /></RouterLink
    >
  </section>
  <LoadingSkeleton v-else :reading="null" :vocabulary="0" />
</template>
