<script setup>
import IconBase from './IconBase.vue'

defineProps({
  size: { type: Number, default: 24 },
})
</script>

<template>
  <IconBase :size="size">
    <path d="M3 12l4.5-7 9 0L21 12l-4.5 7h-9z" />
    <circle cx="12" cy="12" r="2" />
  </IconBase>
</template>
