import { defineStore } from 'pinia'

export const useUserStore = defineStore("user", {
    state: () => ({
        username:localStorage.getItem("username") || null,
        loggedIn: localStorage.getItem("username") !== null,
        token:localStorage.getItem("token") || null,
        rooms: [],
        setupInfo: (() => {
            try {
                return JSON.parse(localStorage.getItem("setupInfo")) || null
            } catch (e) {
                console.warn("Erreur parsing setupInfo:", e)
                return null
            }
        })(),
        interfaceState: "popup" // "popup", "waiting", "animating", "chat"
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
        setSetupInfo(age, gender, interests) {
            const setupInfo = {"age": age, "gender": gender, "interests": interests}
            this.setupInfo = setupInfo
            localStorage.setItem("setupInfo", JSON.stringify(setupInfo))
        },
        logout() {
            this.username = null
            this.loggedIn = false
            this.token = null
            this.rooms = []
            this.setupInfo = null
            localStorage.removeItem("username")
            localStorage.removeItem("token")
            localStorage.removeItem("setupInfo")
        }
    }
})