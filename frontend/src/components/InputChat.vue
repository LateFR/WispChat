<script setup>
  import { nextTick, ref, watch } from 'vue'
  import ws  from '@/services/ws'

  const props = defineProps({
    modelValue: String,
  })
  const emit = defineEmits(['update:modelValue'])

  const newMessage = ref('')
  const messageInput = ref(null)

  // local sync
  watch(() => props.modelValue, (val) => {
    newMessage.value = val
  })

  async function sendMessage() {
    if (newMessage.value.trim()) {
      ws.sendMessage(newMessage.value)
      newMessage.value = ''
      emit('update:modelValue', '')
      await nextTick()
      messageInput.value.focus()  // on refocus le champ de saisie
    }
  }
</script>

<template>
    <div class="p-4 bg-base-100 border-t border-base-300">
        <form @submit.prevent="sendMessage" class="flex gap-3">
        <input 
          ref="messageInput"
          v-model="newMessage" 
          type="text" 
          placeholder="Tapez votre message..." 
          class="input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary"
          :disabled="ws.match.value.matched !== 'stable'"
          enterkeyhint="send"                    
          autocomplete="off"
        />
        <button 
          type="submit"
          class="btn btn-primary btn-square"
          :disabled="!newMessage.trim() || ws.match.value.matched !== 'stable'"
        >
          <img src="@/assets/send-button.png" alt="send" class="w-6 h-6">
        </button>
      </form>
    </div>
</template>