const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
import ws from '@/services/ws'
import { useUserStore } from '@/stores/user'
import router from '@/router'
import { submitMode } from './match';
function get_token(username) {
    return fetch(`${API_BASE_URL}/token?username=` + username, {
        method: "GET"
    })
}

async function get_and_process_token(username) {
  const response = await get_token(username)
  if (response.status === 200) {
    const json = await response.json().catch(error => {
      console.error("Error while getting token:", error)
      throw new Error("Server unreachable")
    })
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
    try {
        const response = await fetch(`${API_BASE_URL}/token/validate?token=` + token, {
            method: "GET"
        })
        if (response.status === 200) {
            return response.text().then(text => {
                return text
            })
        } else {
            return null
        }
    } catch (error) {
        console.warn("Error while validating token:", error)
        return null
    }
}

export async function logout(token) {
    localStorage.removeItem("username")
    localStorage.removeItem("token")
    const response = await fetch(`${API_BASE_URL}/token/logout?token=` + token, {
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

export async function sendSetupInfo(age, gender, interests) {
    const store = useUserStore()
    const response = await fetch(`${API_BASE_URL}/setup/info`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": store.token,
        },
        body: JSON.stringify({"age": age, "gender": gender, "interests": interests}),
    })
    if (response.status === 200) {
        store.setSetupInfo(age, gender, interests)
        return true
    } else {
        return false
    }
}

export async function tryReSetup(){
    const store = useUserStore()
    if (store.setupInfo) {
        const age = store.setupInfo.age
        const gender = store.setupInfo.gender
        const interests = store.setupInfo.interests
        if (age && gender && interests) {
            const success = await sendSetupInfo(age, gender, interests)
            if (success) {
                await submitMode(store.mode)  // re-submit mode
                return true
            } else {
                return false
            }
        }
    }
    return false
}
export default {
    get_and_process_token,
    validate_token,
    can_reconnect
}