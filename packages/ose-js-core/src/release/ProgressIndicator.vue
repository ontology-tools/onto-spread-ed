<script setup lang="ts">

import type { Release } from "../model";
import { computed } from "vue";
import { currentStage, releaseStages } from "./stages";

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
  stepName?: string
  stepNumber?: number
}>()

const percent = computed(() => Math.round((props.details?.__progress?.progress ?? 0) * 100))

const stepNumber = computed(() => props.stepNumber ?? releaseStages(props.release).findIndex(s => s.name === props.stepName))
const state = computed(() => props.release?.state === 'running' && currentStage(props.release) > stepNumber.value ? 'completed' : props.release?.state)

</script>

<template>
  <p>
    <slot></slot>
  </p>

  <template v-if="details && '__progress' in details && details?.__progress">
    <p class="text-secondary mb-3">
      {{ details.__progress.message ?? "Working on" }} {{ details.__progress.current_item }}
      <template v-if="details.__progress.position">
        ({{ details.__progress.position[0] }}/{{ details.__progress.position[1] }})
      </template>
    </p>
    <div class="progress" role="progressbar">
      <div class="progress-bar"
        :class="{ 'progress-bar-animated': state == 'running' || state == 'starting', 'progress-bar-striped': state == 'running' || state == 'starting', 'bg-success': state == 'completed', 'bg-danger': state == 'cancelled' || state == 'errored', }"
        :style="{ width: `${percent}%` }">{{ percent }}%
      </div>
    </div>
  </template>
  <template v-else-if="state == 'running' || state == 'starting'">
    <p class="text-secondary mb-3">{{ state == 'starting' ? 'Starting' : 'Running' }}…</p>
    <div aria-label="Step is running" class="progress" role="progressbar">
      <div class="progress-bar progress-bar-striped progress-bar-animated w-100"></div>
    </div>
  </template>
</template>

<style scoped lang="scss"></style>
