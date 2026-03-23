<template>
  <div class="home-page">
    <section v-if="featuredVideo" class="spotlight-grid">
      <article class="spotlight-panel" @click="navigateToDetail(featuredVideo.id)">
        <div class="spotlight-backdrop">
          <img v-if="featuredVideo.poster" :src="featuredVideo.poster" :alt="featuredVideo.title">
        </div>
        <div class="spotlight-overlay"></div>
        <div class="spotlight-content">
          <p class="spotlight-kicker">继续浏览</p>
          <h2>{{ featuredVideo.id }}</h2>
          <p class="spotlight-title">{{ featuredVideo.title }}</p>
          <div class="spotlight-actions">
            <button class="spotlight-button spotlight-button-primary" @click.stop="navigateToDetail(featuredVideo.id)">播放详情</button>
            <button class="spotlight-button spotlight-button-secondary" @click.stop="refreshEverything()" :disabled="loading">
              {{ loading ? '\u540c\u6b65\u4e2d...' : '\u5237\u65b0\u7247\u5e93' }}
            </button>
          </div>
        </div>
      </article>

      <aside class="status-rail">
        <div class="rail-card rail-card-primary">
          <span class="rail-label">当前状态</span>
          <strong class="rail-headline">{{ statusHeadline }}</strong>
          <p class="rail-text">{{ statusDescription }}</p>

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

        <div class="rail-stats">
          <div class="rail-stat">
            <span>排队</span>
            <strong>{{ downloadStatus.queueCount }}</strong>
          </div>
          <div class="rail-stat">
            <span>片库</span>
            <strong>{{ videos.length }}</strong>
          </div>
          <div class="rail-stat">
            <span>刷新</span>
            <strong>{{ pollingLabel }}</strong>
          </div>
        </div>

        <div v-if="downloadStatus.queue.length" class="queue-inline">
          <span class="queue-inline-label">队列</span>
          <div class="queue-inline-list">
            <span v-for="item in downloadStatus.queue.slice(0, 6)" :key="item" class="queue-chip">{{ item }}</span>
          </div>
        </div>
      </aside>
    </section>

    <section class="shelf-toolbar">
      <div>
        <p class="shelf-kicker">Library</p>
        <h3>全部影片</h3>
      </div>
      <div class="shelf-toolbar-meta">
        <span>共 {{ videos.length }} 部</span>
      </div>
    </section>

    <div v-if="loading" class="status-card">正在同步本地片库...</div>
    <div v-else-if="error" class="status-card status-error">{{ error }}</div>
    <div v-else-if="!videos.length" class="status-card empty-state">
      <strong>片库还是空的</strong>
      <span>先在顶部输入车牌号，把第一部影片加入你的私人片单。</span>
    </div>

    <template v-else>
      <section class="video-shelf">
        <VideoCard
          v-for="(video, index) in paginatedVideos"
          :key="video.id"
          :video="video"
          :eyebrow="video.id"
          :index-label="String((currentPage - 1) * PAGE_SIZE + index + 1).padStart(2, '0')"
          @click="navigateToDetail(video.id)"
        />
      </section>

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
const PAGE_SIZE = 18

function createDefaultStatus() {
  return {
    active: false,
    current: '',
    queue: [],
    queueCount: 0,
    progress: null
  }
}

