<script setup>
  import { ref, onMounted, watch } from 'vue'
  import ws  from '@/services/ws'
  import { useUserStore } from '@/stores/user'
  import router from '@/router'
  import { handleLogout,  validate_token } from '@/services/login'
  import Chat from './Chat.vue'
  import Loading from './Loading.vue'
  import { requestMatch } from '@/services/match'
  import MatchAnimation from './MatchAnimation.vue'
  import Header from './Header.vue'
  import Popup from './PopupMode.vue'

  const newMessage = ref('')
  const store = useUserStore()
  console.log("Current interface state:", store.interfaceState)

  function initMatching() {
    validate_token(store.token).then(username => {
      console.log("Token is valid for user:", username)
      if (!username) {
        handleLogout()
      }
    })
    ws.initWebSocket(async () => {
      // Ici on est sûr que le WS est connecté
      if (!await requestMatch()) { // If match request fails, it means token is invalid
        handleLogout()
      }
      ws.match.value.matched = "waiting"
      store.interfaceState = "waiting"
    })
  }
  onMounted(() => {
    if (store.interfaceState !== "popup") {
      initMatching()
    }
  })
  
  
  // Fonction pour envoyer un message
  async function sendMessage() {
    if (newMessage.value.trim()) {
      ws.sendMessage(newMessage.value)
      newMessage.value = ''
    }
  }
  

  function showChat() {
    ws.match.value.matched = "stable"
    store.interfaceState = "chat"
  }

  watch(() => ws.match.value.matched, (newValue, oldValue) => {
    if (newValue === "matched" && oldValue === "waiting") {
      console.log("Transitioning to animating")
      store.interfaceState = "animating"
    }
    if (newValue === "waiting" && oldValue !== "waiting") {
      newMessage.value = ""
      ws.match.value.opponent = {"username": null, "gender": null}
      ws.leaveRoom(store.rooms[0]) // leave the current room
      ws.match.value.room = null
      setTimeout(async () => {
        if (!await requestMatch()) { // If match request fails, it means token is invalid
          router.push("/login")
        }
      }, 1)
    }
  })

  function handlePopupModeValidation() {
    store.interfaceState = "waiting"
    initMatching()
  }
</script>

<template>
  <div class="bg-base-200 min-h-screen flex justify-center p-0 sm-p-4">
    <!-- Le conteneur `relative` est important pour que MatchAnimation puisse se positionner par-dessus -->
    <div class="flex flex-col h-screen w-full max-w-4xl bg-base-100 shadow-xl relative">
      <Header />

      <!-- Affichage du Chat ou du Loading. Le Chat reste affiché pendant l'animation. -->
      <Chat v-if="store.interfaceState === 'chat' || store.interfaceState === 'popup'" />
      <Loading v-if="store.interfaceState === 'waiting'" message="Waiting for match..." color="primary" type="dots" />
      
      <!-- L'animation en tant que véritable overlay (positionné par-dessus le chat) -->
      <MatchAnimation 
        v-if="store.interfaceState === 'animating'"
        :opponent="ws.match.value.opponent" 
        @animation-finished="showChat"
        class="absolute inset-0 flex justify-center items-center z-50"
      />
      
      <Popup
        v-if="store.interfaceState === 'popup'"
        @validated="handlePopupModeValidation"
      />
      <!-- Zone de saisie -->
      <div class="p-4 bg-base-100 border-t border-base-300">
        <form @submit.prevent="sendMessage" class="flex gap-3">
          <input 
            v-model="newMessage" 
            type="text" 
            placeholder="Tapez votre message..." 
            class="input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary"
            :disabled="ws.match.value.matched !== 'stable'"
          />
          <button 
            type="submit" 
            class="btn btn-primary btn-square"
            :disabled="!newMessage.trim() || ws.match.value.matched !== 'stable'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Animation pour la popup de mode */
@keyframes bounce-in {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  70% {
    transform: scale(1.05);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes bounce-out-up {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  30% {
    transform: scale(0.95);
    opacity: 1;
  }
  100% {
    transform: scale(0.9) translateY(-100px);
    opacity: 0;
  }
}

.popup-bounce-enter-active {
  animation: bounce-in 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.popup-bounce-leave-active {
  animation: bounce-out-up 0.4s ease-in-out forwards;
}
</style>