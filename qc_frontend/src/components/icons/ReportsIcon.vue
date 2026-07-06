<script setup>
import IconBase from './IconBase.vue'

defineProps({
  size: { type: Number, default: 24 },
})
</script>

<template>
  <IconBase :size="size">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <path d="M14 2v6h6" />
    <path d="M8 13h3M8 17h5" />
    <path d="M16 13v8" />
  </IconBase>
</template>
