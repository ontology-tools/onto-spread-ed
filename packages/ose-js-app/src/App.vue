<script setup lang="ts">
import {computed, watch} from "vue";
import {useRoute, useRouter} from "vue-router";
import {prefix, useMe} from "./api";
import {layout} from "./state";

const route = useRoute();
const router = useRouter();
const {me} = useMe();

// admin implies every permission (the backend also lists them all for admins)
const can = (p: string) => !!me.value?.permissions && (me.value.permissions.includes(p) || me.value.permissions.includes("admin"));
const showAdmin = computed(() =>
    ["admin", "release", "index", "scripts", "repository-config-view"].some(can));

watch(me, m => {
  if (m) document.title = m.app_title;
});

const bare = computed(() => route.meta.bare === true);

const loginUrl = computed(() => `${prefix}/login?next=${encodeURIComponent(window.location.origin + prefix + (route.path === "/loggedout" ? "/" : route.fullPath))}`);

function setBranch(branch: string) {
  router.push({query: {...route.query, branch}});
}
</script>

<template>
  <router-view v-if="bare"/>
  <template v-else>
    <div v-if="me?.environment === 'test'" class="banner">
      <i class="fa fa-exclamation-triangle"></i> THIS IS A TEST INSTANCE WORKING WITH (POSSIBLY
      OUTDATED) COPIES OF THE ONTOLOGIES <i class="fa fa-exclamation-triangle"></i>
    </div>
    <nav class="navbar navbar-expand-lg p-3" :class="`env-${me?.environment}`" data-bs-theme="dark">
      <div class="container-fluid">
        <RouterLink class="navbar-brand" to="/">{{ me?.app_title }}</RouterLink>
        <div class="collapse navbar-collapse">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <RouterLink class="nav-link active" to="/home"><i class="fa fa-home"></i> Home</RouterLink>
            </li>
            <li v-if="showAdmin" class="nav-item">
              <RouterLink class="nav-link active" to="/admin"><i class="fa fa-gear"></i> Admin</RouterLink>
            </li>
          </ul>
        </div>

        <div v-if="me?.logged_in" class="dropdown">
          <a class="btn btn-light dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown"
             aria-expanded="false"><i class="fas fa-user"></i> {{ me.login }}</a>
          <ul class="dropdown-menu dropdown-menu-end">
            <li><a class="dropdown-item" :href="`${prefix}/logout`">Logout</a></li>
          </ul>
        </div>
        <a v-else-if="me" class="btn btn-light" :href="loginUrl">Login</a>
      </div>
    </nav>
    <div class="container-fluid">
      <div id="content">
        <div class="container-fluid">
          <nav aria-label="breadcrumb" style="margin-top: 14px">
            <ol class="breadcrumb">
              <li class="breadcrumb-item"><RouterLink to="/home">Home</RouterLink></li>
              <li v-for="(crumb, i) in layout.breadcrumb" :key="i" class="breadcrumb-item"
                  :class="{active: !crumb.to}" :aria-current="crumb.to ? undefined : 'page'">
                <RouterLink v-if="crumb.to"
                            :to="{path: crumb.to, query: layout.activeBranch ? {branch: layout.activeBranch} : {}}">
                  {{ crumb.name }}
                </RouterLink>
                <template v-else>{{ crumb.name }}</template>
              </li>
            </ol>
            <div v-if="layout.activeBranch" class="dropdown">
              <a class="btn btn-primary dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown"
                 aria-expanded="false"><i class="fas fa-code-branch"></i> {{ layout.activeBranch }}</a>
              <ul class="dropdown-menu dropdown-menu-end">
                <li v-for="branch in layout.branches" :key="branch">
                  <a class="dropdown-item branch-item" :class="{active: branch === layout.activeBranch}" href="#"
                     @click.prevent="setBranch(branch)">
                    <span class="branch-icon"><i v-if="branch === layout.mainBranch" class="fas fa-star"
                                                 title="Default branch"></i></span>
                    <span class="branch-name">{{ branch }}</span>
                  </a>
                </li>
              </ul>
            </div>
          </nav>
        </div>
        <hr/>

        <router-view/>
      </div>
      <div class="version-info">
        <small>v{{ me?.app_version }}</small>
      </div>
    </div>
  </template>
  <BToastOrchestrator/>
</template>
