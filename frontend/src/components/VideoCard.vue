<template>
  <article class="video-card" @click="$emit('click')">
    <div class="poster-shell">
      <img v-if="showPoster" class="poster" :src="video.poster" :alt="video.title" @error="onPosterError">
      <div v-else class="poster-fallback">
        <span class="fallback-id">{{ video.id }}</span>
        <span class="fallback-text">LOCAL LIBRARY</span>
      </div>

      <div class="card-sheen"></div>
      <div class="card-index" v-if="indexLabel">{{ indexLabel }}</div>
    </div>

    <div class="card-meta">
      <p v-if="eyebrow" class="card-eyebrow">{{ eyebrow }}</p>
      <h3>{{ displayTitle }}</h3>
    </div>
  </article>
</template>

<script>
export default {
  props: {
    video: {
      type: Object,
      required: true
    },
    eyebrow: {
      type: String,
      default: ''
    },
    indexLabel: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      posterFailed: false
    }
  },
  computed: {
    showPoster() {
      return Boolean(this.video.poster) && !this.posterFailed
    },
    displayTitle() {
      const title = String(this.video?.title || '').trim()
      const id = String(this.video?.id || '').trim()
      if (!title || !id) {
        return title
      }

      const escapedId = id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const prefixPattern = new RegExp(`^${escapedId}[\\s._:：-]+`, 'i')
      return title.replace(prefixPattern, '').trim() || title
    }
  },
  watch: {
    'video.poster'() {
      this.posterFailed = false
    }
  },
  methods: {
    onPosterError() {
      this.posterFailed = true
    }
  }
}
</script>

<style scoped>
.video-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  cursor: pointer;
  width: 100%;
  transform-origin: center bottom;
  transition: transform 0.24s ease, z-index 0.24s ease;
}

.video-card:hover {
  z-index: 2;
  transform: translateY(-6px) scale(1.02);
}

.poster-shell {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1rem;
  background: linear-gradient(180deg, rgba(34, 34, 34, 0.96) 0%, rgba(14, 14, 14, 0.98) 100%);
  aspect-ratio: 0.72;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.22);
}

.poster,
.poster-fallback,
.card-sheen {
  position: absolute;
  inset: 0;
}

.poster {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.34s ease, filter 0.34s ease;
}

.video-card:hover .poster {
  transform: scale(1.04);
  filter: saturate(1.06);
}

.poster-fallback {
  display: grid;
  place-content: center;
  gap: 0.45rem;
  padding: 1rem;
  text-align: center;
  background: radial-gradient(circle at 28% 18%, rgba(211, 31, 43, 0.2), transparent 34%), #111111;
}

.fallback-id {
  color: rgba(230, 223, 213, 0.86);
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.9rem;
  letter-spacing: 0.08em;
}

.fallback-text {
  color: var(--text-soft);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.card-sheen {
  background:
    linear-gradient(180deg, rgba(0, 0, 0, 0.04) 10%, rgba(0, 0, 0, 0.16) 38%, rgba(0, 0, 0, 0.24) 100%),
    linear-gradient(130deg, rgba(255, 255, 255, 0.12) 0%, transparent 28%);
}

.card-index {
  position: absolute;
  left: 0.75rem;
  top: 0.7rem;
  z-index: 1;
  color: rgba(230, 223, 213, 0.8);
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.08rem;
  letter-spacing: 0.08em;
  text-shadow: 0 8px 20px rgba(0, 0, 0, 0.45);
}


.card-meta {
  display: flex;
  flex-direction: column;
  gap: 0.22rem;
  min-height: 0;
}

.card-eyebrow {
  margin: 0;
  color: rgba(230, 223, 213, 0.68);
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.card-meta h3 {
  margin: 0;
  color: rgba(230, 223, 213, 0.82);
  font-size: 0.84rem;
  line-height: 1.45;
  font-weight: 700;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

@media (max-width: 720px) {
  .video-card {
    gap: 0.45rem;
  }

  .video-card:hover {
    transform: translateY(-4px) scale(1.012);
  }

  .card-meta h3 {
    font-size: 0.78rem;
    line-height: 1.38;
  }
}
</style>




