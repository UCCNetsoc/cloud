export interface Config {
  apiBaseUrl: string;
  oidcAuthority: string;
  hCaptchaSiteKey: string;
}

// TODO: change defaults to netsoc.co
export const config: Config = {
  apiBaseUrl: process.env.VUE_APP_NETSOC_API_URL.replace(
    new RegExp('[/]+$'),
    ''
  ) ?? 'http://api.netsoc.dev',
  oidcAuthority: process.env.VUE_APP_OIDC_AUTHORITY ?? 'http://keycloak.netsoc.dev/auth/realms/freeipa',
  hCaptchaSiteKey: process.env.NODE_ENV === 'development' ? (process.env.VUE_APP_HCAPTCHA_SITE_KEY ?? '') : '0e8176fb-1fc2-4d51-a153-773cbd8b9837'
}
