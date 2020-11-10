<template>
  <v-container fill-height fluid>
    <v-row v-if="!visible" class="justify-center text-center text-no-wrap">
      <v-col cols="12" sm="12">
        <!-- <p style="color: yellow; font-size: 24px">warning message</p> -->
      </v-col>
    </v-row>
    <v-row v-if="!visible" class="mt-12 justify-center text-center text-no-wrap">
      <v-col cols="12" sm="12">
        <v-img style="height: min(24rem, 35vh)" :src="require('@/assets/netsoc-logo.svg')" contain></v-img>
      </v-col>
    </v-row>
    <v-row v-if="!visible" class="justify-center text-center">
      <v-col cols="12" sm="12">
        <h2 class="font-weight-light display-5" style="position: relative; z-index: 2">
          New to UCC Netsoc or Linux? Try out our <router-link to='/tutorial'>Tutorial</router-link> to get started<br/>
          Need help? Check out <code>#servers</code> on our <a target="_blank" href="https://discord.netsoc.co">Discord</a><br/>
          Already experienced? View our <a target="_blank" href="https://github.com/UCCNetsoc">GitHub</a>!
        </h2>
      </v-col>
    </v-row>
    <v-row v-if="!visible" class="justify-center ma-0 pa-0" fill-height style="width: 100%">
      <v-col v-for="item in menu" cols="12" xl="1" md="2" sm="2" xs="12" class="ma-2 pa-0" v-bind:key="item.name" @click="$router.push(item.route, ()=>{})">
        <v-card class="text-center service" flat>
          <v-card-text class="justify-center" style="padding-left: 0; padding-right: 0">
            <v-icon class="align-center" size="48">{{ item.icon }}</v-icon>
          </v-card-text>
          <v-card-title style="padding-left: 0; padding-right: 0" class="justify-center subtitle-1">
            <p class="nowrap">{{ item.name }}</p>
          </v-card-title>
        </v-card>
      </v-col>
    </v-row>
    <landing-dialog :visible="visible"/>
  </v-container>
</template>

<style scoped>
.service {
  top: 0;
  transition: 0.4s all;
  cursor: pointer;
  background-color: rgba(0,0,0,0);
  width: 100%;
}

.service:hover {
  top: -24px;
}
.nowrap {
  white-space: nowrap;
}

</style>

<script lang="ts">
import Vue from 'vue'
import LandingDialog from '@/components/LandingDialog.vue'

export default Vue.extend({
  name: 'Landing',
  components: {
    LandingDialog
  },

  computed: {
    visible (): boolean {
      return this.$store.state.auth.user === null
    }
  },

  data: () => ({
    selectedMenu: 0,
    menu: [
      { icon: 'mdi-information', name: 'About', route: '/about' },
      { icon: 'mdi-account-circle', name: 'Account', route: '/account' },
      { icon: 'mdi-cloud', name: 'Cloud', route: '/cloud' },
      // { icon: 'mdi-console-line', name: 'Terminal', route: '/terminal' },
      { icon: 'mdi-lifebuoy', name: 'Tutorial', route: '/tutorial' },
      { icon: 'mdi-book', name: 'Wiki', route: '/wiki' }
    ]
  })

})
</script>
