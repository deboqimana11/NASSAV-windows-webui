<template>
  <div class="gallery-shell" v-if="images.length > 0">
    <div class="gallery-grid">
      <button
        v-for="(image, index) in images"
        :key="index"
        type="button"
        class="gallery-tile"
        :class="{ 'gallery-tile-featured': index === 0 && images.length > 2 }"
        @click="openLightbox(index)"
      >
        <img
          :src="image"
          :alt="'剧照 ' + (index + 1)"
          loading="lazy"
        >

      </button>
    </div>

    <transition name="lightbox-fade">
      <div
        v-if="showLightbox"
        class="lightbox"
        @click.self="closeLightbox"
      >
        <div class="lightbox-shell">
          <div class="lightbox-topbar">
            <div>
              <p class="lightbox-kicker">Scene Stills</p>
              <strong>第 {{ currentIndex + 1 }} 张，共 {{ images.length }} 张</strong>
            </div>
            <button class="close-btn" @click="closeLightbox">关闭</button>
          </div>

          <div class="lightbox-stage">
            <button class="nav-btn prev" @click.stop="prevImage" aria-label="上一张">
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="currentColor" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
              </svg>
            </button>

            <img
              :src="images[currentIndex]"
              class="lightbox-image"
              @click.stop
            >

            <button class="nav-btn next" @click.stop="nextImage" aria-label="下一张">
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="currentColor" d="m8.59 16.59 1.41 1.41 6-6-6-6-1.41 1.41L13.17 12z"/>
              </svg>
            </button>
          </div>

          <div class="thumb-strip">
            <button
              v-for="(image, index) in images"
              :key="`thumb-${index}`"
              type="button"
              class="thumb-btn"
              :class="{ 'thumb-btn-active': index === currentIndex }"
              @click="currentIndex = index"
            >
              <img :src="image" :alt="'缩略图 ' + (index + 1)">
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>

  <div v-else class="gallery-empty">
    <p class="lightbox-kicker">Scene Stills</p>
    <strong>暂时没有可展示的剧照</strong>
    <span>等抓取到剧照资源后，这里会自动补齐画廊内容。</span>
  </div>
</template>

<script>
export default {
  props: {
    images: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      showLightbox: false,
      currentIndex: 0
    }
  },
  beforeUnmount() {
    document.body.style.overflow = ''
    document.removeEventListener('keydown', this.handleKeydown)
  },
  methods: {
    openLightbox(index) {
      this.currentIndex = index
      this.showLightbox = true
      document.body.style.overflow = 'hidden'
      document.addEventListener('keydown', this.handleKeydown)
    },
    closeLightbox() {
      this.showLightbox = false
      document.body.style.overflow = ''
      document.removeEventListener('keydown', this.handleKeydown)
    },
    prevImage() {
      this.currentIndex = (this.currentIndex - 1 + this.images.length) % this.images.length
    },
    nextImage() {
      this.currentIndex = (this.currentIndex + 1) % this.images.length
    },
    handleKeydown(e) {
      if (e.key === 'Escape') this.closeLightbox()
      if (e.key === 'ArrowLeft') this.prevImage()
      if (e.key === 'ArrowRight') this.nextImage()
    }
  }
}
</script>

<style scoped>
.gallery-shell,
.gallery-empty {
  min-width: 0;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  grid-auto-rows: 170px;
  gap: 0.9rem;
}

.gallery-tile {
  position: relative;
  padding: 0;
  border: none;
  border-radius: 1rem;
  overflow: hidden;
  cursor: pointer;
  background: #0d1016;
  box-shadow: 0 12px 26px rgba(0, 0, 0, 0.22);
  transition: transform 0.26s ease, box-shadow 0.26s ease, filter 0.26s ease;
}

.gallery-tile-featured {
  grid-column: span 2;
  grid-row: span 2;
}

.gallery-tile:hover {
  transform: translateY(-4px);
  box-shadow: 0 18px 34px rgba(0, 0, 0, 0.32);
  filter: brightness(1.04);
}

