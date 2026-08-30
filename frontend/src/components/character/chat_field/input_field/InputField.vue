<script setup>
import {defineAsyncComponent, onUnmounted, ref, useTemplateRef} from "vue";
import SendIcon from "@/components/character/icons/SendIcon.vue";
import MicIcon from "@/components/character/icons/MicIcon.vue";
import streamApi from "@/js/http/streamApi.js";

const Microphone = defineAsyncComponent(() => import("@/components/character/chat_field/input_field/Microphone.vue"))

const props = defineProps(['friendId'])
const emit = defineEmits(['pushBackMessage', 'addToLastMessage'])
const inputRef = useTemplateRef('input-ref')
const message = ref('')
const showMic = ref(false)
const needsPlaybackGesture = ref(false)
let processId = 0
let audioUnlockPromise = Promise.resolve()

let mediaSource = null
let sourceBuffer = null
let audioPlayer = new Audio()
let audioQueue = []
let isUpdating = false
let audioObjectUrl = ''

function processQueue() {
  if (isUpdating || audioQueue.length === 0 || !sourceBuffer || sourceBuffer.updating) return
  isUpdating = true
  try {
    sourceBuffer.appendBuffer(audioQueue.shift())
  } catch (error) {
    console.error('写入语音数据失败:', error)
    isUpdating = false
  }
}

function initAudioStream() {
  stopAudio()
  if (!window.MediaSource || !MediaSource.isTypeSupported('audio/mpeg')) return

  mediaSource = new MediaSource()
  audioObjectUrl = URL.createObjectURL(mediaSource)
  audioPlayer.src = audioObjectUrl
  mediaSource.addEventListener('sourceopen', () => {
    try {
      sourceBuffer = mediaSource.addSourceBuffer('audio/mpeg')
      sourceBuffer.addEventListener('updateend', () => {
        isUpdating = false
        processQueue()
      })
    } catch (error) {
      console.error('初始化语音播放器失败:', error)
    }
  }, {once: true})
  tryPlayAudio()
}

async function tryPlayAudio() {
  try {
    await audioPlayer.play()
    needsPlaybackGesture.value = false
  } catch (error) {
    needsPlaybackGesture.value = true
    console.warn('浏览器阻止了自动播放:', error)
  }
}

async function unlockAudio() {
  const silentWav = 'data:audio/wav;base64,UklGRiYAAABXQVZFZm10IBAAAAABAAEAgD4AAAB9AAACABAAZGF0YQIAAAAAAA=='
  audioPlayer.src = silentWav
  audioPlayer.volume = 0
  try {
    await audioPlayer.play()
    audioPlayer.pause()
    needsPlaybackGesture.value = false
  } catch (error) {
    console.warn('预解锁音频失败:', error)
  } finally {
    audioPlayer.volume = 1
    audioPlayer.removeAttribute('src')
    audioPlayer.load()
  }
}

function handleOpenMicrophone() {
  // 必须在用户点击事件中调用 play，才能解锁 Chrome 的自动播放限制。
  audioUnlockPromise = unlockAudio()
  showMic.value = true
}

function stopAudio() {
  audioPlayer.pause()
  audioQueue = []
  isUpdating = false
  sourceBuffer = null
  if (mediaSource?.readyState === 'open') {
    try { mediaSource.endOfStream() } catch (error) {}
  }
  mediaSource = null
  if (audioObjectUrl) URL.revokeObjectURL(audioObjectUrl)
  audioObjectUrl = ''
  audioPlayer.removeAttribute('src')
}

function handleAudioChunk(base64Data) {
  try {
    const binary = atob(base64Data)
    const bytes = new Uint8Array(binary.length)
    for (let index = 0; index < binary.length; index++) bytes[index] = binary.charCodeAt(index)
    audioQueue.push(bytes)
    processQueue()
    if (audioPlayer.paused) tryPlayAudio()
  } catch (error) {
    console.error('解析语音数据失败:', error)
  }
}

function focus() {
  inputRef.value?.focus()
}

async function handleSend(event, audioMessage) {
  const content = (audioMessage || message.value).trim()
  if (!content) return

  await audioUnlockPromise
  const currentId = ++processId
  message.value = ''
  initAudioStream()
  emit('pushBackMessage', {role: 'user', content, id: crypto.randomUUID()})
  emit('pushBackMessage', {role: 'ai', content: '', id: crypto.randomUUID()})

  try {
    await streamApi('/api/friend/message/chat/', {
      body: {friend_id: props.friendId, message: content},
      onmessage(data) {
        if (currentId !== processId) return
        if (data.content) emit('addToLastMessage', data.content)
        if (data.audio) handleAudioChunk(data.audio)
        if (data.error) console.error(data.error)
      },
    })
  } catch (error) {
    console.error('发送消息失败:', error)
  }
}

function close() {
  ++processId
  showMic.value = false
  stopAudio()
}

function handleStop() {
  ++processId
  stopAudio()
}

onUnmounted(stopAudio)
defineExpose({focus, close})
</script>

<template>
  <form v-if="!showMic" @submit.prevent="handleSend" class="absolute bottom-4 left-2 h-12 w-86 flex items-center">
    <input
        ref="input-ref"
        v-model="message"
        class="input bg-black/30 backdrop-blur-sm text-white text-base w-full h-full rounded-2xl pr-20"
        type="text"
        placeholder="文本输入..."
    >
    <button type="submit" class="absolute right-2 w-8 h-8 flex justify-center items-center cursor-pointer">
      <SendIcon />
    </button>
    <button type="button" @click="handleOpenMicrophone" class="absolute right-10 w-8 h-8 flex justify-center items-center cursor-pointer">
      <MicIcon />
    </button>
  </form>
  <Microphone v-else @close="showMic = false" @send="handleSend" @stop="handleStop" />
  <button
      v-if="needsPlaybackGesture"
      type="button"
      @click="tryPlayAudio"
      class="absolute bottom-18 left-1/2 -translate-x-1/2 btn btn-sm bg-black/70 text-white border-0"
  >
    ▶ 播放语音
  </button>
</template>
