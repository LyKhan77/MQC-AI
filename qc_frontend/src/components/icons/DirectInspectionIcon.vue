<script setup>
import IconBase from './IconBase.vue'

defineProps({
  size: { type: Number, default: 24 },
})
</script>

<template>
  <IconBase :size="size">
    <rect x="6" y="6" width="12" height="12" />
    <circle cx="12" cy="12" r="3" />
    <path d="M20 20l-4.5-4.5" />
  </IconBase>
</template>
