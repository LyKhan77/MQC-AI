<script setup>
import IconBase from './IconBase.vue'

defineProps({
  size: { type: Number, default: 24 },
})
</script>

<template>
  <IconBase :size="size">
    <rect x="3" y="5" width="18" height="14" />
    <circle cx="8.5" cy="10" r="1.5" />
    <path d="M3 16l5-5 4 4 7-7" />
  </IconBase>
</template>
