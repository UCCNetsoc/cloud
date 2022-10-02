import config from "../config";
import { userManager } from "../userManager";

const apiPrefix = config.apiBaseUrl + "/v1";

const request = async (url: string, options: { method?: RequestInit["method"], body?: RequestInit["body"] }, auth = true,): Promise<[number, any, Response]> => {
  const user = await userManager.getUser();
  url = url.replace("$username", user?.profile.preferred_username || "");

  var headers = new Headers({
    "Content-Type": "application/json",
  });

  if (auth) {
    headers.append("Authorization", `Bearer ${user?.access_token}`)
  }

  const req = await fetch(apiPrefix + url, {
    headers,
    ...options
  })

  if (req.status < 200 || req.status >= 300) {
    throw new Error(`Request failed with status ${req.status}\n${req}`)
  }

  // must clone the response, so as to open it as json response 
  // (second element) and as a standalone response (third element)
  return [req.status, await req.clone().json(), req]
}

export default request;
