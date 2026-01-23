<script setup lang="ts">
import {Ref, ref} from "vue";

const body: Ref<HTMLDivElement | null> = ref(null)
let id: number | null = Math.round(Math.random() * 10000);

</script>

<template>
  <div class="collapsible-card">
    <div class="header collapsed" data-bs-toggle="collapse" :data-bs-target="'#body-' + id ">
      <div class="title">
        <slot name="title"></slot>
      </div>
      <span></span>
      <slot name="buttons"></slot>
      <i class="fa fa-chevron-up"></i>
    </div>
    <div class="body collapse" :id="'body-' + id" ref="body">
      <slot name="body"></slot>
    </div>
  </div>
</template>

<style scoped lang="scss">
.collapsible-card {
  border-width: 2px 2px 4px 2px;
  border-style: solid;
  border-color: #DDDDDD;
  border-radius: 4px;

  .header {
    padding: 14px 20px 14px 14px;
    display: flex;
    gap: 14px;
    cursor: pointer;
    border-bottom: 2px solid #DDDDDD;

    .title {
      font-size: large;
    }

    span {
      flex-grow: 1;
    }

    i {
      align-self: center;
      transition: transform 1s;
    }
  }

  .header.collapsed {
    i {
      transform: rotate(180deg);
    }

    transition: border-bottom-width;
    border-bottom-width: 0;
    transition-delay: 1s;
  }

  .body {
    margin: 14px 20px 14px 14px;
    transition: height 1s;
    box-sizing: border-box;
  }
}
</style>
