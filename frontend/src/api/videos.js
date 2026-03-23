import axios from 'axios'

const API_KEY = import.meta.env.VITE_API_KEY || 'IBHUSDBWQHJEJOBDSW'

function resolveApiBase() {
  const configured = (import.meta.env.VITE_API_BASE || '').trim()

  if (typeof window !== 'undefined' && window.location?.hostname) {
    const currentHost = window.location.hostname
    const currentProtocol = window.location.protocol

    if (configured) {
      try {
        const configuredUrl = new URL(configured)
        const loopbackHosts = new Set(['127.0.0.1', 'localhost'])
        if (!(loopbackHosts.has(configuredUrl.hostname) && !loopbackHosts.has(currentHost))) {
          return configured
        }
      } catch (error) {
        return configured
      }
    }

    return `${currentProtocol}//${currentHost}:31471`
  }

  return configured || 'http://127.0.0.1:31471'
}

const API_BASE = resolveApiBase()

function withApiBase(path) {
  return `${API_BASE}${path}`
}

export default {
  async getVideoList() {
    const response = await axios.get(withApiBase('/api/videos'))
    return response.data.map((video) => ({
      ...video,
      poster: video.poster ? withApiBase(video.poster) : null
    }))
  },

  async getVideoDetail(id) {
    const response = await axios.get(withApiBase(`/api/videos/${id}`))
    const data = response.data

    return {
      ...data,
      poster: data.fanarts?.[0] ? withApiBase(data.fanarts[0]) : null,
      videoFile: data.videoFile ? withApiBase(data.videoFile) : null,
      fanarts: data.fanarts?.map((img) => withApiBase(img)) || []
    }
  },

  async getDownloadStatus() {
    const response = await axios.get(withApiBase('/api/status'))
    return response.data
  },

  async addVideo(id) {
    const normalizedId = id.trim().toUpperCase()
    const pattern = /^([A-Z0-9]+)-\d+$/

    if (!normalizedId) {
      throw new Error('请输入车牌号')
    }

    if (!pattern.test(normalizedId)) {
      throw new Error('格式错误：请输入类似 ABC-123 的车牌号')
    }

    const response = await axios.get(withApiBase(`/api/addvideo/${encodeURIComponent(normalizedId)}`), {
      headers: {
        Authorization: `Bearer ${API_KEY}`
      }
    })

    return {
      id: normalizedId,
      message: typeof response.data === 'string' ? response.data : '提交成功'
    }
  }
}

