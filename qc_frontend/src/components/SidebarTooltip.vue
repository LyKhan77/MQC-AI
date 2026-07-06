<script setup>
defineProps({
  label: { type: String, required: true },
})
</script>

<template>
  <div class="tooltip-wrapper">
    <slot />
    <div class="tooltip" role="tooltip">{{ label }}</div>
  </div>
</template>

<style scoped>
.tooltip-wrapper {
  position: relative;
  display: flex;
}

.tooltip {
  position: absolute;
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
  background: var(--color-inverse-canvas);
  color: var(--color-inverse-ink);
  padding: 8px 12px;
  font-size: 13px;
  letter-spacing: 0.16px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  z-index: 100;
}

.tooltip-wrapper:hover .tooltip,
.tooltip-wrapper:focus-within .tooltip {
  opacity: 1;
}

@media (prefers-reduced-motion: reduce) {
  .tooltip {
    transition: none;
  }
}
</style>
