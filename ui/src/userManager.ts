/* eslint-disable */

import { User as OidcUser, UserManager, WebStorageStateStore } from 'oidc-client';
import { VuexStorage } from './store/storage'
import store from './store'

import { config } from '@/config'
import { fetchRest } from '@/api/rest'

const popupWindowFeatures: { [k: string]: string | number } = {
  status: 'no',
  location: 'no',
  toolbar: 'no',
  menubar: 'no',
  resizable: 'no',
  width: 500,
  height: 620,
  left: (window.screen.width / 2) - (500 / 2),
  top: (window.screen.height / 2) - (600 / 2)
}

const userManager = new UserManager({
  clockSkew: 8 * (60 * 60),
  authority: config.oidcAuthority,
  client_id: 'netsocadmin',
  redirect_uri: `http://${window.location.host}/accounts/login/finish`,
  silent_redirect_uri: `http://${window.location.host}/accounts/login/finish-silent`,
  post_logout_redirect_uri: `http://${window.location.host}/accounts/logout/finish`,
  response_type: 'code',
  scope: 'openid profile email roles',
  revokeAccessTokenOnSignout: true,
  automaticSilentRenew: true,
  filterProtocolClaims: true,
  checkSessionInterval: 2000,
  loadUserInfo: true,

  // Convert features dict into a window features string, i.e location=no,status=no...
  popupWindowFeatures: Object.keys(popupWindowFeatures).reduce(
    (prev: string, cur: string, _: number, __: string[]) => {
      return `${prev},${cur}=${popupWindowFeatures[cur]}`
    }, ''),

  userStore: new WebStorageStateStore({ store: new VuexStorage(store, 'oidcClientStorage') })
})

userManager.events.addUserLoaded((user: OidcUser) => {
  // console.log("User loaded", user)
  store.commit('auth/setUser', { user: user });

  (async () => {
    try {
      let res = await fetchRest(
        `${config.apiBaseUrl}/v1/accounts/${user.profile.preferred_username}/home-directory`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${user.access_token}`
          }
        }, [200, 404]
      )
      
      // Home directory does not exist, we need to create it
      if (res.status == 404) {
        res = await fetchRest(
          `${config.apiBaseUrl}/v1/accounts/${user.profile.preferred_username}/home-directory`, {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${user.access_token}`
            }
          }, [201])
      }
    } catch (e) {
      alert(`Could not ensure home directory created: ${e}. Try refreshing the page`)
    }
  })()
})

userManager.events.addUserUnloaded(() => {
  store.commit('auth/setUser', { user: null })
})

export default userManager;