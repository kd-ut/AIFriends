<script setup>
import {computed, nextTick, ref, useTemplateRef} from "vue";
import InputField from "@/components/character/chat_field/input_field/InputField.vue";
import CharacterPhotoField from "@/components/character/chat_field/character_photo_field/CharacterPhotoField.vue";
import ChatHistory from "@/components/character/chat_field/chat_history/ChatHistory.vue";

const props = defineProps(['friend'])
const modalRef = useTemplateRef('modal-ref')
const inputRef = useTemplateRef('input-ref')
const chatHistoryRef = useTemplateRef('chat-history-ref')
const history = ref([])

async function showModal() {
  modalRef.value.showModal()
  await nextTick()
  inputRef.value?.focus()
}

const modalStyle = computed(() => props.friend ? {
  backgroundImage: `url(${props.friend.character.background_image})`,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
  backgroundRepeat: 'no-repeat',
} : {})

async function handlePushBackMessage(message) {
  history.value.push(message)
  await chatHistoryRef.value?.scrollToBottom()
}

async function handleAddToLastMessage(delta) {
  const lastMessage = history.value.at(-1)
  if (lastMessage) lastMessage.content += delta
  await chatHistoryRef.value?.scrollToBottom()
}

function handlePushFrontMessage(message) {
  history.value.unshift(message)
}

function handleClose() {
  modalRef.value.close()
  inputRef.value?.close()
}

defineExpose({showModal})
</script>

<template>
  <dialog ref="modal-ref" class="modal">
    <div class="modal-box w-90 h-150" :style="modalStyle">
      <button @click="handleClose" class="btn btn-sm btn-circle btn-ghost bg-transparent absolute right-1 top-1">✕</button>
      <ChatHistory
          ref="chat-history-ref"
          v-if="friend"
          :history="history"
          :friend-id="friend.id"
          :character="friend.character"
          @push-front-message="handlePushFrontMessage"
      />
      <InputField
          v-if="friend"
          ref="input-ref"
          :friend-id="friend.id"
          @push-back-message="handlePushBackMessage"
          @add-to-last-message="handleAddToLastMessage"
      />
      <CharacterPhotoField v-if="friend" :character="friend.character" />
    </div>
  </dialog>
</template>
