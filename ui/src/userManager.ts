import { UserManager, WebStorageStateStore } from "oidc-client-ts";
import config from './config';

const locSplit: string[] = window.location.href.split("/")

export const userManager = new UserManager({
  authority: config.oidcAuthority,
  client_id: 'netsoc-cloud',
  response_type: 'code',
  redirect_uri: `${locSplit[0]}//${locSplit[2]}/callback`,

  silent_redirect_uri: `${locSplit[0]}//${locSplit[2]}/login/silent`,
  post_logout_redirect_uri: `${locSplit[0]}//${locSplit[2]}/callback/silent`,
  scope: 'openid profile email roles',
  revokeTokensOnSignout: true,
  automaticSilentRenew: true,
  filterProtocolClaims: true,
  checkSessionIntervalInSeconds: 2000,
  loadUserInfo: true,
  userStore: new WebStorageStateStore({ store: window.localStorage }),
});

