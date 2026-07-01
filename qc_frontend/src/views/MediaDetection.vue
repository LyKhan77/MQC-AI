<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '../composables/useI18n.js'
import { useSettings } from '../composables/useSettings.js'
import {
  detectImage, uploadVideo, videoStreamUrl,
  processImages, extractVideo, videoExtractStatus, listDetectCrops, approveDetectCrops,
} from '../api/detect.js'
import { submitBatch } from '../api/batches.js'
import CropReviewDialog from '../components/CropReviewDialog.vue'

const { t } = useI18n()
const router = useRouter()
const { settings } = useSettings()

const purpose = ref('test')
const mode = ref('image')

const selectedFiles = ref([])
const dragOver = ref(false)

const busy = ref(false)
const error = ref('')
const imageResults = ref([])
const videoUrl = ref('')
const progress = ref({ done: 0, total: 0 })

const showReview = ref(false)
const reviewCrops = ref([])
const sessionKey = ref('')

const accept = computed(() => (mode.value === 'image' ? 'image/*' : 'video/*'))
const hasModel = computed(() => !!settings.value.activeModel)
const hasSelection = computed(() => selectedFiles.value.length > 0)
const progressPct = computed(() =>
  progress.value.total ? Math.round((progress.value.done / progress.value.total) * 100) : 0,
)
const framesLabel = computed(() => `${t('media.frames')} ${progress.value.done} / ${progress.value.total}`)

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function revokeFile(item) {
  if (item.previewUrl) URL.revokeObjectURL(item.previewUrl)
}

function clearFiles() {
  selectedFiles.value.forEach(revokeFile)
  selectedFiles.value = []
}

function removeFile(index) {
  const [removed] = selectedFiles.value.splice(index, 1)
  if (removed) revokeFile(removed)
}

function clearResults() {
  error.value = ''
  imageResults.value = []
  videoUrl.value = ''
  progress.value = { done: 0, total: 0 }
}

function stageFiles(fileList) {
  const files = Array.from(fileList || [])
  if (!files.length) return
  const wantImage = mode.value === 'image'
  const next = []
  let invalid = false
  for (const file of files) {
    const isImage = file.type.startsWith('image/')
    const isVideo = file.type.startsWith('video/')
    if ((wantImage && !isImage) || (!wantImage && !isVideo)) {
      invalid = true
      continue
    }
    next.push({
      file,
      name: file.name,
      size: file.size,
      previewUrl: isImage ? URL.createObjectURL(file) : '',
    })
    if (!wantImage) break
  }
  if (!next.length) {
    error.value = wantImage ? t('media.invalidImage') : t('media.invalidVideo')
    return
  }
  if (invalid) error.value = wantImage ? t('media.invalidImage') : t('media.invalidVideo')
  else error.value = ''
  clearResults()
  if (wantImage) selectedFiles.value.push(...next)
  else {
    clearFiles()
    selectedFiles.value = next
  }
}

function onBrowse(e) {
  stageFiles(e.target.files)
  e.target.value = ''
}

function onDrop(e) {
  dragOver.value = false
  stageFiles(e.dataTransfer?.files)
}

function switchMode(next) {
  if (mode.value === next) return
  mode.value = next
  clearFiles()
  clearResults()
}

function switchPurpose(next) {
  if (purpose.value === next) return
  purpose.value = next
  clearResults()
}

