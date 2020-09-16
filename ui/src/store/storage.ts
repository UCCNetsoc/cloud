/* eslint-disable */

import { GetterTree, ActionTree, MutationTree, Store, ActionContext } from 'vuex'

/**
 * This is a Vuex module that implements a Vuex module and a Storage interface implementation
 * https://developer.mozilla.org/en-US/docs/Web/API/Storage
 *
 * Use case:
 * oidc-client supports custom storage backends that implement the Storage interface as
 * localStorage/sessionStorage. We want to store that info in Vuex instead
 */

export interface State {
  storage: { [key: string]: string};
}

const mutations: MutationTree<State> = {
  setItem (state: State, { key, value }: { key: string; value: string }): void {
    // console.log("setItem", key, value)
    state.storage[key] = value
  },

  removeItem (state: State, { key }: {key: string}) {
    // console.log("removeItem", key)
    delete state.storage[key]
  },

  clear (state: State) {
    // console.log("clear")
    state.storage = { }
  }
}

const actions: ActionTree<State, any> = {
  setItem (store: ActionContext<State, any>, payload: { key: string; value: string }) {
    // console.log("commit setItem", payload)
    store.commit('setItem', payload)
  },

  removeItem (store: ActionContext<State, any>, payload: { key: string }) {
    // console.log("commit removeItem", payload)
    store.commit('removeItem', payload)
  },

  clear (store: ActionContext<State, any>) {
    // console.log("clear")
    store.commit('clear')
  }
}

const getters: GetterTree<State, any> = {
  storage (state: State) {
    return state.storage
  }
}

export default {
  namespaced: true,
  state: {
    storage: { }
  },
  mutations,
  actions,
  getters
}

export class VuexStorage {
  private store: Store<any>
  private namespace = ''

  /**
   *
   * @param store The Vuex store you want oidc-client data to be stored in
   * @param namespace The Vuex module namespace you want us to register our module in
   */
  constructor (store: any, namespace = '') {
    this.store = store
    this.namespace = namespace
  }

  get length (): number {
    // console.log("length")
    const storage = this.store.getters[this.namespace + '/storage']
    return Object.keys(storage).length
  }

  key (n: number): string {
    // console.log(`key ${n}`)
    const storage = this.store.getters[this.namespace + '/storage']
    return Object.keys(storage)[n]
  }

  getItem (key: string): string | null {
    // console.log("getItem", key)
    const storage = this.store.getters[this.namespace + '/storage']

    if (key in storage) {
      return storage[key]
    }

    return null
  }

  setItem (key: string, value: any): void {
    // console.log("setItem", key, value)
    this.store.dispatch(this.namespace + '/setItem', { key, value })
    
  }

  removeItem (key: string) {
    // console.log("removeItem", key)
    this.store.dispatch(this.namespace + '/removeItem', { key })
  }

  clear () {
    // console.log("clear")
    this.store.dispatch(this.namespace + '/clear')
  }
}
