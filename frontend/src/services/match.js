import { useUserStore } from '@/stores/user'
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function requestMatch() {
    const store = useUserStore()
    const response = await fetch(`${API_BASE_URL}/matchmaking/join`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": store.token,
        }
    })
    console.log("Requesting match...")
    if (response.status === 200) {
        return true
    } else {
        return false
    }
}