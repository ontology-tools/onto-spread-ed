<script setup lang="ts">

import type { Release } from "../model";
import { computed } from "vue";

const props = defineProps<{
  release?: Release
  details?: {
    [key: string]: any,
    __progress?: {
      position?: [number, number]
      progress: number
      current_item?: string
      message?: string
    }
  }
  state?: "running" | "starting" | "completed" | "canceled" | "errored" | "waiting-for-user" | "pending"
}>()

const percent = computed(() => Math.round((props.details?.__progress?.progress ?? 0) * 100))

</script>

<template>
  <p>
    <slot></slot>
  </p>

  <template v-if="details && '__progress' in details && details?.__progress">
    <p class="text-secondary mb-3">
      {{ details.__progress.message ?? "Working on" }} {{ details.__progress.current_item }}
      ({{ details.__progress?.position?.[0] }}/{{ details.__progress?.position?.[1] }})
    </p>
    <div class="progress" role="progressbar">
      <div class="progress-bar"
        :class="{ 'progress-bar-animated': state == 'running' || state == 'starting', 'progress-bar-striped': state == 'running' || state == 'starting', 'bg-success': state == 'completed', 'bg-danger': state == 'canceled' || state == 'errored', }"
        :style="{ width: `${percent}%` }">{{ percent }}%
      </div>
    </div>
  </template>
  <div v-else-if="state == 'running' || state == 'starting'" class="d-flex justify-content-center mt-5">
    <div class="spinner-border text-primary" role="status" style="width: 5rem; height: 5rem">
      <span class="visually-hidden">Waiting...</span>
    </div>
  </div>
</template>

<style scoped lang="scss"></style>
