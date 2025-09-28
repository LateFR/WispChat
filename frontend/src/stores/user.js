import { defineStore } from 'pinia'

export const useUserStore = defineStore("user", {
    state: () => ({
        username:null,
        loggedIn:false
    }),
    actions: {
        login(username) {
            this.username = username,
            this.loggedIn = true
        },
        logout() {
            this.username = null
            this.loggedIn = false
        }
    }
})