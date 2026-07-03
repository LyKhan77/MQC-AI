<script setup>
import { ref, nextTick } from 'vue'

const props = defineProps({
  value: { type: String, default: '' },
  title: { type: String, default: '' },
})
const emit = defineEmits(['save'])

const editing = ref(false)
const draft = ref('')
const inputEl = ref(null)

async function start() {
  draft.value = props.value || ''
  editing.value = true
  await nextTick()
  inputEl.value?.focus()
  inputEl.value?.select()
}

function commit() {
  if (!editing.value) return
  editing.value = false
  const v = draft.value.trim()
  if (v && v !== props.value) emit('save', v)
}

function cancel() {
  editing.value = false
}
</script>

<template>
  <input
    v-if="editing"
    ref="inputEl"
    v-model="draft"
    class="edit-cell-input"
    @keyup.enter="commit"
    @keyup.esc="cancel"
    @blur="commit"
  />
  <span v-else class="editable-cell" :title="title" @dblclick="start">
    <slot>{{ value }}</slot>
  </span>
</template>

<style scoped>
.editable-cell {
  cursor: text;
}
.edit-cell-input {
  font: inherit;
  color: var(--color-ink);
  background: var(--color-surface-1);
  border: 1px solid var(--color-primary);
  padding: 2px 6px;
  width: 100%;
  outline: none;
}
</style>
