<script setup lang="ts">
import { computed, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { billingState, useLiveStore } from '../stores/live'

/* The billing alert's way out (design spec J8b, J8c), on its own page: a pod may
   bill with no batch. Each way ends in Check again, which asks gpunit; an alert
   clears only on its word. */
const live = useLiveStore()
const { billing, renderRunning, renderConfirmed, sessionsRefusal } = storeToRefs(live)
const refusal = ref<string | null>(null)
const state = computed(() =>
  billingState(billing.value, renderRunning.value, renderConfirmed.value),
)

async function check(): Promise<void> {
  refusal.value = null
  try {
    await live.checkBilling()
  } catch (reason) {
    refusal.value = (reason as Error).message
  }
}
</script>

<template>
  <section class="session" data-billing>
    <span class="section-label">Billing</span>
    <p v-if="refusal" class="session__refusal"><span class="refusal__mark" />{{ refusal }}</p>
    <p v-if="!renderConfirmed" class="session__refusal">
      <span class="refusal__mark" />Running renders are unconfirmed: {{ sessionsRefusal }}
    </p>
    <div v-if="state === 'alert'" class="session__alert">
      <p v-if="billing?.pod">
        <span class="refusal__mark" />A pod may still be billing.
        <span class="mono">uv run --env-file .env gpunit down</span>, or stop it in RunPod's
        console, then Check again.
      </p>
      <p v-if="billing?.volume?.state === 'band'">
        <span class="refusal__mark" />The window volume may still be billing.
        <span class="mono">uv run --env-file .env gpunit volume down</span>, then Check again.
      </p>
      <button class="btn btn-primary" type="button" @click="check">Check again</button>
    </div>
    <p v-else-if="state === 'running'" class="session__refusal">A render session is running.</p>
    <p v-else-if="state === 'pending'" class="mono">Checking billing…</p>
    <p v-else-if="state === 'open'" class="mono">The window volume is open and billing.</p>
    <p v-else-if="state === 'quiet'" class="session__quiet" data-quiet>Nothing is billing.</p>
  </section>
</template>
