<template>
  <v-container>
    <message-dialog :visible="msg.length > 0" @okay="msg = '', this.successful && $emit('successful')">
      {{ msg }}
    </message-dialog>
    <confirm-cancel-dialog
      title="instance request"
      :visible="visible"
      :loading="loading"
      @confirmed="submit()"
      @cancelled="$emit('cancelled')"
      width="560"
    >
      <v-form
        lazy-validation
        ref="form"
        v-if="request !== undefined || template !== undefined"
      >
        <v-text-field
          label='Token'
          v-model='token'
          disabled
        ></v-text-field>
        <v-text-field
          label='Email or username'
          v-model='emailOrUsername'
          disabled
        ></v-text-field>
        <v-text-field
          label='Hostname'
          v-model='hostname'
          disabled
        ></v-text-field>
        <v-container>
          <v-row no-gutters justify="start" align="center">
            <v-col sm="2">
              <v-avatar
                size="64"
                tile
              >
                <img
                  :src="template.logo_url"
                >
              </v-avatar>
            </v-col>
            <v-col sm="10">
              <h3 class="white--text">
                {{ template.title + ' ' + request.type }}
              </h3>
              <span>
                {{ getSpecString(template.specs) }}
              </span><br/>
            </v-col>
          </v-row>
        </v-container>
        <v-textarea
          label='Why do you need this instance?'
          class="py-4"
          style="margin-bottom: -2.5em"
          outlined
          disabled
          v-model='request.detail.reason'
        ></v-textarea>
        <v-tabs
          v-model="tab"
          align-with-title
          class="ma-0 pa-0"
        >
          <v-tabs-slider></v-tabs-slider>
          <v-tab
          >
            Approve
          </v-tab>
          <v-tab
          >
            Deny
          </v-tab>
        </v-tabs>
        <v-container v-if="tab === 0" class="mb-0 pb-0">
          <p>
            Press confirm to approve and install instance
          </p>
        </v-container>
        <v-container v-else-if="tab === 1">
          <v-textarea
            label='Denial reason'
            class="py-4"
            style="margin-bottom: -2em"
            outlined
            v-model='denyReason'
          ></v-textarea>
        </v-container>
      </v-form>
    </confirm-cancel-dialog>
  </v-container>
</template>

<script lang='ts'>
import Vue from 'vue'
import ConfirmCancelDialog from '@/components/ConfirmCancelDialog.vue'
import MessageDialog from '@/components/MessageDialog.vue'
import { config } from '@/config'
import { fetchRest } from '@/api/rest'

import { Specs, Request, Template } from '@/api/cloud'

export default Vue.extend({
  components: {
    ConfirmCancelDialog,
    MessageDialog
  },

  computed: {
    required (): ((v: string) => (string | boolean))[] {
      return [
        (v: string) => !!v || 'Required'
      ]
    }
  },

  mounted () {
    this.emailOrUsername = this.$route.params.emailOrUsername
    this.instanceRequestType = this.$route.params.instanceRequestType
    this.hostname = this.$route.params.hostname
    this.token = this.$route.params.token

    this.uiLoad()
  },

  data () {
    const template: Template | undefined = undefined
    const request: Request | undefined = undefined
    return {
      template,
      request,
      loading: false,
      successful: false,
      emailOrUsername: '',
      instanceRequestType: '',
      hostname: '',
      token: '',
      denyReason: '',
      tab: 0,
      msg: ''
    }
  },

  props: {
    visible: {
      type: Boolean,
      default: true
    }
  },

  methods: {
    async uiLoad (): Template {
      this.loading = true
      const headers = {
        Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
      }

      try {
        let req = await fetchRest(
        `${config.apiBaseUrl}/v1/proxmox/${this.emailOrUsername}/${this.instanceRequestType}/${this.hostname}?token=${this.token}`, {
          method: 'GET',
          headers
        })

        this.request = await req.json()

        req = await fetchRest(
          `${config.apiBaseUrl}/v1/proxmox/${this.emailOrUsername}/${this.request.type}-template/${this.request.detail.template_id}`, {
            method: 'GET',
            headers
          })

        this.template = await req.json()
      } catch (e) {
        this.msg = e.message
      } finally {
        this.loading = false
      }
    },

    getSpecString (specs: Specs): string {
      return `${specs.cores} CPU, ${specs.memory}MB RAM, ${specs.disk_space}GB disk space, ${specs.swap}MB swap`
    },

    async submit () {
      const headers = {
        Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
      }

      this.loading = true

      try {
        if (this.tab === 0) {
          await fetchRest(`${config.apiBaseUrl}/v1/proxmox/${this.emailOrUsername}/${this.instanceRequestType}/${this.hostname}/approval?token=${this.token}`, {
            method: 'POST',
            headers
          })

          this.msg = 'Instance request approved'
          this.successful = true
        } else {
          await fetchRest(`${config.apiBaseUrl}/v1/proxmox/${this.emailOrUsername}/${this.instanceRequestType}/${this.hostname}/denial?token=${this.token}`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
              reason: this.denyReason
            })
          })

          this.msg = 'Instance request denied'
          this.successful = true
        }
      } catch (e) {
        this.msg = e.message
        this.successful = false
      } finally {
        this.loading = false
      }
    }
  }
})
</script>
