<template>
  <v-container>
    <card-dialog
      :visible="visible"
      width="380"
    >
      <v-card-title class="justify-center text-center white--text font-weight-light">
        resend verification
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
          <vue-hcaptcha v-if="hcaptcha !== ''" :sitekey='hcaptcha' @verify='onVerify'></vue-hcaptcha>
        </v-form>
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
import VueHcaptcha from '@hcaptcha/vue-hcaptcha'

export default Vue.extend({
  name: 'SignUpResendVerfyDialog',
  components: {
    CardDialog,
    VueHcaptcha
  },

  computed: {
    required () {
      return [
        (v: string) => !!v || 'Required'
      ]
    },
    hcaptcha () {
      return config.hCaptchaSiteKey
    }
  },

  mounted () {
    this.emailOrUsername = this.$route.params.emailOrUsername || ''
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
        this.$emit('sucessful')
      }
    },

    onVerify (response: string) {
      this.hcaptchaResponse = response
      this.disabled = false
    },

    async submit () {
      if (this.$refs.form.validate()) {
        try {
          const res = await fetchRest(`${config.apiBaseUrl}/v1/accounts/${this.emailOrUsername}/verification-email`, {
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
            msg: `Could not resend verification: ${e.message}`
          }
        }
      }
    }
  }
})
</script>
