<template>
  <v-container fluid class="d-flex justify-space-around">
    <v-row class="ma-0">
      <v-card class="flex-grow-1 ma-1">
        <v-card-title>
            <h1 class="font-weight-bold">Hi ocanty!</h1>
        </v-card-title>
        <v-card-subtitle class="mt-0">netsocadmin3 pre-release</v-card-subtitle>
        <v-card-text>
          Having issues or unexpected errors?
          <a href="https://github.com/UCCNetsoc/netsocadmin2">
            Report all problems on our GitHub
          </a>
        </v-card-text>
      </v-card>
      <v-card class="flex-grow-1 ma-1">
        <v-card-title>About</v-card-title>
        <v-card-subtitle>History of netsocadmin</v-card-subtitle>
        <v-card-text>
          <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet. Duis sagittis ipsum. Praesent mauris. Fusce nec tellus sed augue semper porta. Mauris massa. Vestibulum lacinia arcu eget nulla. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Curabitur sodales ligula in libero. Sed dignissim lacinia nunc. </p>

          <p>Curabitur tortor. Pellentesque nibh. Aenean quam. In scelerisque sem at dolor. Maecenas mattis. Sed convallis tristique sem. Proin ut ligula vel nunc egestas porttitor. Morbi lectus risus, iaculis vel, suscipit quis, luctus non, massa. Fusce ac turpis quis ligula lacinia aliquet. Mauris ipsum. Nulla metus metus, ullamcorper vel, tincidunt sed, euismod in, nibh. Quisque volutpat condimentum velit. </p>

          <p>Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Nam nec ante. Sed lacinia, urna non tincidunt mattis, tortor neque adipiscing diam, a cursus ipsum ante quis turpis. Nulla facilisi. Ut fringilla. Suspendisse potenti. Nunc feugiat mi a tellus consequat imperdiet. Vestibulum sapien. Proin quam. Etiam ultrices. Suspendisse in justo eu magna luctus suscipit. Sed lectus. </p>

          <p>Integer euismod lacus luctus magna. Quisque cursus, metus vitae pharetra auctor, sem massa mattis sem, at interdum magna augue eget diam. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Morbi lacinia molestie dui. Praesent blandit dolor. Sed non quam. In vel mi sit amet augue congue elementum. Morbi in ipsum sit amet pede facilisis laoreet. Donec lacus nunc, viverra nec, blandit vel, egestas et, augue. Vestibulum tincidunt malesuada tellus. Ut ultrices ultrices enim. Curabitur sit amet mauris. Morbi in dui quis est pulvinar ullamcorper. </p>

          <p>Nulla facilisi. Integer lacinia sollicitudin massa. Cras metus. Sed aliquet risus a tortor. Integer id quam. Morbi mi. Quisque nisl felis, venenatis tristique, dignissim in, ultrices sit amet, augue. Proin sodales libero eget ante. Nulla quam. Aenean laoreet. Vestibulum nisi lectus, commodo ac, facilisis ac, ultricies eu, pede. Ut orci risus, accumsan porttitor, cursus quis, aliquet eget, justo. Sed pretium blandit orci. Ut eu diam at pede suscipit sodales. </p>
        </v-card-text>
      </v-card>
      <v-card class="flex-grow-0 ma-1">
        <v-card-title>GDPR &amp; My Data</v-card-title>
        <v-card-subtitle></v-card-subtitle>
        <v-card-text>
          <p>You can request a data download at any time</p>
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
  name: 'Account',
  components: {},

  data: () => ({
    some: null
  })
})
</script>
