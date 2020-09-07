<template>
  <v-card :loading="loading" flat>
    <v-card-title>
      <b>MySQL (mysql.netsoc.co)</b>
    </v-card-title>
    <v-card-text v-if="!loading">
      <v-container class="pa-0" v-if="hasUser === false">
        <p>
          You do not currently have a MySQL user, press the button below to set one up:
        </p>
        <v-btn color="primary" @click="popConfirmCancel(ConfirmCancelMode.CreateUser)">
          <span>Create User</span>
          <v-icon style="margin-left: 6px">
            mdi-send
          </v-icon>
        </v-btn>
      </v-container>
      <v-container  class="pa-0" v-else>
        <p>
          You can connect to the MySQL server @ <code>mysql.netsoc.co</code><br/><br/>
          Your MySQL username is <code>{{ this.$store.state.auth.user.profile.preferred_username }}</code><br/><br/>
          If you have just created your MySQL user, check your email for it's password.<br/>
          Alternatively, you can reset it below:
        </p>
        <v-btn color="warning" @click="popConfirmCancel(ConfirmCancelMode.ResetPassword)">
          <span>Reset Password</span>
          <v-icon style="margin-left: 6px">
            mdi-send
          </v-icon>
        </v-btn>
      </v-container>
    </v-card-text>
    <message-dialog :visible="msg.length > 0" @okay="msg = ''">
      {{ msg }}
    </message-dialog>
    <confirm-cancel-dialog
      :title="confirmCancel.mode"
      :visible="confirmCancel.mode !== ConfirmCancelMode.Hidden"
      :loading="confirmCancel.loading"
      @confirmed="confirm()"
      @cancelled="cancel()"
      centered
    >
      <p v-if="confirmCancel.mode == ConfirmCancelMode.CreateUser" style="text-align: center">
        Your are about to create your MySQL user <code>{{ this.$store.state.auth.user.profile.preferred_username }}</code><br /><br />
        <b>The password will be emailed to the email address associated with your account</b>
      </p>
      <p v-else-if="confirmCancel.mode == ConfirmCancelMode.ResetPassword" style="text-align: center">
        Are you sure you want to reset your MySQL password?<br/><br/>
        Your new password for this user will be emailed to the email address associated with your account
      </p>
    </confirm-cancel-dialog>
  </v-card>
</template>

<script lang='ts'>
import ConfirmCancelDialog from '@/components/ConfirmCancelDialog.vue'
import MessageDialog from '@/components/MessageDialog.vue'

import { config } from '@/config'
import { fetchRest } from '@/api/rest'

import Vue from 'vue'

enum ConfirmCancelMode {
  Hidden = '-',
  CreateUser = 'create MySQL user',
  ResetPassword = 'reset MySQL user password',
}

interface ConfirmCancelAction {
  placeholder?: string;
}

export default Vue.extend({
  name: 'MySQLList',
  components: {
    ConfirmCancelDialog,
    MessageDialog
  },

  computed: {
    required () {
      return [
        (v: string) => !!v || 'Required'
      ]
    }
  },

  methods: {
    async popConfirmCancel (mode: ConfirmCancelMode, action: ConfirmCancelAction = {}) {
      this.confirmCancel.action = action
      this.confirmCancel.mode = mode
    },

    async confirm () {
      // Extract username from profile
      const username = this.$store.state.auth.user.profile.preferred_username
      const headers = {
        Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
      }

      // Extract action
      // const { _ } = this.confirmCancel.action
      this.confirmCancel.loading = true

      try {
        switch (this.confirmCancel.mode) {
          case ConfirmCancelMode.CreateUser: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/mysql/${username}/user`, {
                method: 'POST',
                headers
              })

            // Send them the password
            await fetchRest(
              `${config.apiBaseUrl}/v1/mysql/${username}/user/password-reset-email`, {
                method: 'POST',
                headers
              })

            // const detail = await res.json()
            this.msg = 'MySQL user created, check your email for the password'
            break
          }

          case ConfirmCancelMode.ResetPassword: {
            await fetchRest(
              `${config.apiBaseUrl}/v1/mysql/${username}/user/password-reset-email`, {
                method: 'POST',
                headers
              })

            // const d = await res.json()
            this.msg = 'Password reset, check your email!'
          }
        }
      } catch (e) {
        this.msg = e.message
      } finally {
        this.confirmCancel.loading = false
        this.confirmCancel.mode = ConfirmCancelMode.Hidden
        this.uiReloadUserStatus()
      }
    },

    async cancel () {
      this.confirmCancel.loading = false
      this.confirmCancel.mode = ConfirmCancelMode.Hidden
    },

    async uiReloadUserStatus () {
      this.loading = true

      try {
        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/mysql/${this.$store.state.auth.user.profile.preferred_username}/user`, {
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          }, [200, 404])

        if (res.status === 200) {
          this.hasUser = true
        } else if (res.status === 404) {
          this.hasUser = false
        }

        this.loading = false
      } catch (e) {
        this.loading = false
        this.msg = `Could not get your MySQL user status: ${e}`
      }
    }
  },

  data () {
    const action: ConfirmCancelAction = {}

    return {
      ConfirmCancelMode, // Needed to use the enum in the rendered template
      loading: true,
      empty: '',
      msg: '',

      confirmCancel: {
        mode: ConfirmCancelMode.Hidden,
        loading: false,
        action
      },

      hasUser: false
    }
  },

  mounted () {
    this.uiReloadUserStatus()
  }
})
</script>
