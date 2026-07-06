<script setup>
import IconBase from './IconBase.vue'

defineProps({
  size: { type: Number, default: 24 },
})
</script>

<template>
  <IconBase :size="size">
    <path d="M6 6h12v14H6z" />
    <path d="M9 6V4h6v2" />
    <path d="M9 10h6M9 14h6" />
  </IconBase>
</template>
