import Vue from 'vue'
import Vuex, { ModuleTree } from 'vuex'

import auth, { State as AuthState } from './auth'
import oidcClientStorage, { State as OidcClientStorageState } from './storage'
// import { User, UserManager } from 'oidc-client';

Vue.use(Vuex)

// Merge all the types of modules we use
// This is done to provide typing
// Vuex Typescript support bad
interface RootState {
  auth: AuthState;
  oidcClientStorage: OidcClientStorageState;
}

const modules: ModuleTree<RootState> = {
  auth,
  oidcClientStorage
}

const store = new Vuex.Store<RootState>({
  // The fields will be done by Vuex
  state: ({ } as RootState),
  modules
})

export default store
