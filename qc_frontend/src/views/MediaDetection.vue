<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '../composables/useI18n.js'
import {
  detectImage,
  uploadVideo,
  videoStreamUrl,
  processImage,
  extractVideo,
  videoExtractStatus,
  listDetectCrops,
  approveDetectCrops,
} from '../api/detect.js'
import { submitBatch } from '../api/batches.js'
import CropReviewDialog from '../components/CropReviewDialog.vue'

const { t } = useI18n()
const router = useRouter()

const purpose = ref('test')
const mode = ref('image')
const busy = ref(false)
const error = ref('')
const imageResult = ref(null)
const videoUrl = ref('')
const progressText = ref('')

const showReview = ref(false)
const reviewCrops = ref([])
const sessionKey = ref('')

function reset() {
  error.value = ''
  imageResult.value = null
  videoUrl.value = ''
  progressText.value = ''
  reviewCrops.value = []
  sessionKey.value = ''
}

async function onFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  busy.value = true
  reset()
  try {
    if (purpose.value === 'test') {
      if (mode.value === 'image') imageResult.value = await detectImage(file)
      else videoUrl.value = videoStreamUrl((await uploadVideo(file)).video_id)
    } else if (mode.value === 'image') {
      const res = await processImage(file)
      sessionKey.value = res.key
      reviewCrops.value = res.crop_urls
      showReview.value = true
    } else {
      const { video_id } = await uploadVideo(file)
      sessionKey.value = video_id
      await extractVideo(video_id)
      await pollExtract(video_id)
    }
  } catch (err) {
    error.value = err.message || t('common.error')
  } finally {
    busy.value = false
  }
}

async function pollExtract(videoId) {
  while (true) {
    const st = await videoExtractStatus(videoId)
    progressText.value = `${st.progress.done}/${st.progress.total}`
    if (st.status === 'done') break
    if (st.status === 'failed') throw new Error(st.error || t('common.error'))
    await new Promise((r) => setTimeout(r, 1000))
  }
  const crops = await listDetectCrops(videoId)
  reviewCrops.value = crops.crop_urls
  showReview.value = true
}

async function onReviewConfirm({ batchName, selectedFiles }) {
  try {
    const approved = await approveDetectCrops(sessionKey.value, selectedFiles)
    const { batch_id } = await submitBatch({ batchName, sourcePath: approved.folder, cameraId: null })
    showReview.value = false
    router.push({ name: 'qc', query: { batch: batch_id } })
  } catch (err) {
    error.value = err.message || t('common.error')
  }
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('media.title') }}</h2>
      <p class="page-subtitle">{{ t('media.subtitle') }}</p>
    </div>

    <div class="mode-bar">
      <button :class="{ active: purpose === 'test' }" @click="purpose = 'test'; reset()">
        {{ t('media.purposeTest') }}
      </button>
      <button :class="{ active: purpose === 'process' }" @click="purpose = 'process'; reset()">
        {{ t('media.purposeProcess') }}
      </button>
    </div>

    <div class="mode-bar">
      <button :class="{ active: mode === 'image' }" @click="mode = 'image'; reset()">{{ t('media.image') }}</button>
      <button :class="{ active: mode === 'video' }" @click="mode = 'video'; reset()">{{ t('media.video') }}</button>
      <input type="file" :accept="mode === 'image' ? 'image/*' : 'video/*'" @change="onFile" />
    </div>

    <p v-if="busy" class="hint">{{ progressText || t('media.running') }}</p>
    <p v-if="error" class="error-msg">{{ error }}</p>

    <div v-if="imageResult" class="result">
      <img :src="`data:image/jpeg;base64,${imageResult.image}`" class="result-img" />
      <p class="mono">{{ t('media.count') }}: {{ imageResult.count }}</p>
      <ul class="det-list">
        <li v-for="(d, i) in imageResult.detections" :key="i" class="mono">
          {{ d.label }} - {{ (d.confidence * 100).toFixed(0) }}%
        </li>
      </ul>
    </div>

    <div v-if="videoUrl" class="result">
      <img :src="videoUrl" class="result-img" />
    </div>

    <CropReviewDialog
      :show="showReview"
      :crops="reviewCrops"
      :error="error"
      @cancel="showReview = false"
      @confirm="onReviewConfirm"
    />
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
