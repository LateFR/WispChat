<script setup>
    import { useUserStore } from '@/stores/user';
    import { ref, onMounted } from 'vue'
    import login from '@/services/login'
    import router from '@/router';
    import ws from '@/services/ws'
    import VueHcaptcha from '@hcaptcha/vue3-hcaptcha';

    const ready = ref(false)
    const store = useUserStore()
    const username = ref("")
    const login_error = ref("")

    const hcaptchaEnabled = import.meta.env.VITE_HCAPTCHA_ENABLED
    
    const hcaptchaSiteKey = import.meta.env.VITE_HCAPTCHA_SITE_KEY || ""
    const hcaptchaToken = ref(null)

    const usernamePattern = /^[a-zA-Z0-9_-]+$/;

    function validateInput(event) {
        const value = event.target.value
        if (!usernamePattern.test(value)) {
            event.target.value = value.replace(/[^a-zA-Z0-9_-]/g, '')
            username.value = event.target.value
            login_error.value = "N'utilisez que des lettres, des chiffres, des tirets et des underscores."
        } else {
            login_error.value = ""
        }
    }


    store.modifyKey("interfaceState", "popup") // forcer le mode popup
    onMounted(async () => {
        const isReconnectable = await login.can_reconnect()
        if (isReconnectable) {
            ws.reconnect()
            router.push("/setup") // redirige après reconnexion
        } else {
            ready.value = true
        }
    })

   
    function handleLogin() {
        login_error.value = ""

        try {
            if (!username.value)
                throw new Error("Veuillez entrer un nom d'utilisateur.")

            if (!usernamePattern.test(username.value))
                throw new Error("Le nom d'utilisateur contient des caractères non autorisés (lettres, chiffres, _ et - seulement).")

            login.get_and_process_token(username.value, hcaptchaToken.value)
                .then(token => {
                    if (!token) return
                    store.login(username.value, token)
                    username.value = ""
                    console.log("Logged in")
                    router.push("/setup")
                })
                .catch(error => {
                    login_error.value = error.message
                })
        } catch (error) {
            login_error.value = error.message
        }
    }


    function onVerifyHcaptcha(token) {
        hcaptchaToken.value = token
    }
    function onChallegeExpired() {
        hcaptchaToken.value = null
        console.log("hCaptcha expired")
        alert("Vous avez mis trop de temps de temps à valider le captcha. Veuillez réessayer.")
        router.push("/login")
    }

    function onErrorHcaptcha(error) {
        console.error("hCaptcha error:", error)
        alert("Une erreur est survenue lors de la résolution du captcha. Veuillez réessayer.")
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
                            :maxlength="16"
                            @input="validateInput"
                        />
                    </div>
                    

                    <vue-hcaptcha v-if="hcaptchaEnabled" theme="dark" :sitekey="hcaptchaSiteKey" @verify="onVerifyHcaptcha" @error="onErrorHcaptcha" @expired="onChallegeExpired"></vue-hcaptcha>

                    <!-- Le bouton de connexion prend toute la largeur -->
                    <button type="submit" :disabled="(!hcaptchaToken || !hcaptchaEnabled) || !username.length > 0" class="btn btn-primary w-full">
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