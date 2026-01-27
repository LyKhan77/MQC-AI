<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import logoMqc from '@/assets/logoMQC.png'; // Import Logo
import { 
  LayoutDashboard, 
  MonitorPlay, 
  Search, 
  Calculator, 
  ScanEye, 
  Settings, 
  LogOut,
  Menu,
  Bell,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon
} from 'lucide-vue-next';

const router = useRouter();
const isCollapsed = ref(false);
const isDark = ref(false);

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value;
};

const toggleTheme = () => {
  isDark.value = !isDark.value;
  if (isDark.value) {
    document.documentElement.classList.add('dark');
    localStorage.setItem('theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark');
    localStorage.setItem('theme', 'light');
  }
};

const handleLogout = () => {
  localStorage.removeItem('isAuthenticated');
  localStorage.removeItem('user');
  router.push('/login');
};

onMounted(() => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    isDark.value = true;
    document.documentElement.classList.add('dark');
  }
});
</script>

<template>
  <div class="flex h-screen bg-gray-50 dark:bg-dark-bg font-sans text-primary dark:text-gray-100 transition-colors duration-300">
    <!-- Sidebar -->
    <aside 
      class="bg-white dark:bg-dark-surface flex flex-col shadow-xl z-20 transition-all duration-300 ease-in-out border-r border-gray-200 dark:border-dark-border"
      :class="[ isCollapsed ? 'w-20' : 'w-72' ]"
    >
      <!-- Brand Header -->
      <div 
        class="h-16 flex items-center bg-white dark:bg-dark-surface relative group cursor-pointer border-b border-gray-100 dark:border-dark-border"
        :class="[ isCollapsed ? 'justify-center px-0' : 'px-6 justify-between' ]"
        @click="isCollapsed ? toggleSidebar() : null"
      >
        <!-- Logo & Title Group -->
        <div class="flex items-center gap-3 overflow-hidden">
          <div class="w-8 h-8 min-w-[2rem] rounded-lg bg-transparent flex items-center justify-center transition-transform duration-300 relative" :class="{ 'scale-110': isCollapsed }">
            
            <!-- Default Logo -->
            <img 
              :src="logoMqc" 
              alt="MQC Logo"
              class="w-8 h-8 object-contain transition-all duration-300 absolute"
              :class="isCollapsed ? 'group-hover:opacity-0 group-hover:rotate-90 group-hover:scale-50' : ''"
            />

            <!-- Expand Icon -->
            <ChevronRight 
              v-if="isCollapsed"
              class="w-6 h-6 text-primary dark:text-white absolute opacity-0 scale-50 transition-all duration-300 group-hover:opacity-100 group-hover:scale-100 group-hover:rotate-0 -rotate-90"
            />
          </div>
          
          <div v-show="!isCollapsed" class="flex flex-col transition-opacity duration-200">
            <span class="font-bold text-lg tracking-wide leading-none text-primary dark:text-white">MQC System</span>
            <span class="text-[10px] text-gray-400 uppercase tracking-wider mt-1 whitespace-nowrap">Manufacturing AI</span>
          </div>
        </div>

        <!-- Collapse Button -->
        <button 
          v-if="!isCollapsed"
          @click.stop="toggleSidebar"
          class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-white/10 text-gray-400 hover:text-primary dark:hover:text-white transition-colors"
        >
          <ChevronLeft class="w-5 h-5" />
        </button>
      </div>
      
      <!-- Navigation -->
      <nav class="flex-1 py-6 px-3 space-y-1 overflow-y-auto overflow-x-hidden">
        <div v-if="!isCollapsed" class="px-3 mb-2 text-xs font-bold text-gray-400 uppercase tracking-wider fade-in">Overview</div>
        <div v-else class="h-4"></div>
        
        <router-link to="/dashboard" class="group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200" active-class="bg-primary text-white shadow-md shadow-primary/30" :class="[ $route.path === '/dashboard' ? '' : 'hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 dark:text-gray-400 hover:text-primary dark:hover:text-white', isCollapsed ? 'justify-center' : '' ]" :title="isCollapsed ? 'Dashboard' : ''">
          <LayoutDashboard class="w-5 h-5 transition-colors min-w-[1.25rem]" :class="[ $route.path === '/dashboard' ? 'text-white' : 'text-gray-400 group-hover:text-primary dark:group-hover:text-white' ]" />
          <span v-show="!isCollapsed" class="text-sm font-medium whitespace-nowrap">Dashboard</span>
        </router-link>

        <div v-if="!isCollapsed" class="px-3 mt-6 mb-2 text-xs font-bold text-gray-400 uppercase tracking-wider fade-in">Modules</div>
        <div v-else class="my-4 border-t border-gray-100 dark:border-dark-border mx-2"></div>

        <router-link to="/monitor" class="group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200" active-class="bg-primary text-white shadow-md shadow-primary/30" :class="[ $route.path === '/monitor' ? '' : 'hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 dark:text-gray-400 hover:text-primary dark:hover:text-white', isCollapsed ? 'justify-center' : '' ]" :title="isCollapsed ? 'Crowd Control' : ''">
          <MonitorPlay class="w-5 h-5 transition-colors min-w-[1.25rem]" :class="[ $route.path === '/monitor' ? 'text-white' : 'text-gray-400 group-hover:text-primary dark:group-hover:text-white' ]" />
          <span v-show="!isCollapsed" class="text-sm font-medium whitespace-nowrap">Crowd Control</span>
        </router-link>

        <router-link to="/traceability" class="group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200" active-class="bg-primary text-white shadow-md shadow-primary/30" :class="[ $route.path === '/traceability' ? '' : 'hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 dark:text-gray-400 hover:text-primary dark:hover:text-white', isCollapsed ? 'justify-center' : '' ]" :title="isCollapsed ? 'Traceability' : ''">
          <Search class="w-5 h-5 transition-colors min-w-[1.25rem]" :class="[ $route.path === '/traceability' ? 'text-white' : 'text-gray-400 group-hover:text-primary dark:group-hover:text-white' ]" />
          <span v-show="!isCollapsed" class="text-sm font-medium whitespace-nowrap">Traceability</span>
        </router-link>

        <router-link to="/counting" class="group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200" active-class="bg-primary text-white shadow-md shadow-primary/30" :class="[ $route.path === '/counting' ? '' : 'hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 dark:text-gray-400 hover:text-primary dark:hover:text-white', isCollapsed ? 'justify-center' : '' ]" :title="isCollapsed ? 'Counting' : ''">
          <Calculator class="w-5 h-5 transition-colors min-w-[1.25rem]" :class="[ $route.path === '/counting' ? 'text-white' : 'text-gray-400 group-hover:text-primary dark:group-hover:text-white' ]" />
          <span v-show="!isCollapsed" class="text-sm font-medium whitespace-nowrap">Counting</span>
        </router-link>

        <router-link to="/qc-station" class="group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200" active-class="bg-primary text-white shadow-md shadow-primary/30" :class="[ $route.path === '/qc-station' ? '' : 'hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 dark:text-gray-400 hover:text-primary dark:hover:text-white', isCollapsed ? 'justify-center' : '' ]" :title="isCollapsed ? 'QC Station' : ''">
          <ScanEye class="w-5 h-5 transition-colors min-w-[1.25rem]" :class="[ $route.path === '/qc-station' ? 'text-white' : 'text-gray-400 group-hover:text-primary dark:group-hover:text-white' ]" />
          <span v-show="!isCollapsed" class="text-sm font-medium whitespace-nowrap">QC Station</span>
        </router-link>
      </nav>

      <!-- Bottom Actions -->
      <div class="p-4 border-t border-gray-100 dark:border-dark-border bg-gray-50/50 dark:bg-dark-surface space-y-2">
        
        <!-- Dark Mode Toggle -->
        <button 
          @click="toggleTheme"
          class="w-full group flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white dark:hover:bg-white/5 hover:shadow-sm text-gray-500 dark:text-gray-400 hover:text-primary dark:hover:text-white transition-all border border-transparent hover:border-gray-200 dark:hover:border-transparent"
          :class="[ isCollapsed ? 'justify-center' : '' ]"
          :title="isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
        >
          <Sun v-if="isDark" class="w-4 h-4 min-w-[1rem]" />
          <Moon v-else class="w-4 h-4 min-w-[1rem]" />
          <span v-show="!isCollapsed" class="text-sm font-medium whitespace-nowrap">{{ isDark ? 'Light Mode' : 'Dark Mode' }}</span>
        </button>

        <!-- Settings -->
        <router-link to="/settings" class="group flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white dark:hover:bg-white/5 hover:shadow-sm text-gray-500 dark:text-gray-400 hover:text-primary dark:hover:text-white transition-all border border-transparent hover:border-gray-200 dark:hover:border-transparent" :class="[ isCollapsed ? 'justify-center' : '' ]" :title="isCollapsed ? 'Settings' : ''">
          <Settings class="w-4 h-4 min-w-[1rem]" />
          <span v-show="!isCollapsed" class="text-sm font-medium whitespace-nowrap">Settings</span>
        </router-link>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0 bg-gray-50 dark:bg-dark-bg transition-colors duration-300">
      <!-- Header -->
      <header class="bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-dark-border h-16 flex items-center justify-between px-8 shadow-sm z-10 transition-colors duration-300">
        <div class="flex items-center gap-4">
          <button class="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-white/10 rounded-md text-gray-500 dark:text-gray-400">
            <Menu class="w-5 h-5" />
          </button>
          <div class="flex flex-col">
            <h2 class="text-sm font-semibold text-primary dark:text-gray-200">Dashboard Overview</h2>
            <span class="text-xs text-gray-400">Tuesday, 27 Jan 2026</span>
          </div>
        </div>

        <div class="flex items-center gap-6">
           <!-- Notifications -->
           <button class="relative p-2 text-gray-400 hover:text-primary dark:hover:text-white transition-colors">
            <Bell class="w-5 h-5" />
            <span class="absolute top-1.5 right-1.5 w-2 h-2 bg-error rounded-full border border-white dark:border-dark-surface"></span>
          </button>

          <!-- User Profile -->
          <div class="flex items-center gap-3 pl-6 border-l border-gray-200 dark:border-dark-border">
            <div class="text-right hidden md:block">
              <div class="text-sm font-medium text-primary dark:text-gray-200">Operator MQC</div>
            </div>
            <div class="w-9 h-9 rounded-full bg-primary/10 dark:bg-white/10 flex items-center justify-center text-primary dark:text-white font-bold border border-primary/20 dark:border-white/10">
              OP
            </div>
            <button @click="handleLogout" class="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-400 hover:text-error rounded-lg transition-colors ml-2" title="Logout">
              <LogOut class="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      <!-- Page View -->
      <main class="flex-1 overflow-auto p-8 scroll-smooth">
        <div class="max-w-7xl mx-auto">
          <router-view></router-view>
        </div>
      </main>
    </div>
  </div>
</template>
<style scoped>
.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
