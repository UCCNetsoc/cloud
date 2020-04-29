<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="6">
        <v-card>
          <v-card-title>
            <h1>Databases</h1>
          </v-card-title>
          <v-card-text>
            <p>
              We offer MySQL &amp; PostgreSQL databases to all of our users
              You will need
            </p>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6">
        <v-card>
          <domain-directory-mapping/>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import DomainDirectoryMapping from '@/components/DomainDirectoryMapping.vue'

export default Vue.extend({
  name: 'Databases',
  components: {
    DomainDirectoryMapping
  },

  data: () => ({
  })
})
</script>
