<script setup>
  import { ref, onMounted, watch } from 'vue'
  import ws  from '@/services/ws'
  import { useUserStore } from '@/stores/user'
  import router from '@/router'
  import { handleLogout,  validate_token } from '@/services/login'
  import Chat from './Chat.vue'
  import Loading from './Loading.vue'
  import { requestMatch, submitMode } from '@/services/match'
  import MatchAnimation from './MatchAnimation.vue'
  import Header from './Header.vue'
  import Popup from './PopupMode.vue'
  import InputChat from './InputChat.vue'
  import GenericPopup from './GenericPopup.vue'
  const store = useUserStore()
  const newMessage = ref('')
  

  function initMatching() {
    validate_token(store.token).then(username => {
      console.log("Token is valid for user:", username)
      if (!username) {
        handleLogout()
      }
    })
    ws.initWebSocket(async () => {
      // Ici on est sûr que le WS est connecté
      if (!await submitMode(store.mode)) { // Submit the selected mode
        handleLogout()
      }
      if (!await requestMatch()) { // If match request fails, it means token is invalid
        handleLogout()
      }
      ws.match.value.matched = "waiting"
      store.modifyKey("interfaceState", "waiting")
    })
  }
  onMounted(() => {
    if (store.interfaceState !== "popup") {
      initMatching()
    }
  })
  
  

  function showChat() {
    ws.match.value.matched = "stable"
    store.modifyKey("interfaceState", "chat")
  }

  watch(() => ws.match.value.matched, (newValue, oldValue) => {
    if (newValue === "matched" && oldValue === "waiting") {
      console.log("Transitioning to animating")
      store.modifyKey("interfaceState", "animating")
    }
    if (newValue === "waiting" && oldValue !== "waiting") {
      newMessage.value = ""
      ws.match.value.opponent = {"username": null, "gender": null}
      ws.leaveRoom(store.rooms[0]) // leave the current room
      ws.match.value.room = null
      store.modifyKey("interfaceState", "waiting")
      setTimeout(async () => {
        if (!await requestMatch()) { // If match request fails, it means token is invalid
          router.push("/login")
        }
      }, 1)
    }
  })

  function handlePopupModeValidation() {
    store.modifyKey("interfaceState", "popup1")
  }

  function handlePopupCongratValidation() {
    store.modifyKey("interfaceState", "waiting")
    initMatching()
  }
  
const popup1Active = ref(store.interfaceState === 'popup1')

  watch(() => store.interfaceState, (newState) => {
    popup1Active.value = newState === 'popup1'
  })
  
  const showLogoutConfirm = ref(false)
</script>

<template>
  <div class="bg-base-200 min-h-screen flex justify-center p-0 sm:p-4">
    
    <div class="flex flex-col h-screen w-full max-w-4xl bg-base-100 shadow-xl relative">
      <Header v-model="showLogoutConfirm"/>

      <Chat v-if="store.interfaceState === 'chat' || store.interfaceState === 'popup'" :opponent="ws.match.value.opponent || {}"/>

      <Loading v-if="store.interfaceState === 'waiting'" message="Waiting for match..." color="primary" type="dots" />
      
      <MatchAnimation 
        v-if="store.interfaceState === 'animating'"
        :opponent="ws.match.value.opponent" 
        @animation-finished="showChat"
        class="absolute inset-0 flex justify-center items-center z-50"
      />
      
      <InputChat v-model="newMessage"/>
    </div>

    <Popup
      v-if="store.interfaceState === 'popup'"
      @validated="handlePopupModeValidation"
    />
    <GenericPopup
      v-model="popup1Active"
      title="Bienvenue 🎉"
      :show-cancel-button="false"
      @confirm="handlePopupCongratValidation"
    >
      <template #content>
        <p>Bienvenue sur <strong>eavy.chat</strong> !</p>
        <p>En validant cette popup, vous serez mis en relation avec une personne aléatoire.</p>
        <p>⚠️ Soyez respectueux et ne partagez pas d’informations sensibles.</p>
        <p>Si vous rafraîchissez la page ou demandez un nouveau match, vous perdrez l’actuel.</p>
        <p>Faites attention, certains individus peuvent être mal intentionnés 🙂</p>
        <p>Enjoy ! Codé avec amour ❤️</p>
      </template>
    </GenericPopup>

    <!-- On place la popup ici. -->
    <GenericPopup
        v-model="showLogoutConfirm"
        title="Confirmation"
        content="Êtes-vous sûr de vouloir vous déconnecter ?"
        confirm-text="Déconnexion"
        @confirm="handleLogout"
    />
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