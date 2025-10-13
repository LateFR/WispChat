<script setup>
    import { ref, nextTick, watch, defineProps } from 'vue'
    import ws  from '@/services/ws'
    import { useUserStore } from '@/stores/user'
    
    const messagesContainer = ref(null)
    const isUserAtBottom = ref(true)
    const hasNewMessage = ref(false)
    const store = useUserStore()

    const props = defineProps({
      opponent: {
        type: Object,
        required: true
      },
    });
    // Surveiller les nouveaux messages
    watch(() => ws.parsedMessages().length, async (newLength, oldLength) => {
        if (newLength > oldLength) {
        // Vérifier si l'utilisateur était déjà en bas avant le nouveau message
        if (isUserAtBottom.value) {
            await nextTick()
            scrollToBottom()
        } else {
            // Afficher l'indicateur de nouveau message
            hasNewMessage.value = true
        }
        }
    })
    // Fonction pour vérifier si l'utilisateur est en bas du scroll
    function checkIfAtBottom() {
        if (messagesContainer.value) {
        const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
        isUserAtBottom.value = Math.abs(scrollHeight - clientHeight - scrollTop) < 10
        
        // Si on est en bas et qu'il y avait un nouveau message, on le masque
        if (isUserAtBottom.value && hasNewMessage.value) {
            hasNewMessage.value = false
        }
        }
    }
    
    // Fonction pour scroller jusqu'en bas
    function scrollToBottom() {
        if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        hasNewMessage.value = false
        }
    }
</script>
<template>

      <!-- Conteneur des messages avec ref et scroll listener -->
      <ul 
        ref="messagesContainer"
        @scroll="checkIfAtBottom"
        class="flex-1 p-4 overflow-y-auto relative"
      >
        <li v-if="ws.parsedMessages().length === 0" class="text-center text-base-content/50">
          No messages yet. Be the first!
        </li>
        
        <li
          v-for="(message, index) in ws.parsedMessages()"
          :key="index"
          class="chat items-end"
          :class="{
            'chat-end': message.from === store.username, 
            'chat-start': message.from !== store.username,
            // Espacement uniquement entre groupes de messages d'utilisateurs différents
            'mt-3': index > 0 && message.from !== ws.parsedMessages()[index - 1].from,
            // Messages consécutifs du même utilisateur sont collés
            'mt-0.5': index > 0 && message.from === ws.parsedMessages()[index - 1].from
          }"
        >
          <!-- Avatar avec visibilité conditionnelle basée sur le message précédent -->
          <div 
            class="chat-image"
          >
              <div v-if="message.from !== store.username" class="avatar rounded-full flex items-center justify-center w-[48px] h-[48px]">
                <svg v-if="index === 0 || message.from !== ws.parsedMessages()[index - 1].from" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="p-1.5 text-base-content/40">
                  <path fill-rule="evenodd" d="M18.685 19.097A9.723 9.723 0 0021.75 12c0-5.385-4.365-9.75-9.75-9.75S2.25 6.615 2.25 12a9.723 9.723 0 003.065 7.097A9.716 9.716 0 0012 21.75a9.716 9.716 0 006.685-2.653zm-12.54-1.285A7.486 7.486 0 0112 15a7.486 7.486 0 015.855 2.812A8.224 8.224 0 0112 20.25a8.224 8.224 0 01-5.855-2.438zM15.75 9a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" clip-rule="evenodd" />
                </svg> 
              </div>
            </div>
          
          <!-- Header avec le nom, affiché seulement pour le premier message d'un groupe -->
          <div 
            class="chat-header text-xs opacity-70 mb-1"
           :class="{
              'text-primary': message.from !== store.username && props.opponent.gender === 'male' || message.from === store.username && store.setupInfo.gender === 'male',
              'text-secondary': message.from !== store.username && props.opponent.gender === 'female' || message.from === store.username && store.setupInfo.gender === 'female',
            }"
            v-if="index === 0 || message.from !== ws.parsedMessages()[index - 1].from"
          >
            {{ message.from }}
          </div>
          
          <!-- Bulle de message -->
          <div 
            class="chat-bubble break-words whitespace-pre-wrap"
            :class="{'chat-bubble-primary': message.from === store.username}"
          >
            {{ message.message }}
          </div>
        </li>
      </ul>

      <!-- Indicateur de nouveau message -->
      <transition name="slide-up">
      <div 
        v-if="hasNewMessage && !isUserAtBottom"
        @click="scrollToBottom"
        class="absolute left-1/2 transform -translate-x-1/2 bg-primary text-primary-content px-3 py-2 rounded-full shadow-lg cursor-pointer hover:bg-primary-focus transition-colors flex items-center gap-2 z-10"
        :style="{ bottom: `calc(4rem + 0.75rem + env(safe-area-inset-bottom))` }"
        role="button"
        aria-label="Aller en bas"
        title="Aller en bas"
      > 
        <!-- SVG flèche vers le bas -->
        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7"/>
        </svg>
      </div>
    </transition>

</template>


<style scoped>
/* Animation pour l'indicateur de nouveau message */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translate(-50%, 20px);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translate(-50%, 20px);
  opacity: 0;
}


</style>