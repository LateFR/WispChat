<script setup>
    import { useUserStore } from '@/stores/user';
    import { ref, computed, watch } from 'vue'
    import  ws from '@/services/ws'
    import router from '@/router';
    const store = useUserStore()
    const username = ref("")
    function login() {
        ws.login(username.value)
        store.login(username.value)
        username.value = ""
    }
    watch(() => ws.events.value.length, 
        (newLen) => {
            const event = ws.events.value[ws.events.value.length - 1]
            if (event && event.login) {
                router.push("/")
            }
        }
    )
    const loginError = computed(() => {
        if (!ws.events.value || ws.events.value.length === 0) return null
        const firstEvent = ws.events.value[ws.events.value.length - 1]
        if (firstEvent && firstEvent.error) return firstEvent.error
        return null
    })
</script>
<template>
    <!-- Conteneur principal qui centre la carte verticalement et horizontalement sur toute la page -->
    <div class="min-h-screen bg-base-200 flex items-center justify-center p-4">

        <!-- La carte de connexion -->
        <div class="card w-full max-w-sm bg-base-100 shadow-xl">
            <div class="card-body">
                
                <!-- Titre de la carte -->
                <h2 class="card-title justify-center text-2xl font-bold mb-6">
                    Bienvenue !
                </h2>

                <!-- Le formulaire -->
                <form @submit.prevent="login()" class="space-y-4">
                    
                    <!-- Le conteneur pour le champ de saisie, géré par DaisyUI -->
                    <div class="form-control">
                        <label class="label">
                            <span class="label-text">Nom d'utilisateur</span>
                        </label>
                        <input 
                            v-model="username" 
                            type="text" 
                            placeholder="Entrez votre pseudo..." 
                            class="input input-bordered w-full" 
                        />
                    </div>
                    
                    <!-- Le bouton de connexion prend toute la largeur -->
                    <button type="submit" class="btn btn-primary w-full">
                        Se connecter
                    </button>
                </form>

                <!-- Affichage de l'erreur, stylisé et centré -->
                <p v-if="loginError" class="text-error text-center text-sm mt-4">
                    {{ loginError }}
                </p>

            </div>
        </div>

    </div>
</template>