import { ref } from 'vue'
import { useUserStore } from '@/stores/user'

const ws = ref(null)
const myRooms = ref([])
const messages = ref([])
const events = ref([])
let store
// init websocket
function initWebSocket() {
    store = useUserStore()
    const host = window.location.hostname || "localhost"
    ws.value = new WebSocket(`ws://${host}:5000/ws`)
    ws.value.onopen = () => {
        console.log('websocket connected')
    }
    ws.value.onmessage = (event) => {
        const json = JSON.parse(event.data)
        if (json.action == "receive_message") {
            messages.value.push({"from_user": json.from_user, "content": json.content})
        } else if (json.action == "login") {
            console.log("Logged in")
            events.value.push({"login": json.content})
        }

        if (!json.success) {
            console.error(json.error)
            events.value.push({"error": json.error})
        }
    }

    ws.value.onclose = () => {
        console.log("WS closed, reconnecting...")
        setTimeout(reconect, 1000)
    }
}

function reconect() {
    initWebSocket()
    setTimeout(() => {
        login(localStorage.getItem("username"))
        myRooms.value = JSON.parse(localStorage.getItem("rooms"))
    }, 1000)
}
function login(username) {
    sendJSON({"action": "login", "username": username})
    localStorage.setItem("username", username)
}
function joinRoom(room) {
    console.log(room)
    if (myRooms.value.includes(room)) return

    if (ws.value.readyState === WebSocket.OPEN) {
        sendJSON({"action": "join", "room": room})
        myRooms.value.push(room)
        console.log("Connected to " + room)

        localStorage.setItem("rooms", JSON.stringify(myRooms.value))
    } else {
        console.error("Connection to websocket not opened")
    }
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
            from: message.from_user
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
    reconect,
    login,
    joinRoom,
    sendMessage,
    parsedMessages,
    events
}