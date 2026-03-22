<template>
  <div class="container">
    <div class="hero">
      <div>
        <p class="eyebrow">本地片库</p>
        <h1>已入库 {{ videos.length }} 部</h1>
        <p class="subtitle">点击封面进入详情页，支持直接播放本地视频。</p>
      </div>
      <div class="hero-actions">
        <span class="polling-indicator">{{ pollingLabel }}</span>
        <button class="refresh-button" @click="refreshEverything()" :disabled="loading">
          {{ loading ? '刷新中...' : '刷新列表' }}
        </button>
      </div>
    </div>

    <section class="status-strip">
      <div class="status-item">
        <span class="status-name">下载中</span>
        <strong class="status-value">{{ downloadStatus.active ? downloadStatus.current : '空闲' }}</strong>
      </div>
      <div class="status-item">
        <span class="status-name">排队</span>
        <strong class="status-value">{{ downloadStatus.queueCount }} 个</strong>
      </div>
      <div class="status-item status-queue" v-if="downloadStatus.queue.length">
        <span class="status-name">队列</span>
        <div class="queue-inline">
          <span v-for="item in downloadStatus.queue.slice(0, 5)" :key="item" class="queue-chip">{{ item }}</span>
        </div>
      </div>
    </section>

    <div v-if="loading" class="status-card">正在加载本地片库...</div>
    <div v-else-if="error" class="status-card status-error">{{ error }}</div>
    <div v-else-if="!videos.length" class="status-card">还没有视频，先在顶部添加一个车牌号试试。</div>

    <div v-else class="video-grid">
      <VideoCard v-for="video in videos" :key="video.id" :video="video" @click="navigateToDetail(video.id)" />
    </div>
  </div>
</template>

<script>
import VideoCard from '../components/VideoCard.vue'
import videosApi from '../api/videos'

const POLL_INTERVAL_MS = 6000

export default {
  name: 'HomeView',
  components: { VideoCard },
  data() {
    return {
      videos: [],
      downloadStatus: {
        active: false,
        current: '',
        queue: [],
        queueCount: 0
      },
      scrollPosition: 0,
      loading: false,
      error: '',
      pollTimer: null,
      lastUpdatedAt: null
    }
  },
  computed: {
    pollingLabel() {
      if (!this.lastUpdatedAt) {
        return '自动轮询开启'
      }
      return `更新于 ${this.lastUpdatedAt}`
    }
  },
  async created() {
    await this.refreshEverything()
    window.addEventListener('videos:refresh', this.handleExternalRefresh)
    document.addEventListener('visibilitychange', this.handleVisibilityChange)
    this.startPolling()
  },
  activated() {
    window.scrollTo(0, this.scrollPosition)
    this.startPolling()
  },
  deactivated() {
    this.stopPolling()
  },
  beforeUnmount() {
    window.removeEventListener('videos:refresh', this.handleExternalRefresh)
    document.removeEventListener('visibilitychange', this.handleVisibilityChange)
    this.stopPolling()
  },
  beforeRouteLeave(to, from, next) {
    this.scrollPosition = window.scrollY
    next()
  },
  methods: {
    stampUpdatedAt() {
      const now = new Date()
      this.lastUpdatedAt = now.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    },
    async loadVideos(options = {}) {
      const { silent = false } = options
      if (this.loading && !silent) {
        return
      }

      if (!silent) {
        this.loading = true
        this.error = ''
      }

      try {
        const nextVideos = await videosApi.getVideoList()
        this.videos = nextVideos
        this.stampUpdatedAt()
        if (silent) {
          this.error = ''
        }
      } catch (error) {
        if (!silent) {
          this.error = error.message || '加载视频列表失败'
        }
      } finally {
        if (!silent) {
          this.loading = false
        }
      }
    },
    async loadStatus() {
      try {
        this.downloadStatus = await videosApi.getDownloadStatus()
      } catch {
        this.downloadStatus = {
          active: false,
          current: '',
          queue: [],
          queueCount: 0
        }
      }
    },
    async refreshEverything(options = {}) {
      const { silent = false } = options
      await Promise.all([
        this.loadVideos({ silent }),
        this.loadStatus()
      ])
    },
    startPolling() {
      if (this.pollTimer) {
        return
      }
      this.pollTimer = window.setInterval(() => {
        if (document.hidden) {
          return
        }
        this.refreshEverything({ silent: true })
      }, POLL_INTERVAL_MS)
    },
    stopPolling() {
      if (!this.pollTimer) {
        return
      }
      window.clearInterval(this.pollTimer)
      this.pollTimer = null
    },
    handleVisibilityChange() {
      if (!document.hidden) {
        this.refreshEverything({ silent: true })
      }
    },
    handleExternalRefresh() {
      this.refreshEverything({ silent: true })
    },
    navigateToDetail(id) {
      this.$router.push({ name: 'detail', params: { id } })
    }
  }
}
</script>

<style scoped>
.container {
  padding: 0.2rem 0 1rem;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 1rem;
  margin-bottom: 1rem;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.eyebrow {
  margin: 0 0 0.3rem;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #b8606d;
}

h1 {
  margin: 0;
  color: #381821;
  font-size: clamp(1.55rem, 2.5vw, 2.2rem);
}

.subtitle {
  margin: 0.35rem 0 0;
  color: #7f5660;
  font-size: 0.95rem;
}

.polling-indicator {
  display: inline-flex;
  align-items: center;
  height: 38px;
  padding: 0 0.85rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.74);
  color: #8a2037;
  font-size: 0.84rem;
  white-space: nowrap;
}

.refresh-button {
  height: 38px;
  padding: 0 0.95rem;
  border: 1px solid #efc5ca;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  color: #8a2037;
  font-weight: 700;
  cursor: pointer;
}

.status-strip {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  padding: 0.75rem 0.9rem;
  margin-bottom: 1.25rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.7);
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
}

.status-name {
  color: #9c6671;
  font-size: 0.82rem;
  font-weight: 700;
  white-space: nowrap;
}

.status-value {
  color: #381821;
  font-size: 0.92rem;
}

.status-queue {
  flex: 1;
}

.queue-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.queue-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 0.7rem;
  border-radius: 999px;
  background: #fff3f4;
  color: #9f2944;
  font-size: 0.8rem;
  font-weight: 700;
}

.status-card {
  padding: 1rem 1.1rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
  color: #7b4a56;
  box-shadow: 0 10px 24px rgba(138, 32, 55, 0.08);
}

.status-error {
  color: #b42318;
  background: #fff1f1;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
  gap: 16px;
  padding: 0.2rem 0 0;
}

@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .status-strip {
    flex-direction: column;
    align-items: stretch;
  }

  .status-item {
    align-items: flex-start;
    flex-direction: column;
    gap: 0.3rem;
  }

  .polling-indicator,
  .refresh-button {
    width: 100%;
    justify-content: center;
  }

  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(132px, 1fr));
    gap: 14px;
  }
}
</style>

