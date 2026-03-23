<template>
  <div id="app" :class="{ 'app-detail': $route.name === 'detail' }">
    <header class="app-header">
      <div class="header-backdrop"></div>
      <div class="header-shell">
        <div class="topbar">
          <router-link to="/" class="brand">
            <span class="brand-mark">N</span>
            <span class="brand-copy">
              <strong>NASSAV</strong>
              <small>Private Screening Library</small>
            </span>
          </router-link>

          <div class="topbar-side">
            <div class="topbar-meta">
              <span class="meta-pill">Windows WebUI</span>
              <span class="meta-text">本地片库 / 下载队列 / 继续播放</span>
            </div>

            <div class="quick-add">
              <label class="sr-only" for="avid-input">添加下载</label>
              <input
                id="avid-input"
                v-model="inputContent"
                type="text"
                placeholder="输入车牌号，例如 JUQ-340"
                class="quick-add-input"
                @keyup.enter="handleAddVideo"
              >
              <button
                class="quick-add-button"
                @click="handleAddVideo"
                :disabled="isAdding"
              >
                {{ isAdding ? '\u63d0\u4ea4\u4e2d...' : '\u52a0\u5165\u4e0b\u8f7d' }}
              </button>
            </div>
          </div>
        </div>

        <div class="subbar">
          <p class="subbar-copy">像流媒体首页一样浏览你的本地片库，同时保留车牌直下和实时状态。</p>
          <span class="subbar-tip">支持回车添加，首页自动刷新队列与片库</span>
        </div>

        <transition name="notice-fade">
          <div v-if="notice.message" class="notice" :class="`notice-${notice.type}`">
            {{ notice.message }}
          </div>
        </transition>
      </div>
    </header>

    <main class="app-main">
      <router-view v-slot="{ Component }">
        <keep-alive :include="['HomeView']">
          <component :is="Component" :key="$route.fullPath" />
        </keep-alive>
      </router-view>
    </main>
  </div>
</template>

<script>
import videosApi from './api/videos'

export default {
  name: 'App',
  data() {
    return {
      inputContent: '',
      isAdding: false,
      notice: {
        type: 'info',
        message: ''
      },
      noticeTimer: null
    }
  },
  beforeUnmount() {
    if (this.noticeTimer) {
      clearTimeout(this.noticeTimer)
    }
  },
  methods: {
    showNotice(message, type = 'info') {
      this.notice = { message, type }

      if (this.noticeTimer) {
        clearTimeout(this.noticeTimer)
      }

      this.noticeTimer = setTimeout(() => {
        this.notice = { message: '', type: 'info' }
      }, 3500)
    },
    async handleAddVideo() {
      if (this.isAdding) {
        return
      }

      this.isAdding = true
      try {
        const result = await videosApi.addVideo(this.inputContent)
        this.inputContent = ''
        this.showNotice(result.message, 'success')
        window.dispatchEvent(new CustomEvent('videos:refresh'))
        if (this.$route.name !== 'home') {
          this.$router.push({ name: 'home' })
        }
      } catch (error) {
        this.showNotice(error.message || '\u6dfb\u52a0\u89c6\u9891\u5931\u8d25', 'error')
      } finally {
        this.isAdding = false
      }
    }
  }
}
</script>

<style>
:root {
  color-scheme: dark;
  --bg: #090909;
  --bg-soft: #111111;
  --panel: rgba(20, 20, 20, 0.88);
  --panel-strong: rgba(26, 26, 26, 0.96);
  --panel-line: rgba(255, 255, 255, 0.08);
  --text: #e6dfd5;
  --text-muted: #b5aea3;
  --text-soft: #8f877c;
  --accent: #d31f2b;
  --accent-soft: #f07b53;
  --success-bg: rgba(28, 68, 42, 0.82);
  --success-text: #d2f3dc;
  --error-bg: rgba(86, 24, 28, 0.84);
  --error-text: #ffd7d9;
}

* {
  box-sizing: border-box;
}

html {
  background: var(--bg);
}

body {
  margin: 0;
  min-width: 320px;
  font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: rgba(230, 223, 213, 0.88);
  background:
    radial-gradient(circle at 12% 18%, rgba(211, 31, 43, 0.22), transparent 24%),
    radial-gradient(circle at 88% 16%, rgba(240, 123, 83, 0.12), transparent 26%),
    linear-gradient(180deg, #1a090a 0%, #0c0c0c 26%, #090909 100%);
}

button,
input {
  font: inherit;
}

#app {
  min-height: 100vh;
}

