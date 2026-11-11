<script lang="ts" setup>
import {computed} from "vue";

const props = withDefaults(defineProps<{ rows?: number, columns?: number }>(), {rows: 20, columns: 7});

const gridStyle = computed(() => ({gridTemplateColumns: `repeat(${props.columns}, minmax(0, 1fr))`}));

// Deterministic, varying cell widths so the skeleton does not look like a uniform grid
function width(row: number, col: number): string {
  return `${35 + ((row * 7 + col * 13) % 55)}%`;
}
</script>

<template>
  <div class="table-skeleton placeholder-wave" role="status">
    <span class="visually-hidden">Loading…</span>
    <div :style="gridStyle" aria-hidden="true" class="table-skeleton-row table-skeleton-header">
      <span v-for="c in columns" :key="c" class="placeholder bg-secondary" style="width: 60%"></span>
    </div>
    <div v-for="r in rows" :key="r" :style="gridStyle" aria-hidden="true" class="table-skeleton-row">
      <span v-for="c in columns" :key="c" :style="{width: width(r, c)}" class="placeholder"></span>
    </div>
  </div>
</template>

<style scoped>
.table-skeleton {
  overflow: hidden;
  border: 1px solid var(--bs-border-color);
}

.table-skeleton-row {
  display: grid;
  gap: 1rem;
  padding: 0.4rem 0.5rem;
  border-bottom: 1px solid var(--bs-border-color);
}

.table-skeleton-header {
  background: var(--bs-tertiary-bg);
  padding-block: 0.6rem;
}
</style>
