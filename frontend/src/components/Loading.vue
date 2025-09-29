<script setup>
const props = defineProps({
  message: { type: String, default: "Loading..." },
  color: { type: String, default: "primary" },
  type: { type: String, default: "dots" }
})

// Tailwind safelist : on ne peut pas générer dynamiquement loading-*, on choisit statiquement
const loaderClass = props.type === 'dots' ? 'loading loading-dots' : 'loading loading-spinner'
const colorClass = props.color === 'primary' ? 'text-primary' : 'text-secondary'
</script>

<template>
  <div class="flex flex-col justify-center items-center h-screen gap-2">
    <span class="loading-lg":class="[loaderClass, colorClass]"></span>
    <div></div>
    <span class="text-lg font-medium">{{ message }}</span>
  </div>
</template>
