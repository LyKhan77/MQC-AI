<script setup>
import IconBase from './IconBase.vue'

defineProps({
  size: { type: Number, default: 24 },
})
</script>

<template>
  <IconBase :size="size">
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 3" />
    <rect x="4" y="19" width="7" height="3" />
  </IconBase>
</template>
