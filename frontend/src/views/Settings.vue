<script setup>
import { ref, onMounted } from 'vue';
import { cameraService } from '../services/cameraService';
import { 
  Settings, 
  Video, 
  Cpu, 
  Save, 
  Plus, 
  Trash2, 
  Edit2, 
  X, 
  CheckCircle,
  MonitorPlay,
  Search,
  Calculator,
  ScanEye,
  Construction
} from 'lucide-vue-next';

// --- STATE ---
const activeTab = ref('monitor'); // 'general', 'monitor', 'traceability', 'counting', 'qc'
const cameras = ref([]);
const showModal = ref(false);
const editingCamera = ref(null);

// AI Global Params (Mock Store)
const aiConfig = ref({
  confidenceThreshold: 0.65,
  defaultMaxCapacity: 5,
  modelName: 'YOLOv11-Nano'
});

// Form Data for Camera
const formData = ref({
  name: '',
  area: '',
  rtsp: '',
  maxCap: 5
});

// --- METHODS ---
const loadCameras = async () => {
  try {
    const allCameras = await cameraService.getAll();
    // Transform backend format to frontend format
    cameras.value = allCameras.map(cam => ({
      id: cam.id,
      name: cam.name,
      area: cam.area_name,
      rtsp: cam.rtsp_url,
      maxCap: cam.max_capacity
    }));
  } catch (error) {
    console.error('Failed to load cameras:', error);
    alert('Failed to load cameras from server');
  }
};

const openModal = (camera = null) => {
  if (camera) {
    editingCamera.value = camera;
    formData.value = { ...camera };
  } else {
    editingCamera.value = null;
    formData.value = { name: '', area: '', rtsp: '', maxCap: aiConfig.value.defaultMaxCapacity };
  }
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  editingCamera.value = null;
};

const saveCamera = async () => {
  try {
    if (editingCamera.value) {
      await cameraService.update(editingCamera.value.id, formData.value);
    } else {
      await cameraService.add(formData.value);
    }
    await loadCameras();
    closeModal();
  } catch (error) {
    console.error('Failed to save camera:', error);
    alert('Failed to save camera: ' + (error.response?.data?.error || error.message));
  }
};

const deleteCamera = async (id) => {
  if (confirm('Are you sure you want to delete this camera? This will also stop camera thread.')) {
    try {
      await cameraService.delete(id);
      await loadCameras();
    } catch (error) {
      console.error('Failed to delete camera:', error);
      alert('Failed to delete camera: ' + (error.response?.data?.error || error.message));
    }
  }
};

const saveAiConfig = () => {
  // Future enhancement: Save to backend
  alert('AI Configuration saved locally (Backend integration coming in next phase)');
};

