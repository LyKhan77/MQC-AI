<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import logoMqc from '@/assets/logoMQC.png'; // Import Logo
import { Lock, User, ArrowRight, AlertCircle } from 'lucide-vue-next';

const router = useRouter();
const username = ref('');
const password = ref('');
const error = ref('');
const isLoading = ref(false);

const handleLogin = async () => {
  error.value = '';
  isLoading.value = true;

  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 800));

  if (username.value === 'MQC' && password.value === 'mqc123') {
    localStorage.setItem('isAuthenticated', 'true');
    localStorage.setItem('user', 'MQC Operator');
    router.push('/dashboard');
  } else {
    error.value = 'Invalid credentials. Please try again.';
    password.value = '';
  }
  
  isLoading.value = false;
};
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-dark-bg flex items-center justify-center p-4 transition-colors duration-300">
    <div class="max-w-md w-full bg-white dark:bg-dark-surface rounded-2xl shadow-xl border border-gray-100 dark:border-dark-border overflow-hidden">
      
      <!-- Header -->
      <div class="bg-primary p-8 text-center relative overflow-hidden">
        <div class="absolute inset-0 bg-accent/20"></div>
        <div class="absolute -bottom-10 -right-10 w-40 h-40 bg-white/10 rounded-full blur-2xl"></div>
        
        <div class="relative z-10 flex flex-col items-center">
          <div class="w-20 h-20 bg-transparent flex items-center justify-center mb-2">
            <img :src="logoMqc" alt="MQC Logo" class="w-full h-full object-contain drop-shadow-lg" />
          </div>
          <h1 class="text-2xl font-bold text-white tracking-wide">MQC System</h1>
          <p class="text-gray-300 text-sm mt-1">Monitoring & Quality Control</p>
        </div>
      </div>

      <!-- Form -->
      <div class="p-8">
        <form @submit.prevent="handleLogin" class="space-y-5">
          
          <div v-if="error" class="bg-red-50 dark:bg-red-900/20 text-error text-sm p-3 rounded-lg flex items-center gap-2 animate-pulse">
            <AlertCircle class="w-4 h-4" />
            {{ error }}
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Username</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User class="h-5 w-5 text-gray-400" />
              </div>
              <input 
                v-model="username"
                type="text" 
                class="block w-full pl-10 pr-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary dark:bg-dark-bg dark:text-white transition-all outline-none" 
                placeholder="Enter username"
                required
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Password</label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock class="h-5 w-5 text-gray-400" />
              </div>
              <input 
                v-model="password"
                type="password" 
                class="block w-full pl-10 pr-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary dark:bg-dark-bg dark:text-white transition-all outline-none" 
                placeholder="••••••"
                required
              />
            </div>
          </div>

          <button 
            type="submit" 
            :disabled="isLoading"
            class="w-full flex justify-center items-center gap-2 py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition-all disabled:opacity-70 disabled:cursor-not-allowed mt-2"
          >
            <span v-if="isLoading" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <span v-else>Sign In</span>
            <ArrowRight v-if="!isLoading" class="w-4 h-4" />
          </button>
        </form>

        <div class="mt-8 text-center">
          <p class="text-xs text-gray-400">
            Restricted Access. Authorized Personnel Only.<br>
            GSPE Manufacturing Facility.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
