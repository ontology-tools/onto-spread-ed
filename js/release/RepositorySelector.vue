<script setup lang="ts">

defineProps<{
  repositories: { short: string, full: string }[]
}>();

const model = defineModel<string | null>()

</script>

<template>
  <div class="row align-stretch">
    <div class="col-sm-6 col-md-4 col-lg-3 m-2" v-for="item in repositories" @click="model = item.short">

      <a class="card bg-light" style="cursor: pointer; height: 100%; text-decoration: none;; border-width: 2px 2px 4px 2px" :class="{selected: modelValue == item.short}">
        <div class="section p-2 text-center fs-2" style="">
          {{ item.short }}
        </div>
        <div class="card-body text-center">
          {{ item.full }}
        </div>
      </a>
    </div>
  </div>
</template>

<style scoped lang="scss">
  .selected {
    background: darken(rgb(248, 249, 250), 20%) !important;
  }
</style>
