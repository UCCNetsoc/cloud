import { GetterTree, MutationTree } from 'vuex'
import { User as OidcUser } from 'oidc-client'

type User = OidcUser | null

export interface State {
  user: User;
}

const mutations: MutationTree<State> = {
  setUser (state: State, { user }: { user: User }): void {
    state.user = user
  }
}

const getters: GetterTree<State, any> = {
  user (state: State): User {
    return state.user
  }
}

export default {
  namespaced: true,
  state: {
    user: null
  },
  mutations,
  // actions,
  getters
  // modules
}