export default {
  name: 'HomeView',
  components: { VideoCard },
  data() {
    return {
      videos: [],
      downloadStatus: createDefaultStatus(),
      scrollPosition: 0,
      loading: false,
      error: '',
      pollTimer: null,
      lastUpdatedAt: '',
      statusUpdatedAt: '',
      currentPage: 1
    }
  },
  computed: {
    featuredVideo() {
      return this.videos[0] || null
    },
    statusHeadline() {
      if (this.downloadStatus.active) {
        return '\u4e0b\u8f7d\u8fdb\u884c\u4e2d'
      }
      if (this.downloadStatus.queueCount) {
        return '\u7b49\u5f85\u5f00\u59cb'
      }
      return '\u7247\u5e93\u7a7a\u95f2'
    },
    statusDescription() {
      if (this.downloadStatus.active) {
        return this.downloadStatus.current || '\u6b63\u5728\u51c6\u5907\u4e0b\u8f7d\u4efb\u52a1'
      }
      if (this.downloadStatus.queueCount) {
        return `\u961f\u5217\u4e2d\u8fd8\u6709 ${this.downloadStatus.queueCount} \u4e2a\u4efb\u52a1`
      }
      return '\u73b0\u5728\u53ef\u4ee5\u76f4\u63a5\u7ee7\u7eed\u6d4f\u89c8\u6216\u52a0\u5165\u65b0\u4efb\u52a1'
    },
    pollingLabel() {
      if (this.downloadStatus.active && this.statusUpdatedAt) {
        return this.statusUpdatedAt
      }
      if (this.lastUpdatedAt) {
        return this.lastUpdatedAt
      }
      return '\u81ea\u52a8'
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
      if (phase === 'downloading') return '\u4e0b\u8f7d\u4e2d'
      if (phase === 'finalizing') return '\u5c01\u88c5\u4e2d'
      if (phase === 'completed') return '\u5df2\u5b8c\u6210'
      if (phase === 'failed') return '\u4e0b\u8f7d\u5931\u8d25'
      return '\u51c6\u5907\u4e2d'
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
    formatTimestamp(date = new Date()) {
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    },
    stampVideosUpdatedAt() {
      this.lastUpdatedAt = this.formatTimestamp()
    },
    stampStatusUpdatedAt() {
      this.statusUpdatedAt = this.formatTimestamp()
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
        this.stampVideosUpdatedAt()
        if (silent) {
          this.error = ''
        }
      } catch (error) {
        if (!silent) {
          this.error = error.message || '\u52a0\u8f7d\u89c6\u9891\u5217\u8868\u5931\u8d25'
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
        this.stampStatusUpdatedAt()
      } catch {
        this.downloadStatus = createDefaultStatus()
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
.home-page {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.spotlight-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(300px, 0.85fr);
  gap: 1rem;
  align-items: stretch;
}

.spotlight-panel {
  position: relative;
  min-height: clamp(210px, 26vw, 280px);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 1.6rem;
  background: #0f0f0f;
  cursor: pointer;
}

.spotlight-backdrop,
.spotlight-backdrop img,
.spotlight-overlay {
  position: absolute;
  inset: 0;
}

.spotlight-backdrop img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: saturate(0.88) brightness(0.7);
}

.spotlight-overlay {
  background:
    linear-gradient(90deg, rgba(10, 10, 10, 0.96) 0%, rgba(10, 10, 10, 0.72) 36%, rgba(10, 10, 10, 0.32) 62%, rgba(10, 10, 10, 0.92) 100%),
    linear-gradient(180deg, rgba(10, 10, 10, 0.18) 0%, rgba(10, 10, 10, 0.84) 100%);
}

.spotlight-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  height: 100%;
  max-width: min(32rem, 72%);
  padding: clamp(1.05rem, 2vw, 1.4rem);
}

.spotlight-kicker,
.shelf-kicker {
  margin: 0 0 0.35rem;
  color: #ffb37c;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.spotlight-content h2 {
  margin: 0;
  font-family: 'Arial Narrow', 'Impact', sans-serif;
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 0.9;
  letter-spacing: 0.04em;
}

.spotlight-title {
  margin: 0.55rem 0 0;
  color: rgba(230, 223, 213, 0.82);
  font-size: 0.95rem;
  line-height: 1.55;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.spotlight-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-top: 0.95rem;
}

.spotlight-button {
  min-width: 6.8rem;
  height: 2.5rem;
  padding: 0 0.95rem;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  font-weight: 800;
}

.spotlight-button-primary {
  color: white;
  background: linear-gradient(135deg, #e61d2b 0%, #9d0615 100%);
}

.spotlight-button-secondary {
  color: rgba(230, 223, 213, 0.88);
  background: rgba(255, 255, 255, 0.1);
}

.status-rail {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.rail-card {
  padding: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 1.35rem;
  background: linear-gradient(180deg, rgba(18, 18, 18, 0.96) 0%, rgba(12, 12, 12, 0.96) 100%);
}

.rail-label {
  display: block;
  color: var(--text-soft);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.rail-headline {
  display: block;
  margin-top: 0.45rem;
  color: rgba(230, 223, 213, 0.88);
  font-size: 1.05rem;
  font-weight: 800;
}

.rail-text {
  margin: 0.35rem 0 0;
  color: var(--text-muted);
  font-size: 0.85rem;
  line-height: 1.55;
}

.rail-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.65rem;
}

.rail-stat {
  padding: 0.8rem 0.85rem;
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 1.1rem;
  background: rgba(255, 255, 255, 0.03);
}

.rail-stat span {
  display: block;
  color: var(--text-soft);
  font-size: 0.7rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.rail-stat strong {
  display: block;
  margin-top: 0.35rem;
  color: rgba(230, 223, 213, 0.88);
  font-size: 0.95rem;
  font-weight: 800;
  line-height: 1.35;
}

.queue-inline {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.queue-inline-label {
  color: var(--text-soft);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.queue-inline-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.queue-chip {
  display: inline-flex;
  align-items: center;
  min-height: 1.9rem;
  padding: 0 0.72rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.07);
  color: var(--text-muted);
  font-size: 0.78rem;
  font-weight: 700;
}

.download-progress {
  margin-top: 0.8rem;
}

.download-progress-meta {
  display: flex;
  justify-content: space-between;
  gap: 0.7rem;
  color: var(--text-soft);
  font-size: 0.72rem;
}

.download-progress-bar {
  position: relative;
  height: 4px;
  margin-top: 0.35rem;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
}

.download-progress-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #ff7e45 0%, #d31f2b 100%);
}

.shelf-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 1rem;
  padding-top: 0.25rem;
}

.shelf-toolbar h3 {
  margin: 0;
  font-size: clamp(1.35rem, 2vw, 1.8rem);
}

.shelf-toolbar-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  color: var(--text-soft);
  font-size: 0.82rem;
}

.shelf-toolbar-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: 0 0.72rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
}

.status-card {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 1.1rem 1.2rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1.2rem;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-muted);
}

.status-error {
  color: #ffd0d4;
  background: rgba(100, 26, 33, 0.42);
}

.empty-state strong {
  color: rgba(230, 223, 213, 0.88);
  font-size: 1.05rem;
}

.video-shelf {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(172px, 1fr));
  row-gap: 1.6rem;
  column-gap: 0.95rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.9rem;
  margin-top: 0.85rem;
  padding-top: 0.4rem;
}

.page-button {
  min-width: 92px;
  height: 2.65rem;
  padding: 0 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(230, 223, 213, 0.88);
  font-weight: 700;
  cursor: pointer;
}

.page-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-summary {
  color: var(--text-soft);
  font-size: 0.9rem;
  font-weight: 700;
}

@media (max-width: 1040px) {
  .spotlight-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .spotlight-panel {
    min-height: 220px;
  }

  .spotlight-content {
    max-width: 100%;
  }

  .spotlight-overlay {
    background: linear-gradient(180deg, rgba(10, 10, 10, 0.22) 0%, rgba(10, 10, 10, 0.72) 56%, rgba(10, 10, 10, 0.95) 100%);
  }

  .spotlight-actions {
    width: 100%;
  }

  .spotlight-button {
    flex: 1;
  }

  .rail-stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .shelf-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .video-shelf {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    row-gap: 1.3rem;
    column-gap: 0.8rem;
  }

  .pagination {
    gap: 0.6rem;
  }

  .page-button {
    flex: 1;
  }
}
</style>
