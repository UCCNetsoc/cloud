<template>
  <v-container>
    <card-dialog
      :visible="visible"
      width="380"
    >
      <v-card-title class="justify-center text-center white--text font-weight-light">
        password reset
      </v-card-title>
      <v-divider/>
      <v-card-text>
        <v-form
          lazy-validation
          ref="form"
        >
          <v-text-field
            label='Email or username'
            v-model='emailOrUsername'
            :rules='required'
            :disabled='$store.state.auth.user !== null'
          ></v-text-field>
        </v-form>
      </v-card-text>
      <vue-hcaptcha :key="resultDialog.visible" v-if="hcaptcha !== ''" :sitekey='hcaptcha' @verify='onVerify'></vue-hcaptcha>
      <v-divider/>
      <v-card-actions class="justify-center ma-3">
        <v-btn :disabled='disabled' v-on:click="submit()" color="green">Confirm</v-btn>
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
import VueHcaptcha from '@hcaptcha/vue-hcaptcha'

export default Vue.extend({
  name: 'PasswordResetDialog',
  components: {
    CardDialog,
    VueHcaptcha
  },

  computed: {
    required (): ((v: string) => (string | boolean))[] {
      return [
        (v: string) => !!v || 'Required'
      ]
    },

    hcaptcha (): string {
      return config.hCaptchaSiteKey
    }
  },

  mounted () {
    this.emailOrUsername = this.$route.params.emailOrUsername || ''

    if (this.$store.state.auth.user != null) {
      this.emailOrUsername = this.$store.state.auth.user.profile.email
    }
  },

  data: () => ({
    successful: false,
    emailOrUsername: '',

    hcaptchaResponse: '',
    disabled: config.hCaptchaSiteKey !== '',

    resultDialog: {
      visible: false,
      msg: ''
    }
  }),

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

    onVerify (response: string) {
      this.hcaptchaResponse = response
      this.disabled = false
    },

    async submit () {
      // @ts-ignore
      if (this.$refs.form.validate()) {
        try {
          const res = await fetchRest(`${config.apiBaseUrl}/v1/accounts/${this.emailOrUsername}/password-reset-email`, {
            method: 'POST',
            body: JSON.stringify({
              captcha: this.hcaptchaResponse
            })
          })

          const { detail } = await res.json()
          this.resultDialog = {
            visible: true,
            msg: detail.msg
          }
          this.successful = (res.status === 201)
        } catch (e) {
          this.resultDialog = {
            visible: true,
            msg: `Could not send password reset email: ${e.message}`
          }
          this.successful = false
        }
      }
    }
  }
})
</script>
