<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="12">
        <v-card>
          <v-container fluid class="d-flex flex-xs-wrap flex-sm-wrap flex-md-nowrap py-2">
            <v-card flat>
              <v-card-title>
                Databases
              </v-card-title>
              <v-card-subtitle>
                Store that data!
              </v-card-subtitle>
              <v-card-text>
                <v-list flat>
                  Select a database from the list below:
                  <v-list-item-group v-model="selectedDbServer" color="primary">
                    <v-list-item
                      v-for="db in dbServers"
                      :key="db"
                    >
                      <v-list-item-content>
                        <v-list-item-title v-text="db"></v-list-item-title>
                      </v-list-item-content>
                    </v-list-item>
                  </v-list-item-group>
                </v-list>
              </v-card-text>
            </v-card>
            <v-divider v-if="selectedDbServer !== undefined" vertical class="hidden-sm-and-down"/>
            <v-container v-if="selectedDbServer == 0" flat>
              <my-sql-info/>
            </v-container>
          </v-container>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="12" align="stretch">
        <v-card v-if="selectedDbServer == 0">
          <my-sql-list />
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import MySqlList from '@/components/MySqlList.vue'
import MySqlInfo from '@/components/MySqlInfo.vue'

export default Vue.extend({
  name: 'Databases',
  components: {
    MySqlInfo,
    MySqlList
  },

  data: () => ({
    dbServers: ['MySQL'],
    selectedDbServer: undefined
  })
})
</script>
