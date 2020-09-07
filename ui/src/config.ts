
export interface Config {
  apiBaseUrl: string;
  oidcAuthority: string;
}

export const config: Config = {
  apiBaseUrl: process.env.VUE_APP_NETSOC_API_URL.replace(new RegExp('[/]+$'), ''),
  oidcAuthority: process.env.VUE_APP_OIDC_AUTHORITY
}
