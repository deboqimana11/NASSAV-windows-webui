<template>
  <div class="detail-shell" v-if="video">
    <section class="detail-hero" :style="heroStyle">
      <div class="detail-hero-scrim"></div>
      <div class="detail-hero-inner">
        <router-link class="back-link" to="/">返回片库</router-link>

        <div class="hero-copy">
          <p class="hero-kicker">Private Screening</p>
          <h1>{{ video.id }}</h1>
          <p class="hero-title">{{ video.title }}</p>

          <div class="hero-meta">
            <span class="meta-pill meta-pill-strong">{{ video.videoFile ? '\u7acb\u5373\u64ad\u653e' : '\u7b49\u5f85\u4e0b\u8f7d' }}</span>
            <span class="meta-pill">{{ `\u53d1\u884c ${video.releaseDate || '\u672a\u77e5'}` }}</span>
            <span class="meta-pill">{{ `${video.fanarts?.length || 0} \u5f20\u5267\u7167` }}</span>
          </div>

          <p class="hero-summary">
            {{ video.videoFile ? '\u672c\u5730\u89c6\u9891\u5df2\u7ecf\u51c6\u5907\u597d\uff0c\u4e0b\u9762\u53ef\u4ee5\u76f4\u63a5\u89c2\u770b\uff0c\u5e76\u7ee7\u7eed\u6d4f\u89c8\u5267\u7167\u4e0e\u7247\u5e93\u4fe1\u606f\u3002' : '\u5f53\u524d\u5148\u5c55\u793a\u5f71\u7247\u4fe1\u606f\u4e0e\u5267\u7167\uff0c\u7b49\u4e0b\u8f7d\u5b8c\u6210\u540e\u8fd9\u91cc\u4f1a\u81ea\u52a8\u53d8\u6210\u53ef\u64ad\u653e\u72b6\u6001\u3002' }}
          </p>
        </div>
      </div>
    </section>

    <section class="playback-layout">
      <div class="playback-main">
        <div class="player-shell">
          <p class="section-kicker player-kicker">Now Playing</p>
          <div v-if="video.videoFile" class="video-player">
            <video
              class="player"
              :poster="video.poster"
              controls
              preload="metadata"
              playsinline
            >
              <source :src="video.videoFile" type="video/mp4">
              {{ '\u4f60\u7684\u6d4f\u89c8\u5668\u6682\u4e0d\u652f\u6301 HTML5 \u89c6\u9891\u64ad\u653e\u3002' }}
            </video>
          </div>

          <div v-else class="video-unavailable">
            <div class="video-unavailable-copy">
              <span class="video-unavailable-kicker">Video Pending</span>
              <strong>{{ '\u5f53\u524d\u8fd8\u6ca1\u6709\u53ef\u64ad\u653e\u7684\u89c6\u9891\u6587\u4ef6' }}</strong>
              <p>{{ '\u7b49\u4e0b\u8f7d\u4efb\u52a1\u5b8c\u6210\u540e\uff0c\u8fd9\u91cc\u4f1a\u81ea\u52a8\u663e\u793a\u64ad\u653e\u5668\u3002\u4f60\u73b0\u5728\u53ef\u4ee5\u5148\u67e5\u770b\u5267\u7167\u3001\u53d1\u884c\u65e5\u671f\u548c\u7247\u5e93\u4fe1\u606f\u3002' }}</p>
            </div>
          </div>
        </div>
      </div>

      <aside class="detail-sidebar">
        <div class="sidebar-panel">
          <p class="section-kicker">Library Facts</p>
          <div class="fact-list">
            <div class="fact-row">
              <span>影片编号</span>
              <strong>{{ video.id }}</strong>
            </div>
            <div class="fact-row">
              <span>播放状态</span>
              <strong>{{ video.videoFile ? '\u53ef\u76f4\u63a5\u64ad\u653e' : '\u7b49\u5f85\u89c6\u9891\u6587\u4ef6' }}</strong>
            </div>
            <div class="fact-row">
              <span>发行日期</span>
              <strong>{{ video.releaseDate || '\u672a\u77e5' }}</strong>
            </div>
            <div class="fact-row">
              <span>剧照数量</span>
              <strong>{{ `${video.fanarts?.length || 0} \u5f20` }}</strong>
            </div>
          </div>
        </div>
      </aside>
    </section>

    <section class="gallery-band">
      <div class="gallery-band-head">
        <div>
          <p class="section-kicker">Scene Stills</p>
          <h2>剧照集锦</h2>
        </div>
        <p class="gallery-band-note">点开剧照即可进入全屏查看，左右切换浏览整组图片。</p>
      </div>

      <Gallery :images="video.fanarts" />
    </section>
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
  computed: {
    heroStyle() {
      if (!this.video?.poster) {
        return {}
      }
      return {
        backgroundImage: `linear-gradient(90deg, rgba(8, 9, 12, 0.96) 0%, rgba(8, 9, 12, 0.78) 44%, rgba(8, 9, 12, 0.92) 100%), url(${this.video.poster})`
      }
    }
  },
  async created() {
    await this.loadVideo()
  },
  watch: {
    id() {
      this.loadVideo()
    }
  },
  methods: {
    scrollToTop() {
      window.scrollTo({ top: 0, behavior: 'auto' })
    },
    async loadVideo() {
      this.scrollToTop()
      this.video = await videosApi.getVideoDetail(this.id)
      this.$nextTick(() => {
        this.scrollToTop()
      })
    }
  }
}
</script>

<style scoped>
.detail-shell {
  display: flex;
  flex-direction: column;
  gap: 1.35rem;
  color: rgba(230, 223, 213, 0.88);
}

