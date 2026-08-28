<script setup>
import {onBeforeUnmount, ref, useTemplateRef, watch} from "vue";
import CameraIcon from "@/views/user/profile/components/icon/CameraIcon.vue";
import Croppie from "croppie";

const props = defineProps(['backgroundImage'])
const myBackgroundImage = ref(props.backgroundImage)

watch(() => props.backgroundImage, newVal => {
  myBackgroundImage.value = newVal
})

const fileInputRef = useTemplateRef('file-input-ref')
const modalRef = useTemplateRef('modal-ref')
const croppieRef = useTemplateRef('croppie-ref')
let croppie = null

async function openModal(photo) {
  modalRef.value.showModal()

  if (!croppie) {
    croppie = new Croppie(croppieRef.value, {
      viewport: {width: 300, height: 500},
      boundary: {width: 600, height: 600},
      enableOrientation: true,
      enforceBoundary: true,
    })
  }

  croppie.bind({
    url: photo,
  })
}

async function crop() {
  if (!croppie) return

  myBackgroundImage.value = await croppie.result({
    type: 'base64',
    size: 'viewport',
  })

  modalRef.value.close()
}

function onFileChange(e) {
  const file = e.target.files[0]
  e.target.value = ''
  if (!file) return

  const reader = new FileReader()
  reader.onload = () => {
    openModal(reader.result)
  }
  reader.readAsDataURL(file)
}

onBeforeUnmount(() => {
  croppie?.destroy()
})

defineExpose({
  myBackgroundImage,
})
</script>

<template>
  <fieldset class="fieldset">
    <label class="label text-base">聊天背景</label>
    <div class="avatar relative">
      <div v-if="myBackgroundImage" class="w-15 h-25 rounded-box">
        <img :src="myBackgroundImage" alt="">
      </div>
      <div v-else class="w-15 h-25 rounded-box bg-base-200"></div>
      <div @click="fileInputRef.click()" class="w-15 h-25 rounded-box absolute left-0 top-0 bg-black/20 flex justify-center items-center cursor-pointer">
        <CameraIcon />
      </div>
    </div>
  </fieldset>

  <input ref="file-input-ref" type="file" class="hidden" accept="image/*" @change="onFileChange">

  <dialog ref="modal-ref" class="modal">
    <div class="modal-box transition-none max-w-2xl">
      <button @click="modalRef.close()" class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>

      <div ref="croppie-ref" class="flex flex-col my-4"></div>

      <div class="modal-action">
        <button @click="modalRef.close()" class="btn">取消</button>
        <button @click="crop" class="btn btn-neutral">确定</button>
      </div>
    </div>
  </dialog>
</template>

<style scoped>

</style>
