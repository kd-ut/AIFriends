<script setup>
import {ref, watch} from 'vue'

const props = defineProps(['voices', 'curVoiceId'])
const myVoice = ref(props.curVoiceId)

watch(() => props.curVoiceId, value => {
  myVoice.value = value
})

defineExpose({myVoice})
</script>

<template>
  <fieldset class="fieldset">
    <label class="label text-base">音色</label>
    <select v-model="myVoice" class="select w-full">
      <option v-for="voice in voices" :key="voice.id" :value="voice.id">
        {{ voice.name }}
      </option>
    </select>
  </fieldset>
</template>
