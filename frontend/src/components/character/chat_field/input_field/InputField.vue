<script setup>
import {ref, useTemplateRef} from "vue";
import SendIcon from "@/components/character/icons/SendIcon.vue";
import MicIcon from "@/components/character/icons/MicIcon.vue";
import streamApi from "@/js/http/streamApi.js";

const props = defineProps(['friendId'])
const emit = defineEmits(['pushBackMessage', 'addToLastMessage'])
const inputRef = useTemplateRef('input-ref')
const message = ref('')
const isProcessing = ref(false)

function focus() {
  inputRef.value?.focus()
}

async function handleSend() {
  const content = message.value.trim()
  if (isProcessing.value || !content) return

  isProcessing.value = true
  message.value = ''
  emit('pushBackMessage', {role: 'user', content, id: crypto.randomUUID()})
  emit('pushBackMessage', {role: 'ai', content: '', id: crypto.randomUUID()})

  try {
    await streamApi('/api/friend/message/chat/', {
      body: {friend_id: props.friendId, message: content},
      onmessage(data, isDone) {
        if (isDone) isProcessing.value = false
        else if (data.content) emit('addToLastMessage', data.content)
      },
      onerror() {
        isProcessing.value = false
      },
    })
  } catch (error) {
    isProcessing.value = false
  }
}

defineExpose({focus})
</script>

<template>
  <form @submit.prevent="handleSend" class="absolute bottom-4 left-2 h-12 w-86 flex items-center">
    <input
        ref="input-ref"
        v-model="message"
        :disabled="isProcessing"
        class="input bg-black/30 backdrop-blur-sm text-white text-base w-full h-full rounded-2xl pr-20"
        type="text"
        placeholder="文本输入..."
    >
    <button type="submit" :disabled="isProcessing" class="absolute right-2 w-8 h-8 flex justify-center items-center cursor-pointer disabled:opacity-50">
      <SendIcon />
    </button>
    <button type="button" class="absolute right-10 w-8 h-8 flex justify-center items-center cursor-pointer">
      <MicIcon />
    </button>
  </form>
</template>
