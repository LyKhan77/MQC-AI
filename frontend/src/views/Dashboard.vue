<script setup>
import { Users, Package, CheckCircle, AlertTriangle, TrendingUp, Activity } from 'lucide-vue-next';
</script>

<template>
  <div class="space-y-6">
    <!-- Header Section -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-primary dark:text-gray-100 tracking-tight">Factory Status</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Real-time overview of production metrics.</p>
      </div>
      <div class="flex gap-3">
        <button class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-lg text-sm font-medium text-primary dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors shadow-sm">
          <Activity class="w-4 h-4 text-gray-400" />
          System Health: Good
        </button>
      </div>
    </div>

    <!-- Widgets Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      
      <!-- Occupancy Widget -->
      <div class="bg-white dark:bg-dark-surface p-6 rounded-xl shadow-sm border border-gray-200 dark:border-dark-border hover:shadow-md transition-shadow relative overflow-hidden group">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Occupancy</h3>
            <span class="text-xs text-success font-medium bg-green-50 dark:bg-green-900/20 px-2 py-0.5 rounded-full mt-1 inline-block">● Live Monitor</span>
          </div>
          <div class="p-2 bg-primary/10 dark:bg-white/5 rounded-lg text-primary dark:text-white group-hover:bg-primary group-hover:text-white transition-colors">
            <Users class="w-5 h-5" />
          </div>
        </div>
        <div class="flex items-baseline gap-2">
          <span class="text-3xl font-bold text-primary dark:text-gray-100">--</span>
          <span class="text-sm text-gray-400 font-medium">persons</span>
        </div>
        <div class="mt-4 pt-4 border-t border-gray-50 dark:border-white/5 flex justify-between items-center">
           <span class="text-xs text-gray-400">Zone A: Welding</span>
           <span class="text-xs font-semibold text-gray-600 dark:text-gray-400">0 Alerts</span>
        </div>
      </div>

      <!-- Production Widget -->
      <div class="bg-white dark:bg-dark-surface p-6 rounded-xl shadow-sm border border-gray-200 dark:border-dark-border hover:shadow-md transition-shadow group">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Daily Output</h3>
            <span class="text-xs text-accent font-medium bg-blue-50 dark:bg-blue-900/20 px-2 py-0.5 rounded-full mt-1 inline-block">↑ 12% vs ytd</span>
          </div>
          <div class="p-2 bg-primary/10 dark:bg-white/5 rounded-lg text-primary dark:text-white group-hover:bg-primary group-hover:text-white transition-colors">
            <Package class="w-5 h-5" />
          </div>
        </div>
        <div class="flex items-baseline gap-2">
          <span class="text-3xl font-bold text-primary dark:text-gray-100">--</span>
          <span class="text-sm text-gray-400 font-medium">units</span>
        </div>
        <div class="mt-4 pt-4 border-t border-gray-50 dark:border-white/5">
           <div class="h-1.5 w-full bg-gray-100 dark:bg-white/10 rounded-full overflow-hidden">
             <div class="h-full bg-primary dark:bg-gray-400 w-0 animate-pulse"></div>
           </div>
           <p class="text-xs text-gray-400 mt-2 text-right">Target: 2,500</p>
        </div>
      </div>

      <!-- QC Pass Rate -->
      <div class="bg-white dark:bg-dark-surface p-6 rounded-xl shadow-sm border border-gray-200 dark:border-dark-border hover:shadow-md transition-shadow group">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">QC Pass Rate</h3>
            <span class="text-xs text-gray-400 mt-1 block">Last 24 Hours</span>
          </div>
          <div class="p-2 bg-green-50 dark:bg-green-900/20 rounded-lg text-success group-hover:bg-success group-hover:text-white transition-colors">
            <CheckCircle class="w-5 h-5" />
          </div>
        </div>
        <div class="flex items-baseline gap-2">
          <span class="text-3xl font-bold text-primary dark:text-gray-100">--</span>
          <span class="text-sm text-gray-400 font-medium">%</span>
        </div>
        <div class="mt-4 pt-4 border-t border-gray-50 dark:border-white/5 flex gap-2">
           <span class="px-2 py-1 text-xs font-medium bg-red-50 dark:bg-red-900/20 text-error rounded">NG: --</span>
           <span class="px-2 py-1 text-xs font-medium bg-green-50 dark:bg-green-900/20 text-success rounded">OK: --</span>
        </div>
      </div>

      <!-- Critical Alerts -->
      <div class="bg-white dark:bg-dark-surface p-6 rounded-xl shadow-sm border border-red-100 dark:border-red-900/30 hover:shadow-md transition-shadow relative group">
        <div class="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-error/10 to-transparent rounded-bl-full -mr-4 -mt-4"></div>
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="text-sm font-medium text-error uppercase tracking-wide">Critical Alerts</h3>
            <span class="text-xs text-red-400 mt-1 block">Requires Attention</span>
          </div>
          <div class="p-2 bg-red-50 dark:bg-red-900/20 rounded-lg text-error z-10 group-hover:bg-error group-hover:text-white transition-colors">
            <AlertTriangle class="w-5 h-5" />
          </div>
        </div>
        <div class="flex items-baseline gap-2">
          <span class="text-3xl font-bold text-primary dark:text-gray-100">0</span>
          <span class="text-sm text-gray-400 font-medium">active</span>
        </div>
        <div class="mt-4 pt-4 border-t border-gray-50 dark:border-white/5">
           <p class="text-xs text-gray-400">All systems operating normally.</p>
        </div>
      </div>

    </div>

    <!-- Placeholder for Next Feature -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 bg-white dark:bg-dark-surface rounded-xl shadow-sm border border-gray-200 dark:border-dark-border p-6 min-h-[300px] flex flex-col justify-center items-center text-gray-400 border-dashed dark:border-white/10">
            <TrendingUp class="w-12 h-12 mb-3 text-gray-300 dark:text-gray-600" />
            <span class="font-medium">Production Analytics Chart</span>
            <span class="text-xs mt-1">Waiting for data stream...</span>
        </div>
        <div class="bg-white dark:bg-dark-surface rounded-xl shadow-sm border border-gray-200 dark:border-dark-border p-6 min-h-[300px] flex flex-col justify-center items-center text-gray-400 border-dashed dark:border-white/10">
            <Activity class="w-12 h-12 mb-3 text-gray-300 dark:text-gray-600" />
             <span class="font-medium">Recent Activity Log</span>
             <span class="text-xs mt-1">No recent events</span>
        </div>
    </div>
  </div>
</template>
