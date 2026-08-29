<script setup>
defineProps(['userProfile'])
</script>

<template>
  <div v-if="userProfile" class="flex justify-center mt-12 gap-8">
    <div class="avatar">
      <div class="w-44 rounded-full">
        <img :src="userProfile.photo" alt="">
      </div>
    </div>
    <div class="flex flex-col justify-center w-64 h-44">
      <div class="text-2xl font-bold line-clamp-1 break-all">{{ userProfile.username }}</div>
      <div class="text-sm text-gray-500 mt-2">AIFriends号：{{ userProfile.user_id }}</div>
      <div class="text-sm h-20 mt-4 line-clamp-4 break-all">{{ userProfile.profile }}</div>
    </div>
  </div>
</template>

<style scoped>

</style>
