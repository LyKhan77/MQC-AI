<script setup>
import { ref } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import TopBar from './components/TopBar.vue'

const collapsed = ref(false)
</script>

<template>
  <div class="app-shell">
    <AppSidebar :collapsed="collapsed" @toggle="collapsed = !collapsed" />
    <div class="main-area">
      <TopBar />
      <div class="content-area">
        <router-view></router-view>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-area {
  flex: 1;
  overflow: hidden;
}
</style>
