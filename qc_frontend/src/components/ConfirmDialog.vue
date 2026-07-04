<script setup>
import BaseModal from './BaseModal.vue'

defineProps({
  show: Boolean,
  title: { type: String, default: '' },
  message: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Confirm' },
  cancelLabel: { type: String, default: 'Cancel' },
  danger: Boolean,
})

const emit = defineEmits(['cancel', 'confirm'])
</script>

<template>
  <BaseModal :show="show" :title="title" size="sm" @close="emit('cancel')">
    <p class="confirm-message">{{ message }}</p>
    <template #actions>
      <button class="btn-ghost" type="button" @click="emit('cancel')">{{ cancelLabel }}</button>
      <button class="btn-primary" :class="{ danger }" type="button" @click="emit('confirm')">{{ confirmLabel }}</button>
    </template>
  </BaseModal>
</template>

<style scoped>
.confirm-message {
  margin: 0;
  color: var(--color-ink);
}
.btn-ghost,
.btn-primary {
  padding: 8px 16px;
  font-family: var(--font-sans);
  font-size: 15px;
  cursor: pointer;
  border-radius: 0;
}
.btn-ghost {
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink);
}
.btn-primary {
  background: var(--color-primary);
  border: 1px solid var(--color-primary);
  color: var(--color-on-primary);
}
.btn-primary.danger {
  background: var(--color-error);
  border-color: var(--color-error);
}
</style>
