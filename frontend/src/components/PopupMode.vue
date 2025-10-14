<!-- whatsapp/frontend/src/components/PopupMode.vue -->
<script setup>
import { ref, defineEmits, computed } from 'vue'
import router from '@/router'
import { submitMode } from '@/services/match'
import { useUserStore } from '@/stores/user'
import GenericPopup from './GenericPopup.vue'

const availableInterests = [
  { id: 'sport', label: 'Sport' },
  { id: 'culture', label: 'Culture' },
  { id: 'art', label: 'Art' },
  { id: 'science', label: 'Science' },
  { id: 'tech', label: 'Technologie' },
  { id: 'voyages', label: 'Voyages' },
  { id: 'musique', label: 'Musique' },
]
const mode = ref('date') // 'date', 'chill', 'interests'
const interests = ref([])
const store = useUserStore()
const emit = defineEmits(['validated'])
const isVisible = ref(true)

async function handleContinue() {
  if (!isValid.value) return;

  const success = await submitMode(mode.value)
  if (success) {
    console.log("Mode submitted:", mode.value)
    isVisible.value = false // Déclenche l'animation de fermeture
    // On attend la fin de l'animation avant de notifier le parent, pour éviter un "saut" visuel
    setTimeout(() => {
      emit('validated', { mode: mode.value, interests: interests.value })
    }, 300); // Doit correspondre à la durée de la transition CSS de GenericPopup
  } else {
    console.error("Something went wrong during mode submission.")
    alert("Une erreur est survenue. Veuillez vous reconnecter.")
    store.logout()
    router.push('/login')
  }
}

const isValid = computed(() => {
  if (mode.value === 'date' || mode.value === 'chill') {
    return true;
  }
  if (mode.value === 'interests') {
    return interests.value.length > 0;
  }
  return false;
});
</script>

<template>
  <GenericPopup
    v-model="isVisible"
    title="Comment veux-tu discuter ?"
    confirm-text="Valider"
    :show-cancel-button="false"
    :confirm-disabled="!isValid"
    :persistent="true"
    @confirm="handleContinue"
  >
    <template #content>
      <!-- Boutons de sélection de mode -->
      <div class="flex flex-col gap-3 mb-6">
        <button
          class="btn text-left justify-start h-auto py-3"
          :class="{ 'btn-secondary': mode === 'date' }"
          @click="mode = 'date'"
        >
          <div>
            <div class="font-bold">Date</div>
            <div class="text-xs opacity-70 normal-case font-normal">Recherche l'amour ou le flirt.</div>
          </div>
        </button>
        <button
          class="btn text-left justify-start h-auto py-3"
          :class="{ 'btn-primary': mode === 'chill' }"
          @click="mode = 'chill'"
        >
          <div>
            <div class="font-bold">Chill</div>
            <div class="text-xs opacity-70 normal-case font-normal">Pour discuter sans pression et se faire des amis.</div>
          </div>
        </button>
        <!-- <button
          class="btn text-left justify-start h-auto py-3"
          :class="{ 'btn-primary': mode === 'interests' }"
          @click="mode = 'interests'"
        >
          <div>
            <div class="font-bold">Interests</div>
            <div class="text-xs opacity-70 normal-case font-normal">Trouve quelqu'un qui partage tes passions.</div>
          </div>
        </button> -->
      </div>

      <!-- Contenu spécifique au mode sélectionné -->
      <div class="min-h-[150px]">
        <div v-if="mode === 'interests'">
          <label class="label">
            <span class="label-text">Choisis au moins un centre d'intérêt</span>
          </label>
          <div class="grid grid-cols-2 gap-2 p-4 border border-base-300 rounded-lg bg-base-100/50">
            <label v-for="interest in availableInterests" :key="interest.id" class="label cursor-pointer justify-start gap-3">
              <input
                type="checkbox"
                :value="interest.id"
                v-model="interests"
                class="checkbox checkbox-primary"
              />
              <span class="label-text">{{ interest.label }}</span>
            </label>
          </div>
        </div>

        <div v-else class="flex items-center justify-center h-full p-4 text-center text-base-content/70">
          <span v-if="mode === 'date'">Nous te trouverons quelqu'un qui cherche aussi une relation sérieuse. Tu ne seras mis qu'avec des personnes du sexe opposé, en priorisant les individus ayant un âge proche du tien.</span>
          <span v-else>Nous te mettrons en relation avec quelqu'un pour une conversation détendue. Cette personne est complètement aléatoire parmi ceux qui ont activé le mode chill.</span>
        </div>
      </div>
    </template>
  </GenericPopup>
</template>