async function run() {
  const files = selectedFiles.value
  if (!files.length || !hasModel.value) return
  busy.value = true
  clearResults()
  try {
    if (purpose.value === 'test') {
      if (mode.value === 'image') {
        progress.value = { done: 0, total: files.length }
        for (const item of files) {
          imageResults.value.push({ name: item.name, result: await detectImage(item.file) })
          progress.value = { done: imageResults.value.length, total: files.length }
        }
      } else videoUrl.value = videoStreamUrl((await uploadVideo(files[0].file)).video_id)
    } else if (mode.value === 'image') {
      const res = await processImages(files.map((item) => item.file))
      sessionKey.value = res.key
      reviewCrops.value = res.crop_urls
      showReview.value = true
    } else {
      const { video_id } = await uploadVideo(files[0].file)
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
    progress.value = st.progress
    if (st.status === 'done') break
    if (st.status === 'failed') throw new Error(st.error || t('common.error'))
    await new Promise((r) => setTimeout(r, 1000))
  }
  reviewCrops.value = (await listDetectCrops(videoId)).crop_urls
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

function confClass(c) {
  if (c >= 0.7) return 'high'
  if (c >= 0.4) return 'mid'
  return 'low'
}

onUnmounted(() => {
  clearFiles()
})
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('media.title') }}</h2>
      <p class="page-subtitle">{{ t('media.subtitle') }}</p>
    </div>

    <div class="switch-row">
      <div class="switcher" role="tablist">
        <button :class="{ active: purpose === 'test' }" @click="switchPurpose('test')">{{ t('media.purposeTest') }}</button>
        <button :class="{ active: purpose === 'process' }" @click="switchPurpose('process')">{{ t('media.purposeProcess') }}</button>
      </div>
      <div class="switcher" role="tablist">
        <button :class="{ active: mode === 'image' }" @click="switchMode('image')">{{ t('media.image') }}</button>
        <button :class="{ active: mode === 'video' }" @click="switchMode('video')">{{ t('media.video') }}</button>
      </div>
    </div>

    <p class="model-strip mono">
      <span v-if="hasModel">{{ t('media.model') }}: {{ settings.activeModel }} &middot; conf {{ settings.confidenceThreshold }}</span>
      <span v-else class="model-missing">{{ t('media.noModel') }}</span>
    </p>

    <label
      v-if="!hasSelection"
      :class="['dropzone', { over: dragOver, disabled: !hasModel }]"
      @dragover.prevent="dragOver = true"
      @dragleave.prevent="dragOver = false"
      @drop.prevent="onDrop"
    >
      <svg class="dz-icon" viewBox="0 0 32 32" aria-hidden="true"><path d="M16 4v16M9 13l7-7 7 7M6 26h20" fill="none" stroke="currentColor" stroke-width="2"/></svg>
      <span class="dz-title">{{ t('media.dropTitle') }} <span class="dz-browse">{{ t('media.browse') }}</span></span>
      <span class="dz-hint">{{ mode === 'image' ? t('media.hintImage') : t('media.hintVideo') }}</span>
      <input type="file" :accept="accept" :multiple="mode === 'image'" class="dz-input" :disabled="!hasModel" @change="onBrowse" />
    </label>

    <div v-else class="staged">
      <div class="staged-head">
        <span class="mono">{{ selectedFiles.length }} {{ t('media.selectedCount') }}</span>
        <div class="staged-actions">
          <label v-if="mode === 'image'" class="btn-secondary add-more">
            {{ t('media.addMore') }}
            <input type="file" :accept="accept" multiple class="dz-input" :disabled="!hasModel" @change="onBrowse" />
          </label>
          <button class="btn-secondary" type="button" @click="clearFiles">{{ t('media.clearAll') }}</button>
        </div>
      </div>
      <div class="staged-list">
        <div v-for="(item, index) in selectedFiles" :key="`${item.name}-${item.size}-${index}`" class="staged-row">
          <div class="staged-thumb">
            <img v-if="item.previewUrl" :src="item.previewUrl" alt="preview" />
            <svg v-else viewBox="0 0 32 32" aria-hidden="true"><path d="M4 6h24v20H4z M12 12l8 4-8 4z" fill="none" stroke="currentColor" stroke-width="2"/></svg>
          </div>
          <div class="staged-meta">
            <span class="staged-name">{{ item.name }}</span>
            <span class="staged-size mono">{{ formatSize(item.size) }}</span>
          </div>
          <button class="staged-remove" :aria-label="t('media.remove')" @click="removeFile(index)">&times;</button>
        </div>
      </div>
      <button class="btn-primary" :disabled="busy || !hasModel" @click="run">
        {{ busy ? t('media.running') : t('media.run') }}
      </button>
    </div>

    <div v-if="busy" class="progress-wrap">
      <div class="progress-track">
        <div
          class="progress-bar"
          :class="{ indeterminate: progress.total === 0 }"
          :style="progress.total ? { width: progressPct + '%' } : null"
        ></div>
      </div>
      <span v-if="progress.total" class="progress-label mono">{{ framesLabel }}</span>
    </div>

    <p v-if="error" class="error-msg">{{ error }}</p>

    <div v-for="item in imageResults" :key="item.name" class="result">
      <div class="result-canvas">
        <img :src="`data:image/jpeg;base64,${item.result.image}`" alt="annotated" />
      </div>
      <div class="result-list">
        <div class="result-list-head">
          <span>{{ item.name }}</span>
          <span class="mono">{{ item.result.count }}</span>
        </div>
        <p v-if="item.result.count === 0" class="empty-detections">{{ t('media.noDetections') }}</p>
        <ul v-else>
          <li v-for="(d, i) in item.result.detections" :key="i">
            <span class="det-label">{{ d.label }}</span>
            <span class="conf-bar"><span :class="['conf-fill', confClass(d.confidence)]" :style="{ width: (d.confidence * 100) + '%' }"></span></span>
            <span class="det-pct mono">{{ (d.confidence * 100).toFixed(0) }}%</span>
          </li>
        </ul>
      </div>
    </div>

    <div v-if="videoUrl" class="result">
      <div class="result-canvas"><img :src="videoUrl" alt="annotated video" /></div>
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
.switch-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 12px; }
.switcher { display: flex; }
.switcher button {
  padding: 8px 16px; background: var(--color-canvas); color: var(--color-ink-muted);
  border: 1px solid var(--color-hairline); border-left-width: 0; cursor: pointer;
  font-size: 14px; letter-spacing: 0.16px;
}
.switcher button:first-child { border-left-width: 1px; }
.switcher button.active { background: var(--color-primary); color: var(--color-on-primary); border-color: var(--color-primary); }
.switcher button:focus-visible { outline: 2px solid var(--color-primary); outline-offset: -2px; }

