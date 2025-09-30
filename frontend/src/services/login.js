import ws from '@/services/ws'
import { useUserStore } from '@/stores/user'
import router from '@/router'

function get_token(username) {
    return fetch(`http://192.168.1.49:5000/token?username=` + username, {
        method: "GET"
    })
}

async function get_and_process_token(username) {
  const response = await get_token(username)
  if (response.status === 200) {
    const json = await response.json()
    const token = json.token
    localStorage.setItem("token", token)

    const validatedUsername = await validate_token(token)
    if (validatedUsername) {
      localStorage.setItem("username", validatedUsername)
    }

    return token
  } else if (response.status === 403) {
    throw new Error(`Username ${username} already taken`)
  } else {
    const text = await response.text()
    throw new Error("Failed to get token: " + text)
  }
}


export async function validate_token(token) {
    const response = await fetch("http://192.168.1.49:5000/token/validate?token=" + token, {
        method: "GET"
    })
    if (response.status === 200) {
        return response.text().then(text => {
            return text
        })
    } else {
        return null
    }
}

export async function logout(token) {
    localStorage.removeItem("username")
    localStorage.removeItem("token")
    const response = await fetch("http://192.168.1.49:5000/token/logout?token=" + token, {
        method: "GET"
    })
    if (response.status === 200) {
        return response.text().then(text => {
            return text
        })
    } else {
        return null
    }
}

async function can_reconnect() {
    const token = localStorage.getItem("token")
    if (token) {
        const username = await validate_token(token)
        if (username) {
            localStorage.setItem("username", username)
            return true
        } else {
            return false
        }
    } else {
        return false
    }
}

export function handleLogout() {
    const store = useUserStore()
    logout(store.token).then(response => {
      if (response) {
        store.logout()
        ws.messages.value = []
        router.push("/login")
      }
    })
  }

export default {
    get_and_process_token,
    validate_token,
    can_reconnect
}