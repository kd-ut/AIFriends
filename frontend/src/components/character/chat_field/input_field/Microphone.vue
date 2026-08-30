<script setup>
import {onBeforeUnmount, onMounted, ref} from "vue";
import {MicVAD} from "@ricky0123/vad-web";
import KeyboardIcon from "@/components/character/icons/KeyboardIcon.vue";
import api from "@/js/http/api.js";

const emit = defineEmits(['close', 'send', 'stop'])
const isSpeaking = ref(false)
const statusText = ref('正在初始化麦克风…')
let vadInstance = null

function float32ToInt16(float32Array) {
  const buffer = new Int16Array(float32Array.length)
  for (let index = 0; index < float32Array.length; index++) {
    const sample = Math.max(-1, Math.min(1, float32Array[index]))
    buffer[index] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
  }
  return buffer.buffer
}

async function sendToBackend(arrayBuffer) {
  statusText.value = '正在识别…'
  const formData = new FormData()
  formData.append('audio', new Blob([arrayBuffer], {type: 'audio/pcm'}), 'voice.pcm')
  try {
    const {data} = await api.post('/api/friend/message/asr/asr/', formData)
    if (data.result === 'success' && data.text?.trim()) {
      emit('send', null, data.text)
      statusText.value = '语音输入'
    } else {
      statusText.value = data.result || '没有识别到语音'
    }
  } catch (error) {
    statusText.value = error.response?.data?.result || '语音识别失败'
  }
}

async function startRecording() {
  const baseUrl = import.meta.env.DEV ? '/vad-runtime/' : '/static/frontend/vad-runtime-v2/'
  try {
    vadInstance = await MicVAD.new({
      model: 'v5',
      baseAssetPath: baseUrl,
      onnxWASMBasePath: baseUrl,
      onSpeechStart: () => {
        isSpeaking.value = true
        statusText.value = '正在聆听…'
        emit('stop')
      },
      onSpeechEnd: audio => {
        isSpeaking.value = false
        sendToBackend(float32ToInt16(audio))
      },
      ortConfig: ort => {
        ort.env.wasm.wasmPaths = baseUrl
        ort.env.wasm.numThreads = 1
        ort.env.logLevel = 'error'
      },
      positiveSpeechThreshold: 0.8,
      negativeSpeechThreshold: 0.65,
      minSpeechFrames: 5,
      redemptionFrames: 5,
    })
    await vadInstance.start()
    statusText.value = '语音输入'
  } catch (error) {
    console.error('VAD 初始化失败:', error)
    const detail = error?.message || String(error)
    const permissionDenied = error?.name === 'NotAllowedError' || /permission|denied|not allowed/i.test(detail)
    statusText.value = permissionDenied ? '请允许麦克风权限' : `初始化失败：${detail}`
  }
}

onMounted(startRecording)
onBeforeUnmount(() => {
  vadInstance?.destroy()
  vadInstance = null
})
</script>

<template>
  <div class="absolute bottom-4 left-2 h-12 w-86 flex items-center bg-black/30 backdrop-blur-sm rounded-2xl">
    <div v-if="isSpeaking" class="flex items-center justify-center gap-1 h-6 flex-1">
      <div v-for="index in 32" :key="index" class="w-0.5 bg-blue-400 rounded-full animate-wave" :style="{animationDelay: `${index * 0.1}s`}"></div>
    </div>
    <div v-else class="text-white/60 text-base w-full text-center">{{ statusText }}</div>
    <button type="button" @click="emit('close')" class="absolute right-2 w-8 h-8 flex justify-center items-center cursor-pointer">
      <KeyboardIcon />
    </button>
  </div>
</template>

<style scoped>
.animate-wave { height: 4px; animation: wave-animation 0.6s ease-in-out infinite alternate; }
@keyframes wave-animation {
  0% { height: 4px; opacity: 0.3; }
  100% { height: 20px; opacity: 1; }
}
</style>
