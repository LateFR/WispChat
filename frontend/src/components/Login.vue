<script setup>
    import { useUserStore } from '@/stores/user';
    import { ref, onMounted } from 'vue'
    import login from '@/services/login'
    import router from '@/router';
    import ws from '@/services/ws'

    const ready = ref(false)
    const store = useUserStore()
    const username = ref("")
    const login_error = ref("")

    onMounted(async () => {
        const isReconnectable = await login.can_reconnect()
        if (isReconnectable) {
            ws.reconnect()
            router.push("/") // redirige après reconnexion
        } else {
            ready.value = true
        }
    })

   
    function handleLogin() {
        if (!username.value) return
        login.get_and_process_token(username.value).then(token => {
            if (!token) return
            store.login(username.value, token)
            username.value = ""
            console.log("Logged in")
            router.push("/")
        }).catch (error => {
            login_error.value = error.message
            return
        })
    }
</script>
<template>
    <!-- Conteneur principal qui centre la carte verticalement et horizontalement sur toute la page -->
    <div v-if="ready" class="min-h-screen bg-base-200 flex items-center justify-center p-4">

        <!-- La carte de connexion -->
        <div class="card w-full max-w-[500px] bg-base-100 shadow-xl">
            <div class="card-body">
                
                <!-- Titre de la carte -->
                <h2 class="card-title justify-center text-2xl font-bold mb-6">
                    Bienvenue !
                </h2>

                <!-- Le formulaire -->
                <form @submit.prevent="handleLogin()" class="space-y-4">
                    
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
                <p v-if="login_error" class="text-error text-center text-sm mt-4">
                    {{ login_error }}
                </p>

            </div>
        </div>

    </div>
</template>