.model-strip { font-size: 12px; color: var(--color-ink-muted); margin: 0 0 16px; }
.model-missing { color: var(--color-error); }

.dropzone {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 48px 24px; border: 1px solid var(--color-hairline);
  background: var(--color-canvas); cursor: pointer; text-align: center;
  transition: background 150ms ease-out, border-color 150ms ease-out;
}
.dropzone:hover { background: var(--color-surface-1); }
.dropzone.over { border-color: var(--color-primary); border-width: 2px; background: var(--color-surface-1); padding: 47px 23px; }
.dropzone.disabled { opacity: 0.5; pointer-events: none; }
.dz-icon { width: 32px; height: 32px; color: var(--color-ink-subtle); }
.dz-title { font-size: 16px; color: var(--color-ink); }
.dz-browse { color: var(--color-primary); text-decoration: underline; }
.dz-hint { font-size: 12px; color: var(--color-ink-subtle); }
.dz-input { display: none; }

.staged { display: flex; flex-direction: column; gap: 12px; padding: 16px; border: 1px solid var(--color-hairline); background: var(--color-canvas); }
.staged-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; color: var(--color-ink-muted); font-size: 12px; }
.staged-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.add-more { position: relative; overflow: hidden; cursor: pointer; }
.staged-list { display: flex; flex-direction: column; border-top: 1px solid var(--color-hairline); }
.staged-row { display: flex; align-items: center; gap: 16px; padding: 12px 0; border-bottom: 1px solid var(--color-hairline); }
.staged-thumb { width: 56px; height: 56px; flex: none; background: var(--color-surface-1); display: flex; align-items: center; justify-content: center; }
.staged-thumb img { width: 100%; height: 100%; object-fit: cover; }
.staged-thumb svg { width: 24px; height: 24px; color: var(--color-ink-subtle); }
.staged-meta { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1; }
.staged-name { color: var(--color-ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.staged-size { font-size: 12px; color: var(--color-ink-muted); }
.staged-remove { background: transparent; border: none; color: var(--color-ink-muted); font-size: 20px; line-height: 1; cursor: pointer; padding: 4px 8px; }
.staged-remove:hover { color: var(--color-error); }

.progress-wrap { display: flex; align-items: center; gap: 12px; margin-top: 16px; }
.progress-track { flex: 1; height: 4px; background: var(--color-surface-2); overflow: hidden; }
.progress-bar { height: 100%; background: var(--color-primary); transition: width 200ms ease-out; }
.progress-bar.indeterminate { width: 40%; animation: indeterminate 1.2s ease-in-out infinite; }
@keyframes indeterminate { 0% { margin-left: -40%; } 100% { margin-left: 100%; } }
.progress-label { font-size: 12px; color: var(--color-ink-muted); }
@media (prefers-reduced-motion: reduce) {
  .progress-bar.indeterminate { animation: none; width: 100%; }
}

.error-msg { color: var(--color-error); font-size: 13px; margin-top: 12px; }

.result { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; margin-top: 24px; }
@media (max-width: 720px) { .result { grid-template-columns: 1fr; } }
.result-canvas { border: 1px solid var(--color-hairline); background: var(--color-ink); }
.result-canvas img { display: block; width: 100%; }
.result-list { border: 1px solid var(--color-hairline); padding: 16px; }
.result-list-head { display: flex; justify-content: space-between; font-size: 14px; color: var(--color-ink); margin-bottom: 12px; }
.result-list ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.result-list li { display: grid; grid-template-columns: 1fr 2fr auto; align-items: center; gap: 8px; }
.det-label { font-size: 14px; color: var(--color-ink); }
.conf-bar { height: 6px; background: var(--color-surface-2); }
.conf-fill { display: block; height: 100%; }
.conf-fill.high { background: var(--color-success); }
.conf-fill.mid { background: var(--color-warning); }
.conf-fill.low { background: var(--color-error); }
.det-pct { font-size: 12px; color: var(--color-ink-muted); }
.empty-detections { font-size: 13px; color: var(--color-ink-subtle); }
</style>
