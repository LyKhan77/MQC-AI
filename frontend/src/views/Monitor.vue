<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { cameraService } from '../services/cameraService';
import socket from '../services/socket';
import VueApexCharts from 'vue3-apexcharts';
import { 
  Maximize2, 
  Settings, 
  Users, 
  AlertTriangle, 
  Video,
  Grid
} from 'lucide-vue-next';

// --- STATE ---
const cameras = ref([]);
const activeCameraId = ref(null);
const occupancyData = ref({}); // { camera_uuid: currentCount }

// Chart Config
const chartSeries = ref([{ name: 'Occupancy', data: [] }]);
const chartOptions = computed(() => ({
  chart: {
    type: 'bar',
    toolbar: { show: false },
    foreColor: '#9ca3af', // Gray-400
    animations: { enabled: true, easing: 'easeinout', speed: 800 }
  },
  plotOptions: {
    bar: { borderRadius: 4, columnWidth: '60%', distributed: true }
  },
  colors: ['#0081A7', '#00AFB9', '#564D4D', '#F59E0B', '#EF4444'],
  xaxis: {
    categories: cameras.value.map(c => c.area_name || c.name),
    labels: { style: { fontSize: '12px' } }
  },
  yaxis: {
    max: 15,
    title: { text: 'Person Count' }
  },
  grid: { borderColor: '#f3f4f6' },
  tooltip: { theme: 'dark' },
  legend: { show: false }
}));

// --- LOGIC ---
const loadData = async () => {
  try {
    cameras.value = await cameraService.getAll();
    if (cameras.value.length > 0) {
      activeCameraId.value = cameras.value[0].camera_uuid;
    }
  } catch (error) {
    console.error('Failed to load cameras:', error);
  }
};

const activeCamera = computed(() => 
  cameras.value.find(c => c.camera_uuid === activeCameraId.value) || {}
);

const getStatus = (count, max) => {
  if (count > max) return 'CRITICAL';
  if (count > max * 0.8) return 'WARNING';
  return 'NORMAL';
};

// Listen for real-time stats updates via WebSocket
socket.on('stats_update', (payload) => {
  if (payload && payload.data) {
    // Update occupancy data
    const newSeriesData = [];
    
    payload.data.forEach(cam => {
      occupancyData.value[cam.camera_uuid] = cam.current_count;
      newSeriesData.push(cam.current_count);
    });
    
    // Update chart
    chartSeries.value = [{ data: newSeriesData }];
  }
});

onMounted(() => {
  loadData();
  socket.connect();
});

