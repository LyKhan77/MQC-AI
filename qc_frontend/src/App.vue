<template>
  <div class="app-wrapper">
    <nav class="top-nav">
      <span class="nav-brand">GSPE MQC-AI</span>
      <router-link to="/live" class="nav-link">Live Edge Monitor</router-link>
      <router-link to="/qc" class="nav-link">QC Studio</router-link>
    </nav>
    <div class="router-view-container">
      <router-view></router-view>
    </div>
  </div>
</template>

<style scoped>
.app-wrapper { display: flex; flex-direction: column; height: 100vh; }
.router-view-container { flex: 1; overflow: hidden; }
</style>
