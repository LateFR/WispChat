import { defineStore } from 'pinia'

export const useUserStore = defineStore("user", {
    state: () => ({
        username:localStorage.getItem("username") || null,
        loggedIn: localStorage.getItem("username") !== null,
        token:localStorage.getItem("token") || null,
        rooms: []
    }),
    actions: {
        login(username, token) {
            this.username = username,
            this.loggedIn = true,
            this.token = token,
            localStorage.setItem("username", username)
            localStorage.setItem("token", token)
        },
        joinRoom(room) {
            if (this.rooms.includes(room)) return
            this.rooms.push(room)
        },
        leaveRoom(room) {
            if (!this.rooms.includes(room)) return
            this.rooms = this.rooms.filter(r => r !== room)
        },
        logout() {
            this.username = null
            this.loggedIn = false
            this.token = null
            this.rooms = []
            localStorage.removeItem("username")
            localStorage.removeItem("token")
        }
    }
})