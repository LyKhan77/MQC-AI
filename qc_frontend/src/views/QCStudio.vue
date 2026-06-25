<script setup>
import BatchSidebar from '../components/BatchSidebar.vue'
import InspectionCanvas from '../components/InspectionCanvas.vue'
import DefectPanel from '../components/DefectPanel.vue'
</script>

<template>
  <div class="studio-layout">
    <BatchSidebar />
    <InspectionCanvas />
    <DefectPanel />
  </div>
</template>

<style scoped>
.studio-layout { display: flex; height: 100%; width: 100%; }
</style>
