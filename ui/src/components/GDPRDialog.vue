<template>
  <v-container>
    <card-dialog
      :visible="visible"
      width="460"
      overlay-opacity="0.4"
    >
      <v-card-title class="justify-center text-center white--text font-weight-light">
        GDPR data request
      </v-card-title>
      <v-divider/>
      <v-card-text style="margin: -1em 0">
        <v-form
          lazy-validation
          ref="form"
          class=""
        >
          <v-checkbox
            v-model='request.account'
          >
            <span slot='label'>
              Account Metadata<br/>
              <small>
                <i>Username, email and membership information</i>
              </small>
              <br/>
              <small class="green--text">
                Tiny (1KB)
              </small>
            </span>
          </v-checkbox>
          <!-- <v-checkbox
            v-model='request.backups'
          >
            <span slot='label'>
              Backups / Home Directory<br/>
              <small>
                <i>Your latest home directory backup (if available)</i>
              </small><br/>
              <small class="orange--text">
                Medium (15MB-500MB-1GB)
              </small>
            </span>
          </v-checkbox> -->
          <!-- <v-checkbox
            v-model='request.databases'
          >
            <span slot='label'>
              Databases<br/>
              <small><i>A full dump of all of your databases</i></small><br />
              <small class="orange--text">Medium (15MB-500MB-1GB)</small>
            </span>
          </v-checkbox> -->
          <!-- <v-checkbox
            v-model='request.cloud'
          >
            <span slot='label'>
              VPS / VMs<br/>
              <small><i>A full dump of all of your virtual private servers / machines</i></small><br />
              <small class="red--text">Huge (6GB-15GB per vm)</small>
            </span>
          </v-checkbox> -->
        </v-form>
        <p class="text-center red--text">
          <b class="red--text">
            The files you download may contain sensitive information.<br/><br/>
          </b>
          Do not share them with others or they may be able to use your data to gain access to your account
        </p>
      </v-card-text>
      <v-divider/>
      <v-card-actions class="justify-center ma-3">
        <v-btn v-on:click="submit()" color="green">Confirm</v-btn>
        <v-btn v-on:click="$emit('cancelled')" color="red">Cancel</v-btn>
      </v-card-actions>
    </card-dialog>
    <card-dialog
      :visible="resultDialog.visible"
      width="480"
    >
      <v-card-text class="justify-center text-center">
        {{ this.resultDialog.msg }}
      </v-card-text>
      <v-card-actions class="justify-center mb-4">
        <v-btn v-on:click="closeResultDialog()" color="green">Okay</v-btn>
      </v-card-actions>
    </card-dialog>
  </v-container>
</template>

<script lang='ts'>
import Vue from 'vue'
import CardDialog from '@/components/CardDialog.vue'
import { config } from '@/config'
import { fetchRest } from '@/api/rest'

export default Vue.extend({
  name: 'GDPRDialog',
  components: {
    CardDialog
  },

  props: {
    visible: {
      type: Boolean,
      default: true
    }
  },

  methods: {
    closeResultDialog () {
      this.resultDialog.visible = false

      if (this.successful) {
        this.$emit('successful')
      }
    },

    async download (blob: Blob, filename: string) {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url

      a.download = `${filename}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
    },

    async submit () {
      // @ts-ignore
      this.$refs.form.validate()

      // @ts-ignore
      if (!this.$refs.form.validate()) return

      try {
        if (this.request.account) {
          const res = await fetchRest(
            `${config.apiBaseUrl}/v1/accounts/${this.$store.state.auth.user.profile.preferred_username}/gdpr-data`, {
              headers: {
                Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
              }
            }
          )

          const blob = await res.blob()
          this.download(blob, 'account-metadata.json')
        }

        this.successful = true
        this.resultDialog = {
          visible: true,
          msg: 'All files should now be downloading. If you have any queries about the data you received, contact a SysAdmin on the Netsoc Discord'
        }
      } catch (e) {
        this.resultDialog = {
          visible: true,
          msg: `An unexpected error happened, please try again later.\nIf the issue persists contact a SysAdmin on the Netsoc Discord (${e.message})`
        }
        this.successful = false
      }
    }
  },

  // mounted () {
  //   return
  // },

  data: () => ({
    successful: false,

    resultDialog: {
      visible: false,
      msg: ''
    },

    request: {
      account: true,
      database: false,
      cloud: false,
      backups: false

    }
  })

})
</script>
