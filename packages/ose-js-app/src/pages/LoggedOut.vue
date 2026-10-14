<script setup lang="ts">
import {prefix, useMe} from "../api";

const {me} = useMe();
</script>

<template>
  <div>
    <p>You are <strong>logged out</strong>.</p>
    <p>You may also want to <a href="https://github.com/logout">sign out of GitHub</a>.</p>
  </div>
  <hr/>
  <div>
    Click <a :href="`${prefix}/login`">here</a> to log back in to <i>{{ me?.app_title }}</i> through GitHub.
  </div>
</template>
