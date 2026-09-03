import {fetchEventSource} from '@microsoft/fetch-event-source';
import {useUserStore} from "@/stores/user.js";
import api from "./api.js";
import CONFIG_API from "@/js/config/config.js";

const BASE_URL = CONFIG_API.HTTP_URL

export default async function streamApi(url, options = {}) {
  const userStore = useUserStore()

  const startFetch = async () => fetchEventSource(BASE_URL + url, {
    method: options.method || 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${userStore.accessToken}`,
      ...options.headers,
    },
    body: JSON.stringify(options.body || {}),
    openWhenHidden: true,
    async onopen(response) {
      if (response.status === 401) {
        const refreshResponse = await api.post('/api/user/account/refresh_token/', {})
        userStore.setAccessToken(refreshResponse.data.access)
        throw new Error('TOKEN_REFRESHED')
      }
      if (!response.ok || !response.headers.get('content-type')?.includes('text/event-stream')) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.result || errorData.detail || `请求失败: ${response.status}`)
      }
    },
    onmessage(message) {
      if (message.data === '[DONE]') {
        options.onmessage?.('', true)
        return
      }
      try {
        options.onmessage?.(JSON.parse(message.data), false)
      } catch (error) {
        console.error('流解析失败:', error)
      }
    },
    onerror(error) {
      if (error.message === 'TOKEN_REFRESHED') return startFetch()
      options.onerror?.(error)
      throw error
    },
    onclose: options.onclose,
  })

  return startFetch()
}
