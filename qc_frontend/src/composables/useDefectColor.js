import { computed } from 'vue'
import { useDefectClasses } from './useDefectClasses.js'

export function useDefectColor() {
  const { classes } = useDefectClasses()
  const map = computed(() => {
    const m = {}
    for (const c of classes.value) m[c.name] = c.color
    return m
  })

  function colorFor(type) {
    return map.value[type] ?? 'var(--color-ink-subtle)'
  }

  return { colorFor }
}
