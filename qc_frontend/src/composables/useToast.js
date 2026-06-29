import { ref } from 'vue'

const message = ref('')
let timer = null

function showToast(msg, ms = 2000) {
  message.value = msg
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    message.value = ''
  }, ms)
}

export function useToast() {
  return { message, showToast }
}
