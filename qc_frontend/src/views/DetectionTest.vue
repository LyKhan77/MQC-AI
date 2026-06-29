<script setup>
import { ref } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { detectImage, uploadVideo, videoStreamUrl } from '../api/detect.js'

const { t } = useI18n()
const mode = ref('image')
const busy = ref(false)
const error = ref('')
const imageResult = ref(null)
const videoUrl = ref('')

async function onFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  busy.value = true
  error.value = ''
  imageResult.value = null
  videoUrl.value = ''
  try {
    if (mode.value === 'image') {
      imageResult.value = await detectImage(file)
    } else {
      const { video_id } = await uploadVideo(file)
      videoUrl.value = videoStreamUrl(video_id)
    }
  } catch (err) {
    error.value = err.message || t('common.error')
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('detectTest.title') }}</h2>
      <p class="page-subtitle">{{ t('detectTest.subtitle') }}</p>
    </div>

    <div class="mode-bar">
      <button :class="{ active: mode === 'image' }" @click="mode = 'image'">{{ t('detectTest.image') }}</button>
      <button :class="{ active: mode === 'video' }" @click="mode = 'video'">{{ t('detectTest.video') }}</button>
      <input type="file" :accept="mode === 'image' ? 'image/*' : 'video/*'" @change="onFile" />
    </div>

    <p v-if="busy" class="hint">{{ t('detectTest.running') }}</p>
    <p v-if="error" class="error-msg">{{ error }}</p>

    <div v-if="imageResult" class="result">
      <img :src="`data:image/jpeg;base64,${imageResult.image}`" class="result-img" />
      <p class="mono">{{ t('detectTest.count') }}: {{ imageResult.count }}</p>
      <ul class="det-list">
        <li v-for="(d, i) in imageResult.detections" :key="i" class="mono">
          {{ d.label }} - {{ (d.confidence * 100).toFixed(0) }}%
        </li>
      </ul>
    </div>

    <div v-if="videoUrl" class="result">
      <img :src="videoUrl" class="result-img" />
    </div>
  </div>
</template>

<style scoped>
.mode-bar {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 16px;
}
.mode-bar button {
  padding: 6px 16px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink);
  cursor: pointer;
  font-size: 12px;
  letter-spacing: 0.16px;
}
.mode-bar button.active {
  background: var(--color-primary);
  color: var(--color-on-primary);
  border-color: var(--color-primary);
}
.result {
  margin-top: 12px;
}
.result-img {
  max-width: 100%;
  border: 1px solid var(--color-hairline);
  background: var(--color-ink);
}
.det-list {
  margin: 8px 0 0;
  padding-left: 18px;
  font-size: 13px;
}
.hint {
  color: var(--color-ink-subtle);
  font-size: 13px;
}
.error-msg {
  color: var(--color-error);
  font-size: 13px;
}
.mono {
  font-family: var(--font-mono);
}
</style>
