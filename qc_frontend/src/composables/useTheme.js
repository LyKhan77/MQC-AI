import { ref } from 'vue'

const STORAGE_KEY = 'mqc-theme'
const theme = ref('light')

function apply(val) {
  document.documentElement.setAttribute('data-theme', val)
}

function init() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'light' || saved === 'dark') {
    theme.value = saved
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    theme.value = 'dark'
  }
  apply(theme.value)
}

function toggle() {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
  localStorage.setItem(STORAGE_KEY, theme.value)
  apply(theme.value)
}

init()

export function useTheme() {
  return { theme, toggle }
}
