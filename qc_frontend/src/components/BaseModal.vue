<script setup>
import { onMounted, ref, watch } from 'vue'

const props = defineProps({
  show: Boolean,
  title: { type: String, default: '' },
  size: { type: String, default: 'md' },
})

const emit = defineEmits(['close'])
const dialogRef = ref(null)

function syncDialog(open) {
  const dialog = dialogRef.value
  if (!dialog) return

  if (open) {
    if (!dialog.open) {
      if (typeof dialog.showModal === 'function') dialog.showModal()
      else dialog.setAttribute('open', '')
    }
    return
  }

  if (dialog.open) {
    if (typeof dialog.close === 'function') dialog.close()
    else dialog.removeAttribute('open')
  } else {
    dialog.removeAttribute('open')
  }
}

function requestClose() {
  emit('close')
}

function onDialogClick(event) {
  if (event.target === dialogRef.value) requestClose()
}

onMounted(() => syncDialog(props.show))
watch(() => props.show, syncDialog)
</script>

<template>
  <dialog
    v-show="show"
    ref="dialogRef"
    class="dialog"
    :class="`dialog-${size}`"
    @cancel.prevent="requestClose"
    @click="onDialogClick"
  >
    <div v-if="show" class="dialog-shell">
      <header class="dialog-title-row">
        <h3 class="dialog-title">{{ title }}</h3>
        <button class="dialog-close" type="button" :aria-label="'Close'" @click="requestClose">x</button>
      </header>
      <div class="dialog-body">
        <slot />
      </div>
      <div v-if="$slots.actions" class="dialog-actions">
        <slot name="actions" />
      </div>
    </div>
  </dialog>
</template>

<style scoped>
.dialog {
  width: min(520px, calc(100vw - 32px));
  max-height: calc(100vh - 48px);
  padding: 0;
  color: var(--color-ink);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: 0;
}
.dialog-sm { width: min(420px, calc(100vw - 32px)); }
.dialog-lg { width: min(760px, calc(100vw - 32px)); }
.dialog::backdrop { background: rgba(0, 0, 0, 0.5); }
.dialog-shell { display: flex; flex-direction: column; max-height: calc(100vh - 48px); }
.dialog-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 24px;
  border-bottom: 1px solid var(--color-hairline);
}
.dialog-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.16px;
}
.dialog-close {
  width: 32px;
  height: 32px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-ink-muted);
  cursor: pointer;
}
.dialog-close:hover,
.dialog-close:focus-visible {
  color: var(--color-ink);
  border-color: var(--color-hairline);
  outline: none;
}
.dialog-body {
  padding: 24px;
  overflow: auto;
}
.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-hairline);
}
@media (prefers-reduced-motion: reduce) {
  .dialog { scroll-behavior: auto; }
}
</style>
