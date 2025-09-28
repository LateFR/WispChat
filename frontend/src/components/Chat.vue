<script setup>
  import { ref, onMounted } from 'vue'
  import ws  from '@/services/ws'
  import { useUserStore } from '@/stores/user'
  import router from '@/router'

  const newMessage = ref('')
  const store = useUserStore()

    ws.initWebSocket()  
    onMounted(() => {setTimeout(() => {ws.joinRoom("room1")}, 1000)})
  
</script>

<template>
  <!-- Conteneur principal pour un fond gris clair et un centrage du contenu -->
  <div class="bg-base-200 min-h-screen flex justify-center p-0 sm:p-4">

    <!-- La fenêtre de chat, avec une largeur maximale pour les grands écrans -->
    <div class="flex flex-col h-screen w-full max-w-4xl bg-base-100 shadow-xl">

      <!-- En-tête de la salle de chat -->
      <div class="navbar bg-base-100 border-b border-base-300">
        <div class="flex-1">
          <a class="btn btn-ghost text-xl">Chat Room: room1</a>
        </div>
        <div class="flex-none">
          <span class="text-sm mr-4">Connecté en tant que: <strong>{{ store.username }}</strong></span>
        </div>
      </div>
      
      <!-- Liste des messages qui prend tout l'espace disponible -->
      <ul class="flex-1 p-4 overflow-y-auto space-y-4">
        <!-- Message d'accueil s'il n'y a pas encore de message -->
        <li v-if="ws.parsedMessages().length === 0" class="text-center text-base-content/50">
          Aucun message pour le moment. Soyez le premier !
        </li>
        
        <!-- On boucle sur les messages -->
        <li
          v-for="(message, index) in ws.parsedMessages()"
          :key="index"
          class="chat"
          :class="{
            'chat-end': message.from === store.username, 
            'chat-start': message.from !== store.username
          }"
        >
          <div class="chat-header text-xs opacity-70 mb-1">
            {{ message.from }}
          </div>
          <div 
            class="chat-bubble break-words whitespace-pre-wrap"
            :class="{'chat-bubble-primary': message.from === store.username}"
          >
            {{ message.message }}
          </div>
        </li>
      </ul>

      <!-- Zone de saisie du message, visuellement séparée en bas -->
      <div class="p-4 bg-base-100 border-t border-base-300">
        <form @submit.prevent="ws.sendMessage(newMessage); newMessage = ''" class="flex gap-3">
          <input 
            v-model="newMessage" 
            type="text" 
            placeholder="Écrivez votre message..." 
            class="input input-bordered w-full focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button type="submit" class="btn btn-primary btn-square">
            <!-- Icône SVG pour l'envoi -->
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </form>
      </div>
    </div>

  </div>
</template>