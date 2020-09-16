<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="12">
        <v-data-table
            :loading="loading"
            :headers="headers"
            :items="backups"
            :items-per-page="10"
            style="margin-top: -1rem"
          >
            <template slot="no-data">
              {{ empty }}
            </template>

            <template v-slot:item="row">
              <tr>
                <td class="d-flex space-between align-center">
                  <p style="height: 8px">
                    {{row.item.name}}
                  </p>
                  <v-spacer/>
                  <v-btn @click="downloadBackup(row.item)" icon>
                    <v-icon dark>mdi-download</v-icon>
                  </v-btn>
                </td>
              </tr>
          </template>
          </v-data-table>
      </v-col>
    </v-row>
    <v-row class="center ml-1" style="margin-top: -1em">
      <v-col class="d-flex  justify-end" cols="12" sm="12">
        <v-btn @click="loadBackups()" icon>
          <v-icon>
            mdi-refresh
          </v-icon>
        </v-btn>
      </v-col>
    </v-row>
    <message-dialog :visible="msg.length > 0" @okay="msg = ''">
      {{ msg }}
     </message-dialog>
  </v-container>
</template>

<style scoped>

/* disable hover on table */
.v-data-table
  tbody
  tr:hover:not(.v-data-table__expanded__content) {
  background: rgba(0,0,0,0) !important;
}
</style>

<script lang='ts'>
import MessageDialog from '@/components/MessageDialog.vue'
import { config } from '../config'
import Vue from 'vue'
import { fetchRest } from '@/api/rest'

interface Backup {
  name: string;
}

export default Vue.extend({
  name: 'BackupsList',
  components: {
    MessageDialog
  },

  methods: {
    async downloadBackup (backup: Backup) {
      try {
        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/backups/${this.$store.state.auth.user.profile.preferred_username}/${backup.name}/download-link`, {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          }, [201])

        for (const entry of res.headers.entries()) {
          // console.log(entry)
        }
        const a = document.createElement('a')
        a.setAttribute('href', `${config.apiBaseUrl}${res.headers.get('location')}`)
        a.setAttribute('download', '1')
        a.setAttribute('_target', 'blank')
        a.click()
      } catch (e) {
        this.msg = e.message
      }
    },

    async loadBackups () {
      this.loading = true

      try {
        const res = await fetchRest(`${config.apiBaseUrl}/v1/backups/${this.$store.state.auth.user.profile.preferred_username}`, {
          headers: {
            Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
          }
        }, [200])

        this.loading = false
        this.backups = await res.json()

        if (this.backups.length === 0) {
          this.empty = 'You have no backups. Backups are scheduled at regular intervals, please come back later'
        }
      } catch (e) {
        this.loading = false
        this.backups = []
        this.empty = e.message
      }
    }
  },

  data () {
    const backups: Backup[] = []

    return {
      msg: '',

      loading: true,
      empty: '',
      backups: backups,
      headers: [
        {
          text: 'Backup:',
          sortable: true,
          value: 'name'
        }
      ]
    }
  },

  mounted () {
    this.loadBackups()
  }
})
</script>
