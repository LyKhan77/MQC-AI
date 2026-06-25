<script setup>
import { ref } from 'vue'

// ponytail: status mock; ganti dengan polling endpoint Jetson saat Edge App siap.
const status = ref({ online: false, fps: 0, tempC: 0 })
const streamUrl = ref('http://192.168.1.50:8080/stream') // MJPEG endpoint Jetson
</script>

<template>
  <div class="live-container">
    <div class="live-header">
      <h2>Live Inference — Jetson Nano</h2>
      <div class="status-bar">
        <span class="status-pill" :class="status.online ? 'on' : 'off'">
          <span class="dot"></span>{{ status.online ? 'ONLINE' : 'OFFLINE' }}
        </span>
        <span class="metric mono">FPS <b>{{ status.fps }}</b></span>
        <span class="metric mono">TEMP <b>{{ status.tempC }}°C</b></span>
      </div>
    </div>

    <div class="video-frame">
      <img v-if="status.online" :src="streamUrl" alt="Live stream" class="video-img" />
      <div v-else class="video-placeholder">
        <p>Menunggu stream MJPEG / WebRTC dari Jetson Nano…</p>
        <p class="mono hint">{{ streamUrl }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.live-container {
  padding: 1.5rem; height: 100%;
  display: flex; flex-direction: column; gap: 1rem;
}
.live-header { display: flex; align-items: center; justify-content: space-between; }
h2 { margin: 0; font-size: 1.1rem; }
.status-bar { display: flex; align-items: center; gap: 1rem; }
.status-pill {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-size: 0.75rem; font-weight: 600; padding: 0.25rem 0.6rem;
  border-radius: var(--radius-btn); border: 1px solid var(--border-subtle);
}
.status-pill .dot { width: 8px; height: 8px; border-radius: 50%; }
.status-pill.on { color: var(--status-success); }
.status-pill.on .dot { background: var(--status-success); }
.status-pill.off { color: var(--text-muted); }
.status-pill.off .dot { background: var(--text-muted); }
.metric { font-size: 0.8rem; color: var(--text-secondary); }
.metric b { color: var(--text-primary); }

.video-frame {
  flex: 1; background: var(--bg-canvas);
  border: 1px solid var(--accent-primary); border-radius: var(--radius-panel);
  display: flex; align-items: center; justify-content: center; overflow: hidden;
}
.video-img { max-width: 100%; max-height: 100%; object-fit: contain; }
.video-placeholder { text-align: center; color: var(--text-muted); }
.video-placeholder .hint { font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem; }
</style>
