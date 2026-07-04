<script setup>
import { ref, watch, computed } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import BaseModal from './BaseModal.vue'

const { t } = useI18n()

const props = defineProps({
  show: Boolean,
  editing: { type: Object, default: null },
  categories: { type: Array, default: () => [] },
})

const emit = defineEmits(['cancel', 'save'])

const SWATCHES = [
  '#4589ff',
  '#08bdba',
  '#24a148',
  '#f1c21b',
  '#ff832b',
  '#fa4d56',
  '#da1e28',
  '#8a3ffc',
  '#d12771',
  '#9f1853',
  '#6f6f6f',
  '#198038',
]

const name = ref('')
const category = ref('coating')
const color = ref(SWATCHES[0])
const newCategory = ref('')

const categoryList = computed(() => {
  const base = ['coating', 'welding', ...props.categories]
  if (category.value && category.value !== '__add__') base.push(category.value)
  return [...new Set(base)]
})

const isAddingCategory = computed(() => category.value === '__add__')

function onCategoryChange() {
  if (category.value === '__add__') newCategory.value = ''
}

watch(
  () => props.show,
  (open) => {
    if (!open) return
    name.value = props.editing?.name ?? ''
    category.value = props.editing?.category ?? 'coating'
    color.value = props.editing?.color ?? SWATCHES[0]
    newCategory.value = ''
  },
  { immediate: true },
)

function save() {
  const chosenCategory = isAddingCategory.value ? newCategory.value.trim() : category.value.trim()
  emit('save', { name: name.value.trim(), category: chosenCategory || 'coating', color: color.value })
}
</script>

<template>
  <BaseModal
    :show="show"
    :title="editing ? t('defectClasses.editTitle') : t('defectClasses.addTitle')"
    @close="emit('cancel')"
  >
    <div class="form-row">
      <label>{{ t('defectClasses.name') }}</label>
      <input v-model="name" class="text-input" :placeholder="t('defectClasses.namePlaceholder')" />
    </div>
    <div class="form-row">
      <label>{{ t('defectClasses.category') }}</label>
      <select v-model="category" class="text-input" @change="onCategoryChange">
        <option v-for="c in categoryList" :key="c" :value="c">{{ c }}</option>
        <option value="__add__">{{ t('defectClasses.addCategory') }}</option>
      </select>
      <input
        v-if="isAddingCategory"
        v-model="newCategory"
        class="text-input"
        :placeholder="t('defectClasses.newCategoryPrompt')"
      />
    </div>
    <div class="form-row">
      <label>{{ t('defectClasses.color') }}</label>
      <div class="swatches">
        <button
          v-for="s in SWATCHES"
          :key="s"
          type="button"
          :class="['swatch', { active: color === s }]"
          :style="{ background: s }"
          @click="color = s"
        ></button>
      </div>
    </div>
    <template #actions>
      <button class="btn-ghost" @click="emit('cancel')">{{ t('common.cancel') }}</button>
      <button class="btn-primary" :disabled="!name.trim()" @click="save">{{ t('common.save') }}</button>
    </template>
  </BaseModal>
</template>

<style scoped>
.form-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 16px;
}
.form-row label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
}
.text-input {
  padding: 8px 12px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-bottom: 2px solid var(--color-hairline);
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 15px;
  outline: none;
}
.text-input:focus {
  border-bottom-color: var(--color-primary);
}
.swatches {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.swatch {
  width: 24px;
  height: 24px;
  border: 1px solid var(--color-hairline);
  border-radius: 0;
  cursor: pointer;
}
.swatch.active {
  outline: 2px solid var(--color-ink);
  outline-offset: 1px;
}
.btn-ghost {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink);
  cursor: pointer;
  font-size: 15px;
}
.btn-primary {
  padding: 8px 16px;
  background: var(--color-primary);
  border: 1px solid var(--color-primary);
  color: var(--color-on-primary);
  cursor: pointer;
  font-size: 15px;
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
