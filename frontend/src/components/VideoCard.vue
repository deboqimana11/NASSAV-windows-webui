<template>
  <div class="video-card" @click="$emit('click')">
    <div class="poster-container">
      <img v-if="showPoster" class="poster" :src="video.poster" :alt="video.title" @error="onPosterError">
      <div v-else class="poster-fallback">
        <span class="fallback-id">{{ video.id }}</span>
        <span class="fallback-text">NO COVER</span>
      </div>
    </div>
    <div class="info">
      <h3>{{ video.title }}</h3>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    video: {
      type: Object,
      required: true
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
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 18px rgba(138, 32, 55, 0.08);
  width: 100%;
}

.video-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 14px 26px rgba(138, 32, 55, 0.14);
}

.poster-container {
  position: relative;
  width: 100%;
  padding-top: 137.78%;
  overflow: hidden;
  background: linear-gradient(160deg, #f8e7ea 0%, #f3d5da 100%);
}

.poster {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.poster-fallback {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  padding: 1rem;
  text-align: center;
  color: #7f3140;
}

.fallback-id {
  font-size: 1rem;
  line-height: 1.3;
  font-weight: 800;
  letter-spacing: 0.06em;
  word-break: break-word;
}

.fallback-text {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: #b8606d;
}

.info {
  padding: 9px 10px 11px;
  background: white;
}

h3 {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  font-weight: 600;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: #352129;
}
</style>
