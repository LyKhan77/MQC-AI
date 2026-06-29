<script setup>
import { ref } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import TopBar from './components/TopBar.vue'
import { useToast } from './composables/useToast.js'

const collapsed = ref(false)
const { message: toastMessage } = useToast()
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
  <div v-if="toastMessage" class="app-toast">{{ toastMessage }}</div>
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

.app-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-ink);
  color: var(--color-canvas);
  padding: 10px 18px;
  font-size: 13px;
  letter-spacing: 0.16px;
  z-index: 2000;
}
</style>
