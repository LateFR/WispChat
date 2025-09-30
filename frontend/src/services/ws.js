import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import router from '@/router'
import { validate_token } from '@/services/login'

const ws = ref(null)
const myRooms = ref([])
const messages = ref([])
const events = ref([])
const match = ref({"matched": "waiting", "user": null})  // "waiting", "matched", "animating",  "stable"

let store

// init websocket
function initWebSocket(onOpenCallback=null) {
    store = useUserStore()
    const host = window.location.hostname || "localhost"
    
    validate_token(store.token).then(username => {
        if (!username) {
            console.error("Token not valid")
            if (router.currentRoute.value.path !== "/login") {
                router.push("/login")
            }
            return
        }
        try {
            ws.value = new WebSocket(`ws://${host}:5000/ws?token=${store.token}`)
        } catch (error) {
            console.error(error)
            events.value.push({"error": error.message})
            router.push("/login")
        }
        ws.value.onopen = () => {
            console.log('websocket connected')
            if (onOpenCallback) onOpenCallback()
        }
        ws.value.onmessage = (event) => {
            const json = JSON.parse(event.data)
            if (json.action == "receive_message") {
                messages.value.push({"from_user": json.from_user, "content": json.content})
            } else if (json.action == "login") {
                console.log("Logged in")
                events.value.push({"login": json.content})
            } else if (json.action == "matched") {
                whenMatched(json.content.room, json.content.username)
            } else if (json.action == "user_left") {
                console.log(`${json.content.username} left the room`)
                match.value.matched = "waiting"
            }

            if (json.success===false && json.error) {
                console.error(json.error)
                events.value.push({"error": json.error})
            }
        }

        ws.value.onclose = (event) => {
            console.log("WS closed, reconnecting...")
            setTimeout(reconnect, 1000)
        }
    })
}

function reconnect() {
    const token = localStorage.getItem("token")
    const username = localStorage.getItem("username")
    store = useUserStore()
    if (!store.loggedIn){ console.log("Logged out, do not reconnect"); return}
    if (token && username) {
        store.login(username, token)
        initWebSocket()
        setTimeout(() => {
            myRooms.value = JSON.parse(localStorage.getItem("rooms"))
        }, 1000)
        for (const room of store.rooms) {
            joinRoom(room)
        }
        console.log("Reconnected")
    } else {
        console.error("Token or username not found in localStorage")
        router.push("/login")
    }
}
function joinRoom(room) {
    if (myRooms.value.includes(room)) return

    if (ws.value.readyState === WebSocket.OPEN) {
        sendJSON({"action": "join", "room": room})
        myRooms.value.push(room)
        console.log("Connected to " + room)
        store.joinRoom(room)
        localStorage.setItem("rooms", JSON.stringify(myRooms.value))
    } else {
        console.error("Connection to websocket not opened")
    }
}

function leaveRoom(room) {
    if (!myRooms.value.includes(room)) return

    if (ws.value.readyState === WebSocket.OPEN) {
        sendJSON({"action": "leave_room", "room": room})
        myRooms.value = myRooms.value.filter(r => r !== room)
        console.log("Left " + room)
        store.leaveRoom(room)
        localStorage.setItem("rooms", JSON.stringify(myRooms.value))
        messages.value = []
    } else {
        console.error("Connection to websocket not opened")
    }
}
function whenMatched(room, username) {
    joinRoom(room)
    match.value = {"matched": "matched", "user": username}
}

function sendMessage(message) {
    if (myRooms.value.length === 0){
        joinRoom("room1")
    }
    if (!message){
        return
    }
    if (ws.value.readyState === WebSocket.OPEN) {
        sendJSON({"action": "send", "room": myRooms.value[0], "message": message})
    } else {
        console.error("Connection to websocket not opened")
    }
}

function parsedMessages() {
    return messages.value.map(message => {
        return {
            message: message.content,
            from: message.from_user,
            room: message.from_room
        }
    })
}

function sendJSON(payload) {
  if (ws.value.readyState === WebSocket.OPEN) {
    ws.value.send(JSON.stringify(payload))
  } else {
    console.error("Connection to websocket not opened")
  }
}

export default {
    initWebSocket,
    reconnect,
    joinRoom,
    sendMessage,
    parsedMessages,
    whenMatched,
    leaveRoom,
    events,
    match,
    messages
}