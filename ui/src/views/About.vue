<template>
  <v-container fluid class="d-flex mx-1">
    <v-row >
      <v-card class="flex-grow-1 ma-1">
        <v-card-title>
          <v-img
            alt="admin logo"
            class="shrink"
            contain
            src="@/assets/cloud-logo.svg"
            transition="scale-transition"
            width="160"
          />
        </v-card-title>
        <!-- <v-card-subtitle class="mt-0">admin pre-release</v-card-subtitle> -->
        <v-card-text>
          Having issues or unexpected errors?
          <a href="https://github.com/UCCNetsoc/admin">
            Report all problems on our GitHub
          </a>
        </v-card-text>
      </v-card>
      <v-card class="flex-grow-1 ma-1">
        <v-card-title>About</v-card-title>
        <v-card-subtitle>History of Netsoc Admin</v-card-subtitle>
        <v-card-text>
          <p>
            Originally started in 2015.
          </p>
        </v-card-text>
      </v-card>
      <v-card class="ma-1">
        <v-card-title>Contributing</v-card-title>
        <v-card-subtitle></v-card-subtitle>
        <v-card-text>
          <p>Open a Pull Request on our <a href="https://github.com/UCCNetsoc">GitHub</a> or simply have a chat with us in <code>#servers</code> on our <a href="https://discord.netsoc.co">Discord</a></p>
        </v-card-text>
      </v-card>
      <v-card :loading="contributors == null" class="flex-grow-1 ma-1">
        <v-card-title>Contributors</v-card-title>
        <v-card-subtitle></v-card-subtitle>
        <v-card-text>
          <a v-for="contributor in contributors" v-bind:key="contributor.login" :href="contributor.html_url">
            <v-avatar class="ma-1" color="white">
              <img transition="scale-transition" :src="contributor.avatar_url"/>
            </v-avatar>
          </a>
        </v-card-text>
      </v-card>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  name: 'AboutAndContributors',
  components: {},

  mounted: async function () {
    try {
      const contributorsJson = await fetch('https://api.github.com/repos/UCCNetsoc/netsocadmin2/contributors')
      this.contributors = await contributorsJson.json()
      // console.log(this.contributors)
    } catch {

    }
  },

  data: () => ({
    contributors: null
  })
})
</script>
