<template>
  <div class="detail-container" v-if="video">
    <div class="header">
      <div>
        <p class="eyebrow">视频详情</p>
        <h1>{{ video.title }}</h1>
        <p class="release-date">发行日期: {{ video.releaseDate || '未知' }}</p>
      </div>
      <router-link class="back-link" to="/">返回首页</router-link>
    </div>

    <section class="player-section">
      <div v-if="video.videoFile" class="video-player">
        <video
          class="player"
          :poster="video.poster"
          controls
          preload="metadata"
          playsinline
        >
          <source :src="video.videoFile" type="video/mp4">
          你的浏览器暂不支持 HTML5 视频播放。
        </video>
      </div>
      <div v-else class="video-unavailable">
        当前没有可播放的视频文件，可能这部影片还没下载完成。
      </div>
    </section>

    <div class="content-grid">
      <aside class="poster-panel">
        <img :src="video.poster" :alt="video.title">
        <div class="poster-meta">
          <div class="meta-label">状态</div>
          <div class="meta-value">{{ video.videoFile ? '可直接播放' : '仅展示元数据' }}</div>
        </div>
      </aside>

      <section class="gallery-panel">
        <Gallery :images="video.fanarts" />
      </section>
    </div>
  </div>
</template>

<script>
import Gallery from '../components/Gallery.vue'
import videosApi from '../api/videos'

export default {
  components: { Gallery },
  props: ['id'],
  data() {
    return {
      video: null
    }
  },
  async created() {
    this.video = await videosApi.getVideoDetail(this.id)
  }
}
</script>

<style scoped>
.detail-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.25rem;
  background: rgba(255, 255, 255, 0.94);
  border-radius: 24px;
  box-shadow: 0 12px 36px rgba(138, 32, 55, 0.08);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.eyebrow {
  margin: 0 0 0.45rem;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #b8606d;
}

.header h1 {
  margin: 0;
  color: #2f1820;
  font-size: clamp(1.6rem, 2.8vw, 2.4rem);
}

.release-date {
  margin: 0.65rem 0 0;
  color: #a04657;
  font-size: 0.98rem;
}

.back-link {
  display: inline-flex;
  align-items: center;
  min-height: 42px;
  padding: 0 1rem;
  border-radius: 14px;
  text-decoration: none;
  background: #fff1f3;
  color: #8a2037;
  font-weight: 700;
  white-space: nowrap;
}

.player-section {
  margin-bottom: 1.5rem;
}

.video-player {
  border-radius: 22px;
  overflow: hidden;
  background: #12090d;
  box-shadow: 0 16px 36px rgba(21, 10, 13, 0.2);
}

.player {
  width: 100%;
  max-height: 72vh;
  display: block;
  background: #12090d;
}

.video-unavailable {
  padding: 1rem 1.1rem;
  border-radius: 18px;
  color: #7f5660;
  background: #fff5f5;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(240px, 300px) 1fr;
  gap: 1.5rem;
  align-items: start;
}

.poster-panel {
  position: sticky;
  top: 96px;
  padding: 1rem;
  border-radius: 20px;
  background: linear-gradient(180deg, #fff7f8 0%, #fffdfb 100%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.75), 0 10px 24px rgba(138, 32, 55, 0.08);
}

.poster-panel img {
  width: 100%;
  display: block;
  border-radius: 16px;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
}

.poster-meta {
  margin-top: 1rem;
}

.meta-label {
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #b8606d;
}

.meta-value {
  margin-top: 0.35rem;
  color: #381821;
  font-weight: 700;
}

.gallery-panel {
  min-width: 0;
}

@media (max-width: 900px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .poster-panel {
    position: static;
  }
}

@media (max-width: 768px) {
  .detail-container {
    padding: 1rem;
    border-radius: 18px;
  }

  .header {
    flex-direction: column;
  }

  .back-link {
    width: 100%;
    justify-content: center;
  }

  .player {
    max-height: none;
  }
}
</style>
