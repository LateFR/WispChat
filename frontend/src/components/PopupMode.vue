"<!-- whatsapp/frontend/src/components/PopupMode.vue -->

<script setup>
import { ref, defineEmits } from 'vue'
import router from '@/router'
import { submitMode } from '@/services/match'
import { useUserStore } from '@/stores/user'

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

async function handleContinue() {
  if (isValid()) {
    const succes = await submitMode(mode.value)
    if (succes) {
      console.log("Mode submitted:", mode.value)
      emit('validated', { mode: mode.value, interests: interests.value })
    } else {
      console.error("Something went wrong during mode submission.")
      alert("Une erreur est survenue. Veuillez vous reconnecter.")
      store.logout()
      router.push('/login')
    }
  }
}

function isValid() {
  if (mode.value === 'date') {
    return true
  } else if (mode.value === 'chill') {
    return true
  } else if (mode.value === 'interests') {
    return interests.value.length > 0
  }
  return false
}
</script>

<template>
  <!-- Overlay qui couvre tout et centre la popup -->
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-[9999] p-4">
    <!-- La carte de la popup -->
    <div class="bg-base-200 rounded-2xl shadow-xl p-6 w-full max-w-[400px] max-h-[90vh] overflow-y-auto">
      <!-- Titre amélioré : plus grand et plus engageant -->
      <h2 class="text-2xl font-bold text-center mb-6">Comment veux-tu discuter ?</h2>

      <!-- Boutons de sélection de mode -->
      <div class="flex flex-col gap-3 mb-6">
        <button
          class="btn text-left justify-start h-auto py-3"
          :class="{ 'btn-secondary': mode === 'date' }"
          @click="mode = 'date'"
        >
          <div>
            <div class="font-bold">Date</div>
            <div class="text-xs opacity-70 normal-case font-normal">Recherche l'amour ou une connexion sérieuse.</div>
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
          <span v-if="mode === 'date'">Nous te trouverons quelqu'un qui cherche aussi une relation sérieuse. Tu ne sera mis qu'avec des personne du sexe opposé, en priorisant les individus ayant un age proche du tient.</span>
          <span v-else>Nous te mettrons en relation avec quelqu'un pour une conversation détendue. Cette personne est completement aléatoire parmis ceux qui ont activé le mode chill</span>
        </div>
      </div>

      <!-- Bouton de validation -->
      <div class="card-actions justify-end mt-6">
        <button
          type="submit"
          class="btn btn-primary btn-block"
          :disabled="!isValid()"
          @click="handleContinue"
        >
          Trouver un match !
        </button>
      </div>
    </div>
  </div>
</template>"