.app-header {
  position: relative;
  overflow: clip;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.header-backdrop {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(0, 0, 0, 0.38) 0%, rgba(0, 0, 0, 0.72) 100%),
    linear-gradient(90deg, rgba(0, 0, 0, 0.88) 0%, rgba(0, 0, 0, 0.54) 42%, rgba(0, 0, 0, 0.86) 100%),
    radial-gradient(circle at 84% 32%, rgba(211, 31, 43, 0.24), transparent 24%);
}

.header-shell {
  position: relative;
  z-index: 1;
  width: min(100%, 1440px);
  margin: 0 auto;
  padding: clamp(0.9rem, 1.4vw, 1.1rem) clamp(1rem, 3vw, 2rem) clamp(0.8rem, 1.8vw, 1rem);
}

.topbar {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 1rem 1.4rem;
  align-items: center;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.9rem;
  text-decoration: none;
  color: rgba(230, 223, 213, 0.88);
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 2.45rem;
  height: 2.45rem;
  border-radius: 0.8rem;
  background: linear-gradient(180deg, #f4463d 0%, #970c18 100%);
  box-shadow: 0 12px 30px rgba(211, 31, 43, 0.28);
  font-family: 'Arial Narrow', 'Impact', sans-serif;
  font-size: 1.55rem;
  letter-spacing: 0.08em;
}

.brand-copy {
  display: flex;
  flex-direction: column;
  gap: 0.02rem;
}

.brand-copy strong {
  font-family: 'Arial Narrow', 'Impact', sans-serif;
  font-size: 1.9rem;
  letter-spacing: 0.08em;
  line-height: 1;
}

.brand-copy small {
  color: var(--text-soft);
  font-size: 0.7rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.topbar-side {
  display: grid;
  grid-template-columns: auto minmax(320px, 520px);
  gap: 0.9rem;
  align-items: center;
  justify-content: end;
}

.topbar-meta {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.7rem;
  color: var(--text-soft);
  font-size: 0.78rem;
}

.meta-pill {
  padding: 0.33rem 0.62rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(230, 223, 213, 0.88);
}

.quick-add {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.55rem;
  padding: 0.42rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1rem;
  background: linear-gradient(180deg, rgba(20, 20, 20, 0.9) 0%, rgba(12, 12, 12, 0.94) 100%);
}

.quick-add-input {
  min-width: 0;
  height: 2.7rem;
  padding: 0 0.95rem;
  border: none;
  border-radius: 0.75rem;
  outline: none;
  color: rgba(230, 223, 213, 0.88);
  background: rgba(255, 255, 255, 0.05);
}

.quick-add-input::placeholder {
  color: #91897f;
}

.quick-add-input:focus {
  box-shadow: 0 0 0 3px rgba(240, 123, 83, 0.14);
}

.quick-add-button {
  height: 2.7rem;
  padding: 0 1rem;
  border: none;
  border-radius: 0.8rem;
  cursor: pointer;
  color: white;
  font-weight: 800;
  background: linear-gradient(135deg, #e61d2b 0%, #9d0615 100%);
  transition: transform 0.22s ease, box-shadow 0.22s ease, opacity 0.22s ease;
  box-shadow: 0 14px 30px rgba(211, 31, 43, 0.24);
}

.quick-add-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 18px 34px rgba(211, 31, 43, 0.32);
}

.quick-add-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.subbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-top: 0.75rem;
  padding-top: 0.7rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.subbar-copy {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.86rem;
  line-height: 1.45;
}

.subbar-tip {
  color: var(--text-soft);
  font-size: 0.76rem;
  white-space: nowrap;
}

.notice {
  margin-top: 0.85rem;
  padding: 0.85rem 1rem;
  border-radius: 1rem;
  font-size: 0.92rem;
}

.notice-success {
  background: var(--success-bg);
  color: var(--success-text);
}

.notice-error {
  background: var(--error-bg);
  color: var(--error-text);
}

.notice-info {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(230, 223, 213, 0.88);
}

.app-main {
  width: min(100%, 1440px);
  margin: 0 auto;
  padding: clamp(1rem, 2.4vw, 1.6rem) clamp(1rem, 3vw, 2rem) 3rem;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.notice-fade-enter-active,
.notice-fade-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.notice-fade-enter-from,
.notice-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 1080px) {
  .topbar-side {
    grid-template-columns: 1fr;
    justify-content: stretch;
  }

  .topbar-meta {
    justify-content: flex-start;
  }
}

@media (max-width: 820px) {
  .topbar {
    grid-template-columns: 1fr;
  }

  .subbar {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 720px) {
  .topbar-meta {
    flex-wrap: wrap;
  }

  .quick-add {
    grid-template-columns: 1fr;
  }

  .quick-add-button {
    width: 100%;
  }

  .brand-copy strong {
    font-size: 1.8rem;
  }

  .subbar-tip {
    white-space: normal;
  }
}
</style>

