<!-- whatsapp/frontend/src/components/GenericPopup.vue -->
<script setup>
import { defineProps, defineEmits, watch } from 'vue';

// --- Props ---
const props = defineProps({
  // Utilise v-model pour contrôler la visibilité
  modelValue: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
  content: {
    type: String,
    required: true,
  },
  confirmText: {
    type: String,
    default: 'Valider',
  },
  cancelText: {
    type: String,
    default: 'Annuler',
  },
  // Pour masquer le bouton annuler et en faire une simple alerte
  showCancelButton: {
    type: Boolean,
    default: true,
  }
});

// --- Emits ---
// Définit les événements que le composant peut émettre
const emit = defineEmits(['update:modelValue', 'confirm', 'cancel']);

// --- Methods ---
function confirmAction() {
  emit('confirm');
  closePopup();
}

function cancelAction() {
  emit('cancel');
  closePopup();
}

function closePopup() {
  emit('update:modelValue', false);
}

// --- Watchers & Lifecycle ---
// Permet de fermer avec la touche "Echap"
watch(() => props.modelValue, (isVisible) => {
  const onEscape = (e) => {
    if (e.key === 'Escape' && isVisible) {
      cancelAction();
    }
  };
  if (isVisible) {
    document.addEventListener('keydown', onEscape);
  } else {
    document.removeEventListener('keydown', onEscape);
  }
});

</script>

<template>
  <!-- Le composant <transition> de Vue gère les animations d'entrée/sortie -->
  <transition name="popup-fade">
    <!-- 
      L'overlay qui assombrit le fond.
      - `fixed inset-0`: Fait en sorte que ce div prenne 100% de la largeur et de la hauteur de la fenêtre du navigateur.
      - `z-[9999]`: S'assure qu'il est au-dessus de tout le reste.
      - `flex items-center justify-center`: C'EST LA PARTIE IMPORTANTE. Cela transforme le div en conteneur Flexbox
        et centre son enfant direct (la carte de la popup) à la fois verticalement (`items-center`) et horizontalement (`justify-center`).
    -->
    <div
      v-if="modelValue"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] p-4 flex items-center justify-center"
      @click.self="cancelAction"
    >
      <!-- La carte de la popup. Comme c'est l'enfant direct du conteneur flex, elle sera centrée. -->
      <div class="card w-full bg-base-200 shadow-xl max-w-[600px]">
        <div class="card-body">
          <!-- Titre (optionnel) -->
          <h2 v-if="title" class="card-title text-2xl mb-2">{{ title }}</h2>
          
          <!-- Contenu principal -->
          <p class="text-base-content/80">{{ content }}</p>
          
          <!-- Section des boutons -->
          <div class="card-actions justify-end mt-6 space-x-2">
            <button
              v-if="showCancelButton"
              @click="cancelAction"
              class="btn btn-ghost"
            >
              {{ cancelText }}
            </button>
            <button
              @click="confirmAction"
              class="btn btn-primary"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
/* Animation de fondu pour l'overlay et de zoom/fondu pour la popup */
.popup-fade-enter-active, .popup-fade-leave-active {
  transition: opacity 0.3s ease;
}
.popup-fade-enter-active .card, .popup-fade-leave-active .card {
  transition: all 0.3s ease;
}

.popup-fade-enter-from, .popup-fade-leave-to {
  opacity: 0;
}

.popup-fade-enter-from .card, .popup-fade-leave-to .card {
  opacity: 0;
  transform: scale(0.95);
}
</style>