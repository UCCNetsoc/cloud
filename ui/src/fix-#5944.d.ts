/**
 * https://github.com/vuetifyjs/vuetify/issues/5944
 * This occurs with a base project, was an unfixed bug in Vuetify at the time
 *  ERROR in /home/ocanty/nsa3/ui/src/plugins/vuetify.ts(2,21):
 *  Could not find a declaration file for module 'vuetify/lib'. '/home/ocanty/nsa3/ui/node_modules/vuetify/lib/index.js' implicitly has an 'any' type.
 *  Try `npm install @types/vuetify` if it exists or add a new declaration (.d.ts) file containing `declare module 'vuetify/lib';`
 *      1 | import Vue from 'vue'
 *  > 2 | import Vuetify from 'vuetify/lib'
 *      |                     ^
 *      3 | 
 *      4 | Vue.use(Vuetify)
 */
declare module 'vuetify/lib' {
    import 'vuetify/types/lib'
}