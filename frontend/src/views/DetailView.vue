<template>
  <div class="detail-container" v-if="video">
    <div class="header">
      <div>
        <router-link class="back-link back-link-mobile" to="/">返回首页</router-link>
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

    <section class="info-panel">
      <div class="title-block">
        <h1>{{ video.title }}</h1>
        <p class="release-date">发行日期: {{ video.releaseDate || '未知' }}</p>
      </div>
      <div class="meta-row">
        <div class="meta-card">
          <span class="meta-label">状态</span>
          <strong class="meta-value">{{ video.videoFile ? '可直接播放' : '仅展示元数据' }}</strong>
        </div>
        <div class="meta-card">
          <span class="meta-label">图集</span>
          <strong class="meta-value">{{ video.fanarts?.length || 0 }} 张</strong>
        </div>
      </div>
    </section>

    <div class="content-grid">
      <aside class="poster-panel" v-if="video.poster">
        <img :src="video.poster" :alt="video.title">
      </aside>

      <section class="gallery-panel" :class="{ 'gallery-panel-full': !video.poster }">
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
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
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

.back-link-mobile {
  display: none;
}

.player-section {
  margin-bottom: 1rem;
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

.info-panel {
  margin-bottom: 1.4rem;
  padding: 1.1rem 1.2rem;
  border-radius: 20px;
  background: linear-gradient(180deg, #fff7f8 0%, #fffdfb 100%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.78), 0 10px 24px rgba(138, 32, 55, 0.08);
}

.title-block h1 {
  margin: 0;
  color: #2f1820;
  font-size: clamp(1.45rem, 2.5vw, 2.1rem);
  line-height: 1.35;
}

.release-date {
  margin: 0.7rem 0 0;
  color: #a04657;
  font-size: 0.98rem;
}

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem;
  margin-top: 1rem;
}

.meta-card {
  min-width: 160px;
  padding: 0.85rem 0.95rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
}

.meta-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #b8606d;
}

.meta-value {
  display: block;
  margin-top: 0.45rem;
  color: #381821;
  font-size: 0.98rem;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(240px, 300px) 1fr;
  gap: 1.5rem;
  align-items: start;
}

.poster-panel {
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

.gallery-panel {
  min-width: 0;
}

.gallery-panel-full {
  grid-column: 1 / -1;
}

@media (max-width: 900px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .detail-container {
    padding: 1rem;
    border-radius: 18px;
  }

  .header {
    margin-bottom: 0.85rem;
  }

  .back-link {
    display: none;
  }

  .back-link-mobile {
    display: inline-flex;
    margin-top: 0.65rem;
    width: 100%;
    justify-content: center;
  }

  .player {
    max-height: none;
  }

  .info-panel {
    padding: 1rem;
  }

  .meta-row {
    flex-direction: column;
  }

  .meta-card {
    width: 100%;
  }
}
</style>