.detail-hero {
  position: relative;
  min-height: clamp(15rem, 34vw, 23rem);
  margin: -0.45rem 0 0;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 1.7rem;
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(12, 13, 17, 0.98), rgba(27, 21, 25, 0.94)),
    radial-gradient(circle at top right, rgba(185, 34, 52, 0.22), transparent 28%);
  background-size: cover;
  background-position: center 20%;
  box-shadow: 0 28px 60px rgba(0, 0, 0, 0.3);
}

.detail-hero-scrim {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(0, 0, 0, 0.04), rgba(0, 0, 0, 0.36)),
    linear-gradient(90deg, rgba(0, 0, 0, 0.24), transparent 48%, rgba(0, 0, 0, 0.42));
}

.detail-hero-inner {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: inherit;
  padding: clamp(1.1rem, 2vw, 1.5rem);
}

.back-link {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  min-height: 2.4rem;
  padding: 0 0.9rem;
  border-radius: 999px;
  color: rgba(230, 223, 213, 0.88);
  text-decoration: none;
  font-size: 0.84rem;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(10px);
}

.hero-copy {
  max-width: min(44rem, 100%);
}

.hero-kicker,
.section-kicker {
  margin: 0 0 0.38rem;
  color: rgba(255, 206, 162, 0.7);
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.hero-copy h1,
.gallery-band-head h2 {
  font-family: 'Arial Narrow', 'Impact', sans-serif;
}

.hero-copy h1 {
  margin: 0;
  font-size: clamp(2.2rem, 5.4vw, 4.4rem);
  line-height: 0.9;
  letter-spacing: 0.04em;
  color: rgba(236, 229, 219, 0.92);
}

.hero-title {
  max-width: 42rem;
  margin: 0.55rem 0 0;
  color: rgba(230, 223, 213, 0.82);
  font-size: clamp(0.98rem, 1.25vw, 1.12rem);
  line-height: 1.6;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-top: 1rem;
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: 0 0.8rem;
  border-radius: 999px;
  color: rgba(230, 223, 213, 0.84);
  font-size: 0.8rem;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.08);
}

.meta-pill-strong {
  color: #1e0d11;
  background: linear-gradient(135deg, #e3bd7a, #f0d7bb);
}

.hero-summary {
  max-width: 37rem;
  margin: 1rem 0 0;
  color: rgba(230, 223, 213, 0.74);
  font-size: 0.96rem;
  line-height: 1.7;
}

.playback-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.75fr) minmax(17.5rem, 0.78fr);
  gap: 1.2rem;
  align-items: start;
}

.playback-main,
.detail-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.player-shell,
.sidebar-panel,
.gallery-band {
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 1.35rem;
  background: linear-gradient(180deg, rgba(18, 20, 27, 0.96), rgba(10, 12, 16, 0.98));
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.22);
}

.player-shell {
  padding: 0.9rem;
}

.player-kicker {
  margin-bottom: 0.7rem;
}

.video-player {
  overflow: hidden;
  border-radius: 1rem;
  background: #06070a;
}

.player {
  display: block;
  width: 100%;
  max-height: 74vh;
  background: #06070a;
}

.video-unavailable {
  min-height: 25rem;
  display: grid;
  place-items: center;
  border-radius: 1rem;
  background:
    radial-gradient(circle at top, rgba(181, 34, 52, 0.16), transparent 34%),
    linear-gradient(180deg, rgba(18, 21, 28, 0.96), rgba(7, 9, 13, 0.98));
}

.video-unavailable-copy {
  max-width: 28rem;
  padding: 1.4rem;
}

.video-unavailable-kicker {
  display: inline-block;
  margin-bottom: 0.45rem;
  color: rgba(255, 206, 162, 0.66);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.video-unavailable-copy strong {
  display: block;
  color: rgba(236, 229, 219, 0.92);
  font-size: 1.4rem;
}

.video-unavailable-copy p,
.gallery-band-note {
  margin: 0.75rem 0 0;
  color: rgba(230, 223, 213, 0.72);
  line-height: 1.7;
}

.sidebar-panel {
  padding: 1rem;
}

.fact-list {
  display: grid;
  gap: 0.9rem;
}

.fact-row {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  padding-bottom: 0.85rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

.fact-row:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.fact-row span {
  color: rgba(230, 223, 213, 0.58);
  font-size: 0.8rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.fact-row strong {
  color: rgba(230, 223, 213, 0.88);
  font-size: 0.92rem;
  text-align: right;
}

.gallery-band {
  padding: 1.15rem;
}

.gallery-band-head {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 1rem;
  margin-bottom: 1rem;
}

.gallery-band-head h2 {
  font-size: clamp(1.9rem, 4vw, 2.7rem);
  line-height: 0.95;
  letter-spacing: 0.03em;
}

.gallery-band-note {
  margin: 0;
  max-width: 28rem;
  text-align: right;
}

@media (max-width: 1120px) {
  .playback-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .detail-hero {
    min-height: 14rem;
    border-radius: 1.35rem;
  }

  .detail-hero-inner {
    padding: 1rem;
  }

  .hero-copy h1 {
    font-size: clamp(2rem, 9vw, 3rem);
  }

  .hero-title {
    font-size: 0.92rem;
  }

  .player-shell,
  .sidebar-panel,
  .gallery-band {
    border-radius: 1.15rem;
  }

  .player-shell {
    padding: 0.7rem;
  }

  .gallery-band-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .player {
    max-height: none;
  }

  .video-unavailable {
    min-height: 17rem;
  }

  .gallery-band-note {
    text-align: left;
  }
}
</style>


