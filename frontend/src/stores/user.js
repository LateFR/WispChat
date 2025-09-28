import { defineStore } from 'pinia'

export const useUserStore = defineStore("user", {
    state: () => ({
        username:localStorage.getItem("username") || null,
        loggedIn: localStorage.getItem("username") !== null,
        token:localStorage.getItem("token") || null
    }),
    actions: {
        login(username, token) {
            this.username = username,
            this.loggedIn = true,
            this.token = token,
            localStorage.setItem("username", username)
            localStorage.setItem("token", token)
        },
        logout() {
            this.username = null
            this.loggedIn = false
        }
    }
})