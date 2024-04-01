<script setup lang="ts">

import {computed} from "vue";

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
}>()

const percent = computed(() => Math.round((props.details?.__progress?.progress ?? 0) * 100))

</script>

<template>
  <template v-if="release?.state == 'running'">
    <p>
      <slot></slot>
    </p>

    <template v-if="details && '__progress' in details && details?.__progress">
      <p class="text-secondary mb-3">
      Working on {{ details.__progress.current_item }} ({{ details.__progress.position[0] }}/{{ details.__progress.position[1] }})
      </p>
      <div class="progress" role="progressbar">
        <div class="progress-bar progress-bar-striped progress-bar-animated"
             :style="{width: `${percent}%`}">{{ percent }}%
        </div>
      </div>
    </template>
    <div v-else class="d-flex justify-content-center mt-5">
      <div class="spinner-border text-primary" role="status" style="width: 5rem; height: 5rem">
        <span class="visually-hidden">Waiting...</span>
      </div>
    </div>
  </template>
</template>

<style scoped lang="scss">

</style>
