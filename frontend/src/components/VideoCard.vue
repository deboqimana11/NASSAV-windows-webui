<template>
  <div class="video-card" @click="$emit('click')">
    <div class="poster-container">
      <img class="poster" :src="video.poster" :alt="video.title">
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
  background: #f6e4e8;
}

.poster {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
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
