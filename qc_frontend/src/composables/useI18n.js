import { ref, computed } from 'vue'
import id from '../assets/locales/id.js'
import en from '../assets/locales/en.js'

const STORAGE_KEY = 'mqc-lang'
const messages = { id, en }
const locale = ref('id')

function init() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'id' || saved === 'en') {
    locale.value = saved
  }
}

init()

function deepGet(obj, path) {
  return path.split('.').reduce((acc, key) => acc?.[key], obj)
}

function t(key) {
  const msg = deepGet(messages[locale.value], key)
  return msg ?? deepGet(messages.en, key) ?? key
}

function setLocale(val) {
  if (val !== 'id' && val !== 'en') return
  locale.value = val
  localStorage.setItem(STORAGE_KEY, val)
  document.documentElement.setAttribute('lang', val)
}

export function useI18n() {
  return { locale, t, setLocale }
}
