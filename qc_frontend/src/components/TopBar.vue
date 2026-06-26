<script setup>
import { useRoute } from 'vue-router'
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useTheme } from '../composables/useTheme.js'

const route = useRoute()
const { t, locale, setLocale } = useI18n()
const { theme, toggle } = useTheme()

const pageTitle = computed(() => {
  const map = {
    live: t('live.title'),
    qc: t('qc.title'),
    batches: t('batches.title'),
    reports: t('reports.title'),
    audit: t('audit.title'),
    settings: t('settings.title'),
  }
  return map[route.name] ?? ''
})
</script>

<template>
  <header class="top-bar">
    <h1 class="page-title">{{ pageTitle }}</h1>

    <div class="top-bar-actions">
      <button
        class="tb-btn"
        @click="setLocale(locale === 'id' ? 'en' : 'id')"
        :title="locale === 'id' ? 'Switch to English' : 'Ganti ke Indonesia'"
      >
        {{ locale === 'id' ? 'EN' : 'ID' }}
      </button>

      <button
        class="tb-btn"
        @click="toggle"
        :title="theme === 'light' ? t('settings.themeDark') : t('settings.themeLight')"
      >
        <svg v-if="theme === 'light'" class="tb-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
        </svg>
        <svg v-else class="tb-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="5" />
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
        </svg>
      </button>

      <div class="user-badge">
        <span class="user-avatar">QC</span>
      </div>
    </div>
  </header>
</template>

<style scoped>
.top-bar {
  height: 48px;
  flex-shrink: 0;
  background: var(--color-canvas);
  border-bottom: 1px solid var(--color-hairline);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.page-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ink);
  letter-spacing: 0.16px;
}

.top-bar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tb-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 32px;
  padding: 0 8px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink-muted);
  cursor: pointer;
  font-family: var(--font-sans);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.32px;
}

.tb-btn:hover {
  background: var(--color-surface-1);
  color: var(--color-ink);
}

.tb-icon {
  width: 16px;
  height: 16px;
}

.user-badge {
  display: flex;
  align-items: center;
}

.user-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.32px;
}
</style>
