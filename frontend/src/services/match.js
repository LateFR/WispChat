import { useUserStore } from '@/stores/user'


export async function requestMatch() {
    const store = useUserStore()
    const response = await fetch("http://192.168.1.49:5000/matchmaking/join", {
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