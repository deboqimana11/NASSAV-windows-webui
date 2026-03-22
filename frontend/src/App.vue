<template>
  <div id="app">
    <header class="app-header">
      <div class="header-container">
        <router-link to="/" class="logo">
          <div class="logo-mark">N</div>
          <div class="logo-copy">
            <h1>NASSAV</h1>
            <p>Windows 本地片库</p>
          </div>
        </router-link>

        <div class="search-box">
          <input
            v-model="inputContent"
            type="text"
            placeholder="输入车牌号，例如 IPZZ-776"
            class="search-input"
            @keyup.enter="handleAddVideo"
          >
          <button
            class="search-button"
            @click="handleAddVideo"
            :disabled="isAdding"
          >
            {{ isAdding ? '提交中...' : '添加下载' }}
          </button>
        </div>
      </div>

      <transition name="fade">
        <div v-if="notice.message" class="notice" :class="`notice-${notice.type}`">
          {{ notice.message }}
        </div>
      </transition>
    </header>

    <main class="app-main">
      <router-view v-slot="{ Component }">
        <keep-alive :include="['HomeView']">
          <component :is="Component" :key="$route.fullPath" />
        </keep-alive>
      </router-view>
    </main>

    <footer class="app-footer">
      <p>© 2026 NASSAV，本机可用的 Windows 片库面板</p>
    </footer>
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
        this.showNotice(error.message || '添加视频失败', 'error')
      } finally {
        this.isAdding = false
      }
    }
  }
}
</script>

<style>
:root {
  --rose-100: #fff1f1;
  --rose-200: #ffd8dd;
  --rose-300: #ffb1bd;
  --rose-500: #d64b67;
  --rose-700: #8a2037;
  --ink-900: #2a1720;
  --sand-50: #fffaf5;
  --gold-400: #f4b860;
  --success-bg: #edf9f0;
  --success-text: #1f7a38;
  --error-bg: #fff0f0;
  --error-text: #b42318;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  color: var(--ink-900);
  background:
    radial-gradient(circle at top left, rgba(255, 177, 189, 0.4), transparent 24%),
    linear-gradient(180deg, #fff8f4 0%, #fffdf9 100%);
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  color: white;
  background:
    linear-gradient(120deg, rgba(138, 32, 55, 0.96), rgba(214, 75, 103, 0.92)),
    linear-gradient(45deg, rgba(244, 184, 96, 0.18), transparent);
  box-shadow: 0 10px 28px rgba(138, 32, 55, 0.14);
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  max-width: 1360px;
  margin: 0 auto;
  padding: 0.9rem 1.5rem;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  color: white;
  text-decoration: none;
  min-width: 0;
}

.logo-mark {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--rose-700);
  background: linear-gradient(145deg, #fff7e6, #ffd9de);
}

.logo-copy h1 {
  margin: 0;
  font-size: 1.35rem;
  line-height: 1.1;
}

.logo-copy p {
  margin: 0.1rem 0 0;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.78);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  width: min(100%, 460px);
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 40px;
  padding: 0 0.95rem;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 12px;
  outline: none;
  font-size: 0.92rem;
  color: var(--ink-900);
  background: rgba(255, 250, 245, 0.96);
}

.search-input::placeholder {
  color: #b77a86;
}

.search-input:focus {
  border-color: rgba(244, 184, 96, 0.7);
  box-shadow: 0 0 0 4px rgba(244, 184, 96, 0.14);
}

.search-button {
  flex-shrink: 0;
  height: 40px;
  padding: 0 1rem;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 700;
  color: var(--rose-700);
  background: linear-gradient(135deg, #ffe7ac, #ffc97d);
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.search-button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.search-button:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.notice {
  max-width: 1360px;
  margin: 0 auto 0.85rem;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  font-size: 0.92rem;
}

.notice-success {
  color: var(--success-text);
  background: var(--success-bg);
}

.notice-error {
  color: var(--error-text);
  background: var(--error-bg);
}

.notice-info {
  color: var(--rose-700);
  background: rgba(255, 255, 255, 0.88);
}

.app-main {
  flex: 1;
  width: 100%;
  max-width: 1360px;
  margin: 0 auto;
  padding: 1.4rem 1.5rem 3rem;
}

.app-footer {
  text-align: center;
  padding: 0.9rem;
  color: white;
  background: linear-gradient(135deg, #65192a, #9f2944);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 768px) {
  .header-container {
    flex-direction: column;
    align-items: stretch;
    padding: 0.9rem 1rem;
  }

  .search-box {
    width: 100%;
  }

  .app-main {
    padding: 1rem 1rem 2rem;
  }

  .notice {
    margin: 0 1rem 0.9rem;
  }
}
</style>
