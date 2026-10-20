<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

/* The shell: the AppBar, the BillingBanner's slot, the route's screen and the
   JobStrip (design spec §3). Review is keyed by batch and flow, so moving to
   another run keeps the view and its autosave; another flow is a new view. */
const route = useRoute()

const batch = computed(() => (typeof route.params.batch === 'string' ? route.params.batch : null))
const place = computed(() => batch.value ?? 'library')
const screen = computed(() =>
  route.path.includes('/review/') ? 'review' : route.path.endsWith('/hub') ? 'hub' : 'home',
)
const key = computed(() =>
  screen.value === 'review' ? `${route.params.batch}/${route.params.flow}` : route.path,
)
</script>

<template>
  <div class="app">
    <header class="appbar">
      <RouterLink to="/" class="appbar__mark">isekai</RouterLink>
      <span class="appbar__place">{{ place }}</span>
      <template v-if="batch">
        <RouterLink
          :to="`/b/${batch}/hub`"
          class="appbar__tab"
          :class="{ 'appbar__tab--active': screen === 'hub' }"
          >Hub<span class="appbar__key">⌥1</span></RouterLink
        >
        <span class="appbar__tab" :class="{ 'appbar__tab--active': screen === 'review' }"
          >Review<span class="appbar__key">⌥2</span></span
        >
      </template>
    </header>
    <!-- The BillingBanner's slot: empty until a render can bill. -->
    <main class="app__screen">
      <RouterView :key="key" />
    </main>
    <footer class="jobstrip">
      <span class="jobstrip__dot" />
      <span>job · idle</span>
    </footer>
  </div>
</template>
