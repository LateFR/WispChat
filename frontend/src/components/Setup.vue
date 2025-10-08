<script setup>
    import { ref, onMounted } from 'vue'
    import { sendSetupInfo, tryReSetup } from '@/services/login'
    import router from '@/router'
    import { useUserStore } from '@/stores/user'

    const age = ref(null)
    const gender = ref(null)
    const interests = ref([])

    async function sendSetupInfoHandler(){
        const succes = await sendSetupInfo(age.value, gender.value, interests.value)
        if (succes) {
            router.push('/')
        } else {
            console.warn("Something went wrong")
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
    <h1> Plus que quelques informations...</h1>
    <div class="flex flex-col gap-4">
        <select v-model="gender">
            <option value="male">Homme</option>
            <option value="female">Femme</option>
        </select>
        <select v-model="age">
            <option value="18">18 ans</option>
            <option value="19">19 ans</option>
            <option value="20">20 ans</option>
            <option value="21">21 ans</option>
            <option value="22">22 ans</option>
            <option value="23">23 ans</option>
            <option value="24">24 ans</option>
            <option value="25">25 ans</option>
            <option value="26">26 ans</option>
            <option value="27">27 ans</option>
            <option value="28">28 ans</option>
            <option value="29">29 ans</option>
            <option value="30">30 ans</option>
        </select>
        <select v-model="interests">
            <option value="sport">Sport</option>
            <option value="culture">Culture</option>
            <option value="art">Art</option>
            <option value="science">Science</option>
            <option value="tech">Technologie</option>
        </select>
        <button @click='sendSetupInfoHandler' v-show='age && gender && interests' class='btn btn-primary btn-square' > Send </button>
    </div>
</template>