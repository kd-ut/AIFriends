<script setup>
import {nextTick, onBeforeUnmount, onMounted, useTemplateRef} from "vue";
import Message from "@/components/character/chat_field/chat_history/message/Message.vue";
import api from "@/js/http/api.js";

const props = defineProps(['history', 'friendId', 'character'])
const emit = defineEmits(['pushFrontMessage'])
const scrollRef = useTemplateRef('scroll-ref')
const sentinelRef = useTemplateRef('sentinel-ref')
let isLoading = false
let hasMessages = true
let lastMessageId = 0

function checkSentinelVisible() {
  if (!sentinelRef.value || !scrollRef.value) return false
  const sentinelRect = sentinelRef.value.getBoundingClientRect()
  const scrollRect = scrollRef.value.getBoundingClientRect()
  return sentinelRect.top < scrollRect.bottom && sentinelRect.bottom > scrollRect.top
}

async function loadMore() {
  if (isLoading || !hasMessages) return
  isLoading = true
  let newMessages = []
  try {
    const {data} = await api.get('/api/friend/message/get_history/', {
      params: {last_message_id: lastMessageId, friend_id: props.friendId},
    })
    if (data.result === 'success') newMessages = data.messages
  } catch (error) {
    return
  } finally {
    isLoading = false
  }

  if (newMessages.length === 0) {
    hasMessages = false
    return
  }

  const oldHeight = scrollRef.value.scrollHeight
  const oldTop = scrollRef.value.scrollTop
  for (const item of newMessages) {
    emit('pushFrontMessage', {role: 'ai', content: item.output, id: `ai-${item.id}`})
    emit('pushFrontMessage', {role: 'user', content: item.user_message, id: `user-${item.id}`})
    lastMessageId = item.id
  }

  await nextTick()
  scrollRef.value.scrollTop = oldTop + scrollRef.value.scrollHeight - oldHeight
  if (checkSentinelVisible()) await loadMore()
}

let observer = null
onMounted(async () => {
  await loadMore()
  observer = new IntersectionObserver(entries => {
    if (entries.some(entry => entry.isIntersecting)) loadMore()
  }, {root: scrollRef.value, rootMargin: '2px', threshold: 0})
  if (sentinelRef.value) observer.observe(sentinelRef.value)
})

onBeforeUnmount(() => observer?.disconnect())

async function scrollToBottom() {
  await nextTick()
  if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
}

defineExpose({scrollToBottom})
</script>

<template>
  <div ref="scroll-ref" class="absolute top-18 left-0 w-90 h-112 overflow-y-scroll no-scrollbar">
    <div ref="sentinel-ref" class="h-2"></div>
    <Message v-for="item in history" :key="item.id" :message="item" :character="character" />
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
