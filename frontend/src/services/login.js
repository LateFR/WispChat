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
    throw new Error(`Username ${username} already exists`)
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

export default {
    get_and_process_token,
    validate_token
}