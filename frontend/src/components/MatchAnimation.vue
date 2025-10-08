<script setup>
import { onMounted } from 'vue';
import { useUserStore } from '@/stores/user';

const props = defineProps({
  opponent: {
    type: Object,
    required: true
  },
});

const emit = defineEmits(['animation-finished']);
const store = useUserStore();

onMounted(() => {
  setTimeout(() => {
    emit('animation-finished');
  }, 2200); // 2.2 secondes. il faut aussi modifier .animate-match-container (gere l'anim de sortie) dans le css
});
</script>

<template>
  <!-- Overlay -->
  <div class="fixed h-[100vh] w-[100vw] inset-0 backdrop-blur-sm flex flex-col justify-center items-center z-50 overflow-hidden">
    
    <div class="animate-match-container text-center">
      <!-- Grid 3 colonnes : avatar gauche / VS / avatar droit -->
      <div class="grid grid-cols-3 items-center w-full max-w-lg p-4 gap-4">
        
        <!-- Avatar utilisateur -->
        <div class="flex flex-col items-center gap-4 justify-self-start animate-pop-in-left">
          <div class="w-28 h-28 rounded-full flex items-center justify-center">
            <div class="w-full h-full rounded-full" :class='[store.setupInfo.gender === "male" ? "bg-primary" : "bg-secondary"]'>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-[48px] h-[48px] p-3 text-primary-content">
                <path fill-rule="evenodd" d="M18.685 19.097A9.723 9.723 0 0021.75 12c0-5.385-4.365-9.75-9.75-9.75S2.25 6.615 2.25 12a9.723 9.723 0 003.065 7.097A9.716 9.716 0 0012 21.75a9.716 9.716 0 006.685-2.653zm-12.54-1.285A7.486 7.486 0 0112 15a7.486 7.486 0 015.855 2.812A8.224 8.224 0 0112 20.25a8.224 8.224 0 01-5.855-2.438zM15.75 9a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" clip-rule="evenodd" />
              </svg>
          </div>
          </div>
          <span class="text-2xl font-bold text-base-content">{{ store.username }}</span>
        </div>

        <!-- VS -->
        <div class="text-center justify-self-center">
          <span class="text-7xl font-black text-secondary-focus animate-vs-pop-in">VS</span>
        </div>

        <!-- Avatar adversaire -->
        <div class="flex flex-col items-center gap-4 justify-self-end animate-pop-in-right">
          <div class="w-28 h-28 rounded-full flex items-center justify-center">
           <div class="w-full h-full rounded-full" :class='[props.opponent.gender === "male" ? "bg-primary" : "bg-secondary"]'>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-[48px] h-[48px] p-3 text-primary-content">
                <path fill-rule="evenodd" d="M18.685 19.097A9.723 9.723 0 0021.75 12c0-5.385-4.365-9.75-9.75-9.75S2.25 6.615 2.25 12a9.723 9.723 0 003.065 7.097A9.716 9.716 0 0012 21.75a9.716 9.716 0 006.685-2.653zm-12.54-1.285A7.486 7.486 0 0112 15a7.486 7.486 0 015.855 2.812A8.224 8.224 0 0112 20.25a8.224 8.224 0 01-5.855-2.438zM15.75 9a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" clip-rule="evenodd" />
              </svg>
          </div>
          </div>
          <span class="text-2xl font-bold text-base-content">{{ props.opponent.username }}</span>
        </div>
      </div>

      <!-- Texte -->
      <h2 class="mt-10 text-5xl font-bold animate-text-glow">Match Found!</h2>
    </div>
  </div>
</template>


<style scoped>
/* AMÉLIORATION DES ANIMATIONS */

/* Animation d'entrée des avatars */
@keyframes pop-in {
  0% { transform: scale(0.5) translateX(var(--translate-x, 0)); opacity: 0; }
  70% { transform: scale(1.1) translateX(0); opacity: 1; }
  100% { transform: scale(1) translateX(0); opacity: 1; }
}

/* Animation d'entrée du "VS" */
@keyframes vs-pop-in {
  0% { transform: scale(0); opacity: 0; }
  80% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}

/* Animation du texte "Match Found!" (utilise les couleurs DaisyUI --p/--s) */
@keyframes text-glow {
  0%, 100% { opacity: 1; text-shadow: 0 0 10px hsl(var(--p)), 0 0 20px hsl(var(--p)); } 
  50% { opacity: 0.8; text-shadow: 0 0 20px hsl(var(--s)), 0 0 30px hsl(var(--s)); }  
}

/* Animation de sortie pour tout le conteneur */
@keyframes slide-out-and-fade {
  to { transform: translateY(-50px); opacity: 0; }
}


/* Application des animations avec des délais */
.animate-pop-in-left {
  --translate-x: -100px;
  animation: pop-in 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}

.animate-pop-in-right {
  --translate-x: 100px;
  animation: pop-in 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}

.animate-vs-pop-in {
  animation: vs-pop-in 0.5s 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}

.animate-text-glow {
  animation: text-glow 2s 0.6s infinite;
}

.animate-match-container {
  animation: slide-out-and-fade 0.4s 1.8s ease-in forwards;
}
</style>