.gallery-tile::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, transparent 42%, rgba(0, 0, 0, 0.74)),
    linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, transparent 24%);
}

.gallery-tile img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}


.gallery-empty {
  display: grid;
  gap: 0.4rem;
  padding: 1rem 0.2rem 0.1rem;
}

.gallery-empty strong {
  color: rgba(230, 223, 213, 0.88);
  font-size: 1.05rem;
}

.gallery-empty span {
  color: rgba(230, 223, 213, 0.68);
  line-height: 1.7;
}

.lightbox {
  position: fixed;
  inset: 0;
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(4, 5, 9, 0.92);
  backdrop-filter: blur(16px);
}

.lightbox-shell {
  width: min(94vw, 92rem);
  max-height: 94vh;
  display: grid;
  gap: 0.9rem;
  padding: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1.35rem;
  background: linear-gradient(180deg, rgba(18, 20, 27, 0.98), rgba(8, 10, 15, 0.98));
  box-shadow: 0 28px 70px rgba(0, 0, 0, 0.45);
}

.lightbox-topbar {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 1rem;
}

.lightbox-kicker {
  margin: 0 0 0.25rem;
  color: rgba(255, 206, 162, 0.66);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.lightbox-topbar strong {
  color: rgba(230, 223, 213, 0.88);
  font-size: 1rem;
}

.close-btn {
  min-height: 2.3rem;
  padding: 0 0.92rem;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  color: rgba(230, 223, 213, 0.88);
  font-weight: 700;
  background: rgba(255, 255, 255, 0.06);
  cursor: pointer;
}

.lightbox-stage {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 0;
}

.lightbox-image {
  display: block;
  max-width: 100%;
  max-height: 68vh;
  border-radius: 1rem;
  box-shadow: 0 14px 40px rgba(0, 0, 0, 0.4);
}

.nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 3rem;
  height: 3rem;
  border: none;
  border-radius: 999px;
  color: rgba(236, 229, 219, 0.9);
  background: rgba(255, 255, 255, 0.08);
  cursor: pointer;
  display: grid;
  place-items: center;
}

.nav-btn.prev {
  left: 0.8rem;
}

.nav-btn.next {
  right: 0.8rem;
}

.thumb-strip {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 5.4rem;
  gap: 0.6rem;
  overflow-x: auto;
  padding-bottom: 0.15rem;
}

.thumb-btn {
  padding: 0;
  border: 1px solid transparent;
  border-radius: 0.75rem;
  overflow: hidden;
  background: transparent;
  cursor: pointer;
  opacity: 0.52;
  transition: opacity 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.thumb-btn img {
  display: block;
  width: 100%;
  height: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
}

.thumb-btn-active {
  opacity: 1;
  transform: translateY(-1px);
  border-color: rgba(241, 197, 128, 0.82);
}

.lightbox-fade-enter-active,
.lightbox-fade-leave-active {
  transition: opacity 0.25s ease;
}

.lightbox-fade-enter-from,
.lightbox-fade-leave-to {
  opacity: 0;
}

@media (max-width: 900px) {
  .gallery-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-auto-rows: 140px;
  }

  .gallery-tile-featured {
    grid-column: span 2;
    grid-row: span 2;
  }

  .lightbox-shell {
    width: 100%;
    max-height: 100%;
    padding: 0.85rem;
    border-radius: 1rem;
  }

  .lightbox-image {
    max-height: 56vh;
  }
}

@media (max-width: 640px) {
  .gallery-grid {
    grid-template-columns: 1fr 1fr;
    grid-auto-rows: 118px;
    gap: 0.7rem;
  }

  .lightbox-topbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .nav-btn {
    width: 2.55rem;
    height: 2.55rem;
  }

  .nav-btn.prev {
    left: 0.35rem;
  }

  .nav-btn.next {
    right: 0.35rem;
  }

  .thumb-strip {
    grid-auto-columns: 4.6rem;
  }
}
</style>

