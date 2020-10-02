<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="12">
        <v-data-table
            :loading="loading"
            :headers="headers"
            :items="databases"
            :items-per-page="20"
            style="margin-top: -1rem"
          >
            <template slot="no-data">
              {{ empty }}
            </template>

            <template v-slot:item="row">
              <tr>
                <td>
                  {{row.item.name}}
                </td>
                <td style="text-align: left">
                  <v-btn
                    icon
                    @click="popConfirmCancel(ConfirmCancelMode.DeleteDatabase, { name: row.item.name })"
                  >
                    <v-icon>
                      mdi-delete
                    </v-icon>
                  </v-btn>
                </td>
              </tr>
            </template>

          </v-data-table>
      </v-col>
    </v-row>
    <v-row class="center ml-1" style="margin-top: -1em">
      <v-col class="d-flex  justify-end" cols="12" sm="12">
        <v-btn @click="popConfirmCancel(ConfirmCancelMode.CreateDatabase, { })" icon>
          <v-icon>
            mdi-plus
          </v-icon>
        </v-btn>
        <v-btn @click="uiReloadDatabases()" icon>
          <v-icon>
            mdi-refresh
          </v-icon>
        </v-btn>
      </v-col>
    </v-row>
    <message-dialog :visible="msg.length > 0" @okay="msg = ''">
      {{ msg }}
    </message-dialog>
    <confirm-cancel-dialog
      :title="confirmCancel.mode"
      :visible="confirmCancel.mode !== ConfirmCancelMode.Hidden"
      :loading="confirmCancel.loading"
      @confirmed="confirm()"
      @cancelled="cancel()"
      class="confirmCancel"
    >
      <v-form
        v-if="confirmCancel.mode == ConfirmCancelMode.CreateDatabase"
        lazy-validation
        ref="form"
        @submit="confirm()"
      >
        <v-text-field
          :prefix="$store.state.auth.user.profile.preferred_username + '_'"
          label='Database name'
          :rules="databaseNameRules"
          v-model='confirmCancel.action.name'
        ></v-text-field>
      </v-form>
      <p style="text-align: center" v-else-if="confirmCancel.mode == ConfirmCancelMode.DeleteDatabase">
        Are you sure you want to delete the database?<br>
        This action is unrecoverable and will remove ALL data in the database!
      </p>
    </confirm-cancel-dialog>
  </v-container>
</template>

<style scoped>
.confirmCancel p {
  text-align: center !important;
}
</style>

<script lang='ts'>
import ConfirmCancelDialog from '@/components/ConfirmCancelDialog.vue'
import MessageDialog from '@/components/MessageDialog.vue'

import { config } from '@/config'
import { fetchRest } from '@/api/rest'
import { openApiGetSchemaProperty, openApiPropertyValidator } from '@/api/openapi'

import Vue from 'vue'

interface Database {
  name: string;
}

enum ConfirmCancelMode {
  Hidden = '-',
  CreateDatabase = 'create database',
  DeleteDatabase = 'delete database',
}

interface ConfirmCancelAction {
  name?: string;
}

export default Vue.extend({
  name: 'MySqlList',
  components: {
    ConfirmCancelDialog,
    MessageDialog
  },

  computed: {
    required (): ((v: string) => (string | boolean))[] {
      return [
        (v: string) => !!v || 'Required'
      ]
    },

    databaseNameRules () {
      return [
        (v: string) => !!v || 'Database name required',
        openApiPropertyValidator(openApiGetSchemaProperty('Database', 'title'))
      ]
    }
  },

  methods: {
    async confirm () {
      // Extract username from profile
      const username = this.$store.state.auth.user.profile.preferred_username
      const headers = {
        Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
      }

      // Extract action
      const { name } = this.confirmCancel.action

      this.confirmCancel.loading = true

      try {
        switch (this.confirmCancel.mode) {
          case ConfirmCancelMode.CreateDatabase: {
            // @ts-ignore
            if (!this.$refs.form.validate()) return

            await fetchRest(
              `${config.apiBaseUrl}/v1/mysql/${username}/databases/${username + '_' + name}`, {
                method: 'POST',
                headers
              }, [201])

            this.msg = 'Database created'
            break
          }

          case ConfirmCancelMode.DeleteDatabase: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/mysql/${username}/databases/${name}`, {
                method: 'DELETE',
                headers
              }, [200])

            this.msg = 'Database deleted'
            break
          }
        }
      } catch (e) {
        this.msg = e.message
      } finally {
        this.confirmCancel.loading = false
        this.confirmCancel.mode = ConfirmCancelMode.Hidden
        this.uiReloadDatabases()
      }
    },

    async cancel () {
      this.confirmCancel.loading = false
      this.confirmCancel.mode = ConfirmCancelMode.Hidden
    },

    async uiReloadDatabases () {
      this.loading = true
      this.databases = []

      try {
        // console.log(config)
        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/mysql/${this.$store.state.auth.user.profile.preferred_username}/databases/`, {
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          })

        this.loading = false
        this.databases = await res.json()

        if (this.databases.length === 0) {
          this.empty = 'You have no databases, try adding one!'
        }
      } catch (e) {
        this.loading = false
        this.databases = []
        this.empty = e.message
      }
    },

    async popConfirmCancel (mode: ConfirmCancelMode, action: ConfirmCancelAction) {
      this.confirmCancel.action = action
      this.confirmCancel.mode = mode
    }
  },

  data () {
    const databases: Database[] = []
    const action: ConfirmCancelAction = {}

    return {
      ConfirmCancelMode, // Needed to use the enum in the rendered template
      loading: true,
      empty: '',
      msg: '',
      databases,

      confirmCancel: {
        mode: ConfirmCancelMode.Hidden,
        loading: false,
        action
      },

      headers: [
        { text: 'Name', value: 'name' },
        { text: 'Actions' }
      ]
    }
  },

  mounted () {
    this.uiReloadDatabases()
  }
})
</script>
