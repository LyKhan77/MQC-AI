<script setup>
import IconBase from './IconBase.vue'

defineProps({
  size: { type: Number, default: 24 },
})
</script>

<template>
  <IconBase :size="size">
    <rect x="3" y="10" width="7" height="10" />
    <rect x="14" y="10" width="7" height="10" />
    <path d="M6 10V6h14v4" />
  </IconBase>
</template>
