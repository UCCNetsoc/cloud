<template>
  <v-container fluid class="d-flex mx-1">
    <v-row >
      <v-card class="flex-grow-1 ma-1">
        <v-card-title>About</v-card-title>
        <v-card-subtitle>Learn a little more about us...</v-card-subtitle>
        <v-card-text>
          <p>
            Netsoc Cloud is hosted right here in Cork at <a target="_blank" href="https://www.cloudcix.com/">CloudCIX</a><br/>
            Our primary aim is to provide a non-profit service to help students gain access to server hardware for educational and self-development purposes.
            <br/>
            <br/>
            We would not be able to do this without the help and generosity of:<br/>
            Jerry Sweeney (CEO of CloudCIX),<br/>
            <a target="_blank" href="https://societies.ucc.ie/">The UCC Societies Executive,</a><br/>
            <a target="_blank" href="https://www.ucc.ie/en/it/">UCC IT Services</a><br/>
            <br/>
            Having issues, unexpected errors or want to contribute?<br/>
            <a target="_blank" href="https://github.com/UCCNetsoc/admin">
              Check out our GitHub
            </a>
          </p>
        </v-card-text>
      </v-card>
      <v-card :loading="contributors == null" class="flex-grow-1 ma-1">
        <v-card-title>GitHub Contributors</v-card-title>
        <v-card-subtitle>Everyone who has contributed code changes and reported issues to the Netsoc Cloud project</v-card-subtitle>
        <v-card-text>
          <v-list
          >
            <v-list-item-group>
              <template v-for="(item) in contributors">
                <v-list-item
                  :key="item.login"
                  @click="open(item.html_url)"
                >
                  <v-list-item-avatar>
                    <v-img :src="item.avatar_url"></v-img>
                  </v-list-item-avatar>

                  <v-list-item-content>
                    <v-list-item-title v-html="item.login"></v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
              </template>
            </v-list-item-group>
          </v-list>
        </v-card-text>
      </v-card>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'

interface Contributor {
  login: string;
  avatar_url: string;
  html_url: string;
}

export default Vue.extend({
  name: 'AboutAndContributors',
  components: {},
  methods: {
    open (url: string) {
      window.open(url, '_blank', '')
    }
  },

  mounted: async function () {
    try {
      const contributors = await fetch('https://api.github.com/repos/UCCNetsoc/cloud/contributors')
      this.contributors = await contributors.json()
    } catch {

    }
  },

  data: () => {
    const contributors: Contributor[] = []

    return {
      contributors
    }
  }
})
</script>
