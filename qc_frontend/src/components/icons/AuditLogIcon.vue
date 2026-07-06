<script setup>
import IconBase from './IconBase.vue'

defineProps({
  size: { type: Number, default: 24 },
})
</script>

<template>
  <IconBase :size="size">
    <path d="M9 11l3 3 6-6" />
    <path d="M4 5h16v14H4z" />
    <path d="M8 9h4" />
  </IconBase>
</template>
