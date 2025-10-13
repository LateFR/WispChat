<script setup>
import { ref, onMounted, computed } from 'vue'
import { sendSetupInfo, tryReSetup } from '@/services/login'
import router from '@/router'

// --- State ---
const gender = ref(null)
const age = ref(null)
const interests = ref(["nothing"])

// --- Options dynamiques ---

// Pour l'âge : on génère un tableau de 18 à 99
const ageOptions = []
for (let i = 18; i <= 99; i++) {
  ageOptions.push(i)
}

// Pour les centres d'intérêt, c'est plus propre de les définir ici
const availableInterests = [
  { id: 'sport', label: 'Sport' },
  { id: 'culture', label: 'Culture' },
  { id: 'art', label: 'Art' },
  { id: 'science', label: 'Science' },
  { id: 'tech', label: 'Technologie' },
  { id: 'voyages', label: 'Voyages' },
  { id: 'musique', label: 'Musique' },
]

// --- Logique ---

// Une propriété "computed" pour valider le formulaire, c'est plus propre qu'un v-show
const isFormValid = computed(() => {
  return gender.value && age.value && interests.value.length > 0
})

async function sendSetupInfoHandler() {
  if (!isFormValid.value) return // Sécurité supplémentaire

  const success = await sendSetupInfo(age.value, gender.value, interests.value)
  if (success) {
    router.push('/')
  } else {
    // On pourrait afficher une alerte à l'utilisateur ici
    console.warn("Something went wrong during setup info submission.")
    alert("Une erreur est survenue. Veuillez vous reconnecter.")
    router.push('/login')
  }
}

onMounted(async () => {
  const success = await tryReSetup()
  if (success) {
    router.push('/')
  }
})
</script>

<template>
  <!-- Conteneur principal pour centrer le contenu sur la page -->
  <div class="min-h-screen bg-base-200 flex items-center justify-center p-4">

    <!-- On utilise une "card" de DaisyUI pour un look soigné -->
    <div class="card w-full max-w-[500px] bg-base-100 shadow-xl">
      <div class="card-body">
        <h1 class="card-title text-3xl justify-center mb-6">
          Plus que quelques informations...
        </h1>

        <!-- On utilise un vrai formulaire pour la sémantique et l'accessibilité -->
        <form @submit.prevent="sendSetupInfoHandler" class="space-y-4">

          <!-- Champ Genre -->
          <div class="form-control w-full">
            <label class="label">
              <span class="label-text">Vous êtes ?</span>
            </label>
            <select v-model="gender" class="select select-bordered" required>
              <option :value="null" disabled selected>Choisissez une option</option>
              <option value="male">Un homme</option>
              <option value="female">Une femme</option>
            </select>
          </div>

          <!-- Champ Âge (généré dynamiquement) -->
          <div class="form-control w-full">
            <label class="label">
              <span class="label-text">Quel est votre âge ?</span>
            </label>
            <select v-model="age" class="select select-bordered" required>
              <option :value="null" disabled selected>Sélectionnez votre âge</option>
              <option v-for="ageValue in ageOptions" :key="ageValue" :value="ageValue">
                {{ ageValue }} ans
              </option>
            </select>
          </div>

          <!-- Comming soon -->
          <!-- <div class="form-control w-full">
            <label class="label">
              <span class="label-text">Vos centres d'intérêt (plusieurs choix possibles)</span>
            </label>
            <div class="grid grid-cols-2 gap-2 p-4 border border-base-300 rounded-lg">
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
          </div> -->


          <!-- Bouton de soumission -->
          <div class="card-actions justify-end mt-8">
            <button
              type="submit"
              class="btn btn-primary btn-block"
              :disabled="!isFormValid"
            >
              Continuer
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>