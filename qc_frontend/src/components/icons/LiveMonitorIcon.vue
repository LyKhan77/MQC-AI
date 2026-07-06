<script setup>
import IconBase from './IconBase.vue'

defineProps({
  size: { type: Number, default: 24 },
})
</script>

<template>
  <IconBase :size="size">
    <rect x="2" y="6" width="20" height="12" rx="1" />
    <circle cx="12" cy="12" r="3" />
    <path d="M7 3h10" />
  </IconBase>
</template>
