<script setup>
import { Construction, ArrowLeft } from 'lucide-vue-next';

defineProps({
  title: {
    type: String,
    default: 'Feature Under Construction'
  },
  description: {
    type: String,
    default: 'We are currently working on this feature. Check back soon!'
  }
});
</script>

<template>
  <div class="flex flex-col items-center justify-center h-[calc(100vh-10rem)] text-center p-6">
    <div class="w-24 h-24 bg-gray-100 dark:bg-white/5 rounded-full flex items-center justify-center mb-6 animate-bounce">
      <Construction class="w-12 h-12 text-gray-400 dark:text-gray-500" />
    </div>
    
    <h2 class="text-3xl font-bold text-primary dark:text-white mb-3">{{ title }}</h2>
    <p class="text-gray-500 dark:text-gray-400 max-w-md mb-8">
      {{ description }}
    </p>

    <router-link 
      to="/dashboard"
      class="flex items-center gap-2 px-6 py-3 bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-lg text-primary dark:text-white font-medium hover:bg-gray-50 dark:hover:bg-white/5 transition-colors shadow-sm"
    >
      <ArrowLeft class="w-4 h-4" />
      Back to Dashboard
    </router-link>
  </div>
</template>