onMounted(() => {
  loadCameras();
});
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-primary dark:text-white flex items-center gap-2">
        <Settings class="w-6 h-6 text-accent" />
        System Configuration
      </h1>
      <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage global settings and module-specific configurations.</p>
    </div>

    <!-- Tabs Navigation (Feature Based) -->
    <div class="flex border-b border-gray-200 dark:border-dark-border overflow-x-auto">
      <button 
        @click="activeTab = 'general'"
        class="px-5 py-3 text-sm font-medium transition-colors border-b-2 whitespace-nowrap"
        :class="activeTab === 'general' ? 'border-accent text-accent' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'"
      >
        General
      </button>
      <button 
        @click="activeTab = 'monitor'"
        class="px-5 py-3 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 whitespace-nowrap"
        :class="activeTab === 'monitor' ? 'border-accent text-accent' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'"
      >
        <MonitorPlay class="w-4 h-4" />
        Crowd Control
      </button>
      <button 
        @click="activeTab = 'traceability'"
        class="px-5 py-3 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 whitespace-nowrap"
        :class="activeTab === 'traceability' ? 'border-accent text-accent' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'"
      >
        <Search class="w-4 h-4" />
        Traceability
      </button>
      <button 
        @click="activeTab = 'counting'"
        class="px-5 py-3 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 whitespace-nowrap"
        :class="activeTab === 'counting' ? 'border-accent text-accent' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'"
      >
        <Calculator class="w-4 h-4" />
        Counting
      </button>
      <button 
        @click="activeTab = 'qc'"
        class="px-5 py-3 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 whitespace-nowrap"
        :class="activeTab === 'qc' ? 'border-accent text-accent' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'"
      >
        <ScanEye class="w-4 h-4" />
        QC Station
      </button>
    </div>

    <!-- TAB CONTENT: AREA MONITOR -->
    <div v-if="activeTab === 'monitor'" class="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
      
      <!-- Section 1: Camera Management -->
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-lg font-semibold text-primary dark:text-white">Camera Management</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">Configure CCTV streams for occupancy detection.</p>
          </div>
          <button 
            @click="openModal()"
            class="flex items-center gap-2 px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors shadow-sm text-sm font-medium"
          >
            <Plus class="w-4 h-4" />
            Add Camera
          </button>
        </div>

        <div class="bg-white dark:bg-dark-surface rounded-xl shadow-sm border border-gray-200 dark:border-dark-border overflow-hidden">
          <table class="w-full text-left text-sm">
            <thead class="bg-gray-50 dark:bg-white/5 border-b border-gray-100 dark:border-dark-border">
              <tr>
                <th class="px-6 py-4 font-semibold text-gray-600 dark:text-gray-300">Camera Name</th>
                <th class="px-6 py-4 font-semibold text-gray-600 dark:text-gray-300">Area / Zone</th>
                <th class="px-6 py-4 font-semibold text-gray-600 dark:text-gray-300">RTSP URL</th>
                <th class="px-6 py-4 font-semibold text-gray-600 dark:text-gray-300 text-center">Max Capacity</th>
                <th class="px-6 py-4 font-semibold text-gray-600 dark:text-gray-300 text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100 dark:divide-dark-border">
              <tr v-for="cam in cameras" :key="cam.id" class="hover:bg-gray-50 dark:hover:bg-white/5 transition-colors">
                <td class="px-6 py-4 font-medium text-primary dark:text-white">{{ cam.name }}</td>
                <td class="px-6 py-4 text-gray-500 dark:text-gray-400">{{ cam.area }}</td>
                <td class="px-6 py-4 text-gray-400 font-mono text-xs truncate max-w-[200px]" :title="cam.rtsp">{{ cam.rtsp }}</td>
                <td class="px-6 py-4 text-center">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                    {{ cam.maxCap }}
                  </span>
                </td>
                <td class="px-6 py-4 text-right flex justify-end gap-2">
                  <button @click="openModal(cam)" class="p-1.5 text-gray-400 hover:text-accent transition-colors">
                    <Edit2 class="w-4 h-4" />
                  </button>
                  <button @click="deleteCamera(cam.id)" class="p-1.5 text-gray-400 hover:text-error transition-colors">
                    <Trash2 class="w-4 h-4" />
                  </button>
                </td>
              </tr>
              <tr v-if="cameras.length === 0">
                <td colspan="5" class="px-6 py-8 text-center text-gray-400 italic">No cameras registered. Please add one.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Section 2: AI Parameters -->
      <div class="space-y-4">
        <div class="flex justify-between items-center border-t border-gray-200 dark:border-dark-border pt-6">
           <div>
            <h2 class="text-lg font-semibold text-primary dark:text-white">AI Model Parameters</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">Fine-tune detection sensitivity.</p>
          </div>
           <button @click="saveAiConfig" class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-white/5 border border-gray-200 dark:border-dark-border rounded-lg text-sm font-medium text-primary dark:text-white hover:bg-gray-50 dark:hover:bg-white/10 transition-colors">
            <Save class="w-4 h-4" /> Save Config
          </button>
        </div>

        <div class="bg-white dark:bg-dark-surface p-6 rounded-xl shadow-sm border border-gray-200 dark:border-dark-border grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Confidence Threshold ({{ (aiConfig.confidenceThreshold * 100).toFixed(0) }}%)</label>
            <input 
              v-model="aiConfig.confidenceThreshold" 
              type="range" min="0.1" max="0.95" step="0.05"
              class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700 accent-accent"
            />
            <p class="text-xs text-gray-400 mt-2">Minimum confidence score to detect a person. Higher values reduce false positives but may miss objects.</p>
          </div>

          <div class="space-y-4">
            <div>
               <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Model Selection</label>
               <select v-model="aiConfig.modelName" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-dark-bg dark:text-white">
                 <option value="YOLOv11-Nano">YOLOv11 Nano (Fastest)</option>
                 <option value="YOLOv11-Small">YOLOv11 Small (Balanced)</option>
                 <option value="YOLOv11-Medium">YOLOv11 Medium (Accurate)</option>
               </select>
             </div>
             <div>
               <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Processing FPS Limit</label>
               <select class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-dark-bg dark:text-white">
                 <option>5 FPS (Low CPU)</option>
                 <option selected>10 FPS (Recommended)</option>
                 <option>15 FPS (High CPU)</option>
               </select>
             </div>
          </div>
        </div>
      </div>
    </div>

    <!-- OTHER TABS (Placeholders) -->
    <div v-else-if="activeTab !== 'general'" class="p-12 text-center text-gray-400 bg-white dark:bg-dark-surface rounded-xl border border-dashed border-gray-300 dark:border-dark-border animate-in fade-in">
      <Construction class="w-16 h-16 mx-auto mb-4 opacity-50 text-accent" />
      <h3 class="text-lg font-semibold text-gray-600 dark:text-gray-300">Feature Coming Soon</h3>
      <p class="max-w-md mx-auto mt-2">Configuration for <strong>{{ activeTab.charAt(0).toUpperCase() + activeTab.slice(1) }}</strong> module is currently under development.</p>
    </div>

     <!-- GENERAL TAB (Simple Placeholder) -->
     <div v-else class="space-y-6 animate-in fade-in">
        <div class="bg-white dark:bg-dark-surface p-6 rounded-xl shadow-sm border border-gray-200 dark:border-dark-border">
          <h3 class="font-bold text-lg mb-4 dark:text-white">Application Settings</h3>
          <div class="flex items-center justify-between py-3 border-b border-gray-100 dark:border-dark-border">
            <span class="text-gray-600 dark:text-gray-300">Auto-Logout Timer</span>
            <select class="border rounded px-2 py-1 dark:bg-dark-bg dark:text-white dark:border-gray-600"><option>15 mins</option><option>30 mins</option></select>
          </div>
           <div class="flex items-center justify-between py-3">
            <span class="text-gray-600 dark:text-gray-300">Notification Sound</span>
            <input type="checkbox" checked class="accent-accent w-4 h-4" />
          </div>
        </div>
     </div>

    <!-- Modal Form (Reuse existing logic) -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div class="bg-white dark:bg-dark-surface rounded-xl shadow-2xl w-full max-w-md border border-gray-200 dark:border-dark-border animate-in zoom-in-95 duration-200">
        <div class="flex justify-between items-center p-6 border-b border-gray-100 dark:border-dark-border">
          <h3 class="text-lg font-bold text-primary dark:text-white">{{ editingCamera ? 'Edit Camera' : 'Add New Camera' }}</h3>
          <button @click="closeModal" class="text-gray-400 hover:text-gray-600 dark:hover:text-white"><X class="w-5 h-5" /></button>
        </div>
        
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Camera Name</label>
            <input v-model="formData.name" type="text" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-accent dark:bg-dark-bg dark:text-white" placeholder="e.g., CCTV-01" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Area / Zone</label>
            <input v-model="formData.area" type="text" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-accent dark:bg-dark-bg dark:text-white" placeholder="e.g., Welding Station" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">RTSP Stream URL</label>
            <input v-model="formData.rtsp" type="text" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-accent dark:bg-dark-bg dark:text-white" placeholder="rtsp://ip:port/stream" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Max Capacity (Threshold)</label>
            <input v-model="formData.maxCap" type="number" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-accent dark:bg-dark-bg dark:text-white" placeholder="5" />
          </div>
        </div>

        <div class="p-6 border-t border-gray-100 dark:border-dark-border flex justify-end gap-3">
          <button @click="closeModal" class="px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/5 rounded-lg transition-colors">Cancel</button>
          <button @click="saveCamera" class="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors">Save Changes</button>
        </div>
      </div>
    </div>
  </div>
</template>
