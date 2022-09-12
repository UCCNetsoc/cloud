import { userManager } from "../userManager";

const apiPrefix = "http://localhost:8000/v1";

const request = async (url: string, options: { method?: RequestInit["method"], body?: RequestInit["body"] }): Promise<[number, any]> => {
  const user = await userManager.getUser();
  url = url.replace("$username", user?.profile.preferred_username || "");

  console.log(url)

  const headers = new Headers({
    "Content-Type": "application/json",
    "Authorization": `Bearer ${user?.access_token}`
  })

  const req = await fetch(apiPrefix + url, {
    credentials: 'include',
    headers,
    ...options
  })
  
  if (req.status < 200 || req.status >= 300) {
    throw new Error(`Request failed with status ${req.status}\n${req}`)
  }
  return [req.status, req.json()]
}

export default request;
