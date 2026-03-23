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
      <div class="status-item status-item-download">
        <span class="status-name">下载中</span>
        <strong class="status-value">{{ downloadStatus.active ? downloadStatus.current : '空闲' }}</strong>
        <div v-if="downloadStatus.active && downloadStatus.progress" class="download-progress">
          <div class="download-progress-meta">
            <span>{{ progressPhaseLabel }}</span>
            <span>{{ progressSummary }}</span>
          </div>
          <div class="download-progress-bar">
            <span class="download-progress-fill" :style="{ width: `${progressPercent}%` }"></span>
          </div>
        </div>
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

    <template v-else>
      <div class="video-grid">
        <VideoCard v-for="video in paginatedVideos" :key="video.id" :video="video" @click="navigateToDetail(video.id)" />
      </div>

      <div v-if="totalPages > 1" class="pagination">
        <button class="page-button" @click="goToPrevPage" :disabled="currentPage === 1">上一页</button>
        <span class="page-summary">第 {{ currentPage }} / {{ totalPages }} 页</span>
        <button class="page-button" @click="goToNextPage" :disabled="currentPage === totalPages">下一页</button>
      </div>
    </template>
  </div>
</template>

<script>
import VideoCard from '../components/VideoCard.vue'
import videosApi from '../api/videos'

const ACTIVE_STATUS_POLL_MS = 2000
const IDLE_STATUS_POLL_MS = 6000
const PAGE_SIZE = 24

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
      lastUpdatedAt: null,
      currentPage: 1,
      wasDownloadActive: false
    }
  },
  computed: {
    pollingLabel() {
      if (!this.lastUpdatedAt) {
        return '自动轮询开启'
      }
      return `更新于 ${this.lastUpdatedAt}`
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.videos.length / PAGE_SIZE))
    },
    paginatedVideos() {
      const start = (this.currentPage - 1) * PAGE_SIZE
      return this.videos.slice(start, start + PAGE_SIZE)
    },
    progressPercent() {
      return Math.max(2, Math.min(100, Number(this.downloadStatus.progress?.progressPercent || 0)))
    },
    progressPhaseLabel() {
      const phase = this.downloadStatus.progress?.phase
      if (phase === 'downloading') return '下载中'
      if (phase === 'finalizing') return '封装中'
      if (phase === 'completed') return '已完成'
      if (phase === 'failed') return '下载失败'
      return '准备中'
    },
    progressSummary() {
      const progress = this.downloadStatus.progress
      if (!progress) {
        return ''
      }

      const parts = []
      if (progress.estimatedBytes > 0) {
        parts.push(`${Math.round(progress.progressPercent || 0)}%`)
        parts.push(`${this.formatBytes(progress.downloadedBytes)} / ${this.formatBytes(progress.estimatedBytes)}`)
      } else if (progress.downloadedBytes > 0) {
        parts.push(this.formatBytes(progress.downloadedBytes))
      }

      if (progress.phase === 'downloading' && progress.speedBytesPerSec > 0) {
        parts.push(this.formatSpeed(progress.speedBytesPerSec))
      }

      return parts.join(' · ')
    }
  },
  async created() {
    await this.refreshEverything()
    this.wasDownloadActive = this.downloadStatus.active
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
        if (this.currentPage > this.totalPages) {
          this.currentPage = this.totalPages
        }
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
          queueCount: 0,
          progress: null
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
      this.scheduleNextPoll()
    },
    stopPolling() {
      if (!this.pollTimer) {
        return
      }
      window.clearTimeout(this.pollTimer)
      this.pollTimer = null
    },
    scheduleNextPoll() {
      this.stopPolling()
      const delay = this.downloadStatus.active ? ACTIVE_STATUS_POLL_MS : IDLE_STATUS_POLL_MS
      this.pollTimer = window.setTimeout(() => {
        this.pollDownloadStatus()
      }, delay)
    },
    async pollDownloadStatus() {
      if (document.hidden) {
        this.scheduleNextPoll()
        return
      }

      const previousCurrent = this.downloadStatus.current
      const previousActive = this.downloadStatus.active
      await this.loadStatus()

      if ((previousActive && !this.downloadStatus.active) || previousCurrent !== this.downloadStatus.current) {
        await this.loadVideos({ silent: true })
      }

      this.wasDownloadActive = this.downloadStatus.active
      this.scheduleNextPoll()
    },
    handleVisibilityChange() {
      if (!document.hidden) {
        this.refreshEverything({ silent: true })
        this.scheduleNextPoll()
      }
    },
    handleExternalRefresh() {
      this.refreshEverything({ silent: true })
    },
    formatBytes(bytes) {
      const value = Number(bytes || 0)
      if (!value) {
        return '0 B'
      }
      const units = ['B', 'KB', 'MB', 'GB', 'TB']
      let size = value
      let unitIndex = 0
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024
        unitIndex += 1
      }
      const digits = unitIndex === 0 ? 0 : size >= 100 ? 0 : size >= 10 ? 1 : 2
      return `${size.toFixed(digits)} ${units[unitIndex]}`
    },
    formatSpeed(bytesPerSec) {
      return `${this.formatBytes(bytesPerSec)}/s`
    },
    navigateToDetail(id) {
      this.$router.push({ name: 'detail', params: { id } })
    },
    goToPrevPage() {
      if (this.currentPage > 1) {
        this.currentPage -= 1
        window.scrollTo({ top: 0, behavior: 'auto' })
      }
    },
    goToNextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage += 1
        window.scrollTo({ top: 0, behavior: 'auto' })
      }
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

.status-item-download {
  flex-direction: column;
  align-items: flex-start;
  min-width: min(360px, 100%);
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

.download-progress {
  width: min(320px, 100%);
  margin-top: 0.2rem;
}

.download-progress-meta {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  color: #8e6570;
  font-size: 0.76rem;
}

.download-progress-bar {
  position: relative;
  height: 4px;
  margin-top: 0.35rem;
  border-radius: 999px;
  background: rgba(191, 120, 134, 0.18);
  overflow: hidden;
}

.download-progress-fill {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #c96376 0%, #8a2037 100%);
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

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.9rem;
  margin-top: 1.2rem;
}

.page-button {
  min-width: 88px;
  height: 38px;
  padding: 0 0.95rem;
  border: 1px solid #efc5ca;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.94);
  color: #8a2037;
  font-weight: 700;
  cursor: pointer;
}

.page-button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.page-summary {
  color: #7f5660;
  font-size: 0.92rem;
  font-weight: 700;
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

  .pagination {
    gap: 0.65rem;
  }

  .page-button {
    flex: 1;
  }
}
</style>