onUnmounted(() => {
  socket.off('stats_update');
  socket.disconnect();
});
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-8rem)] gap-6">
    
    <!-- Top Bar: Header Only -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-primary dark:text-white flex items-center gap-2">
          <Video class="w-6 h-6 text-accent" />
          Crowd Control
        </h1>
        <p class="text-sm text-gray-500 mt-1">Select an active feed from strip below.</p>
      </div>
      
      <!-- Quick Actions -->
      <router-link to="/settings" class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-white/5 border border-gray-200 dark:border-dark-border rounded-lg text-sm font-medium hover:bg-gray-50 dark:hover:bg-white/10 transition-colors">
        <Settings class="w-4 h-4 text-gray-500" />
        Configure Cameras
      </router-link>
    </div>

    <!-- Main Content -->
    <div class="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
      
      <!-- Left: Video Feed & Thumbnail Strip -->
      <div class="lg:col-span-2 flex flex-col gap-4 min-h-0">
        
        <!-- Main Video Player -->
        <div class="flex-1 bg-black rounded-xl overflow-hidden relative shadow-lg flex flex-col group min-h-[400px]">
          <div class="flex-1 relative bg-gray-900 flex items-center justify-center">
              <!-- Real Stream -->
              <img 
                v-if="activeCameraId"
                :src="cameraService.getVideoStreamUrl(activeCameraId)" 
                class="absolute inset-0 w-full h-full object-cover"
                alt="Camera Stream"
              />
              
              <!-- Camera Info Overlay -->
              <div class="absolute top-4 left-4 bg-black/60 backdrop-blur px-3 py-1 rounded text-xs font-mono text-white flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                LIVE: {{ activeCamera.name }}
              </div>

              <!-- Camera Info Overlay -->
              <div class="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                <h2 class="text-white font-bold text-lg">{{ activeCamera.name }}</h2>
                <p class="text-gray-300 text-sm">{{ activeCamera.area_name }}</p>
              </div>
          </div>
        </div>

        <!-- Thumbnail Strip (Scrollable) -->
        <div class="h-24 flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
          <button 
            v-for="cam in cameras" 
            :key="cam.camera_uuid"
            @click="activeCameraId = cam.camera_uuid"
            class="flex-shrink-0 w-40 relative rounded-lg overflow-hidden border-2 transition-all group"
            :class="activeCameraId === cam.camera_uuid ? 'border-accent ring-2 ring-accent/30' : 'border-transparent opacity-70 hover:opacity-100'"
          >
            <img :src="cameraService.getVideoStreamUrl(cam.camera_uuid)" class="w-full h-full object-cover" />
            
            <!-- Status Dot -->
            <div class="absolute top-2 right-2 w-3 h-3 rounded-full border border-white shadow-sm"
              :class="{
                'bg-success': getStatus(occupancyData[cam.camera_uuid], cam.max_capacity) === 'NORMAL',
                'bg-warning': getStatus(occupancyData[cam.camera_uuid], cam.max_capacity) === 'WARNING',
                'bg-error': getStatus(occupancyData[cam.camera_uuid], cam.max_capacity) === 'CRITICAL',
              }"
            ></div>

            <!-- Label -->
            <div class="absolute bottom-0 inset-x-0 bg-black/70 p-1.5 text-center">
              <p class="text-[10px] text-white font-medium truncate">{{ cam.name }}</p>
            </div>
          </button>

          <!-- Add Camera Shortcut -->
          <router-link to="/settings" class="flex-shrink-0 w-24 flex flex-col items-center justify-center bg-gray-100 dark:bg-white/5 rounded-lg border border-dashed border-gray-300 dark:border-white/20 text-gray-400 hover:text-accent hover:border-accent transition-colors">
            <Settings class="w-6 h-6 mb-1" />
            <span class="text-[10px]">Add Cam</span>
          </router-link>
        </div>

      </div>

      <!-- Right: Analytics Panel -->
      <div class="flex flex-col gap-6">
        
        <!-- Chart Section -->
        <div class="bg-white dark:bg-dark-surface p-4 rounded-xl shadow-sm border border-gray-200 dark:border-dark-border flex-1 min-h-[250px]">
          <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-4 flex items-center gap-2">
            <Users class="w-4 h-4" /> Real-time Occupancy
          </h3>
          <div class="h-[200px] w-full">
            <VueApexCharts width="100%" height="100%" type="bar" :options="chartOptions" :series="chartSeries" />
          </div>
        </div>

        <!-- Status Grid -->
        <div class="bg-white dark:bg-dark-surface p-4 rounded-xl shadow-sm border border-gray-200 dark:border-dark-border">
          <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase mb-4 flex items-center gap-2">
            <Grid class="w-4 h-4" /> Area Status
          </h3>
          
          <div class="grid grid-cols-1 gap-3 max-h-[300px] overflow-y-auto pr-1">
            <div 
              v-for="cam in cameras" 
              :key="cam.camera_uuid"
              class="flex items-center justify-between p-3 rounded-lg border transition-all"
              :class="{
                'bg-green-50 border-green-100 dark:bg-green-900/10 dark:border-green-900/30': getStatus(occupancyData[cam.camera_uuid], cam.max_capacity) === 'NORMAL',
                'bg-yellow-50 border-yellow-100 dark:bg-yellow-900/10 dark:border-yellow-900/30': getStatus(occupancyData[cam.camera_uuid], cam.max_capacity) === 'WARNING',
                'bg-red-50 border-red-100 dark:bg-red-900/10 dark:border-red-900/30': getStatus(occupancyData[cam.camera_uuid], cam.max_capacity) === 'CRITICAL',
              }"
            >
              <div>
                <p class="font-medium text-sm text-gray-800 dark:text-gray-200">{{ cam.area_name }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ cam.name }}</p>
              </div>
              <div class="text-right">
                <span class="text-lg font-bold" 
                  :class="{
                    'text-success': getStatus(occupancyData[cam.camera_uuid], cam.max_capacity) === 'NORMAL',
                    'text-warning': getStatus(occupancyData[cam.camera_uuid], cam.max_capacity) === 'WARNING',
                    'text-error': getStatus(occupancyData[cam.camera_uuid], cam.max_capacity) === 'CRITICAL',
                  }"
                >
                  {{ occupancyData[cam.camera_uuid] || 0 }}
                </span>
                <span class="text-xs text-gray-400"> / {{ cam.max_capacity }}</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
