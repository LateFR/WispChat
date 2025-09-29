<script setup>
  import { ref, onMounted, nextTick } from 'vue'
  import ws  from '@/services/ws'
  import { useUserStore } from '@/stores/user'
  import router from '@/router'
  import { logout } from '@/services/login'
  import Chat from './Chat.vue'
  import Loading from './Loading.vue'
import Chat from './Chat.vue'

  const newMessage = ref('')
  const store = useUserStore()

  ws.initWebSocket()  
  onMounted(() => {
    setTimeout(() => {ws.joinRoom("room1")}, 1000)
  })
  
  
  // Fonction pour envoyer un message
  async function sendMessage() {
    if (newMessage.value.trim()) {
      ws.sendMessage(newMessage.value)
      newMessage.value = ''
    }
  }
  
  function handleLogout() {
    logout(store.token).then(response => {
      if (response) {
        store.logout()
        router.push("/login")
      }
    })
  }
</script>

<template>
  <div class="bg-base-200 min-h-screen flex justify-center p-0 sm-p-4">
    <div class="flex flex-col h-screen w-full max-w-4xl bg-base-100 shadow-xl relative">

      <div class="navbar bg-base-100 border-b border-base-300">
        <div class="flex-1">
          <a class="btn btn-ghost text-xl">Chat room: room1</a>
        </div>
        <div class="flex-none">
          <div class="dropdown dropdown-end">
            <label tabindex="0" class="btn btn-ghost btn-circle avatar">
              <div class="avatar online">
                <div class="w-36 rounded-full">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-full h-full p-1.5 text-base-content/40">
                        <path fill-rule="evenodd" d="M18.685 19.097A9.723 9.723 0 0021.75 12c0-5.385-4.365-9.75-9.75-9.75S2.25 6.615 2.25 12a9.723 9.723 0 003.065 7.097A9.716 9.716 0 0012 21.75a9.716 9.716 0 006.685-2.653zm-12.54-1.285A7.486 7.486 0 0112 15a7.486 7.486 0 015.855 2.812A8.224 8.224 0 0112 20.25a8.224 8.224 0 01-5.855-2.438zM15.75 9a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" clip-rule="evenodd" />
                    </svg>
                </div>
              </div>
            </label>
            <ul tabindex="0" class="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-200 rounded-box w-52">
              <li class="p-2 font-semibold pointer-events-none">
                <span>{{ store.username }}</span>
              </li>
              <li>
                <button @click="handleLogout()" class="flex items-center text-error">
                  Logout
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>
      
      <Chat />
      
      <!-- Zone de saisie -->
      <div class="p-4 bg-base-100 border-t border-base-300">
        <form @submit.prevent="sendMessage" class="flex gap-3">
          <input 
            v-model="newMessage" 
            type="text" 
            placeholder="Tapez votre message..." 
            class="input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button 
            type="submit" 
            class="btn btn-primary btn-square"
            :disabled="!newMessage.trim()"
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
