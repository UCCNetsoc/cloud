<template>
  <v-container>
    <card-dialog
      :visible="visible"
      width="380"
    >
      <v-card-title class="justify-center text-center white--text font-weight-light">
        verify account
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
            :disabled='$route.params.emailOrUsername !== undefined'
          ></v-text-field>
          <v-text-field
            label='Verification token'
            v-model='token'
            :rules='required'
            :disabled='$route.params.token !== undefined'
          ></v-text-field>
           <v-text-field
            label='Password'
            v-model='password'
            :rules='passwordRules'
            type='password'
          ></v-text-field>
          <v-text-field
            label='Confirm password'
            v-model='confirmPassword'
            :rules='confirmPasswordRules'
            type='password'
          ></v-text-field>
        </v-form>
      </v-card-text>
      <v-divider/>
      <v-card-actions class="justify-center ma-3">
        <v-btn v-on:click="submit()" color="green">Confirm</v-btn>
        <v-btn v-on:click="$router.push('/accounts/verification-email')" color="warning">Resend</v-btn>
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
import { openApiGetSchemaProperty, openApiPropertyValidator } from '@/api/openapi'

export default Vue.extend({
  name: 'SignUpVerifyDialog',
  components: {
    CardDialog
  },

  computed: {
    required (): ((v: string) => (string | boolean))[] {
      return [
        (v: string) => !!v || 'Required'
      ]
    },

    passwordRules (): ((v: string) => (string | boolean))[] {
      return [
        (v: string) => !!v || 'Password required',
        openApiPropertyValidator(openApiGetSchemaProperty('CompleteVerification', 'password'))
      ]
    },

    confirmPasswordRules (): ((v: string) => (string | boolean))[] {
      return [
        () => (this.password === this.confirmPassword) || 'Passwords do not match'
      ]
    }
  },

  mounted () {
    this.token = this.$route.params.token || ''
    this.emailOrUsername = this.$route.params.emailOrUsername || ''
  },

  data: () => ({
    successful: false,
    emailOrUsername: '',
    token: '',

    password: '',
    confirmPassword: '',
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

    async submit () {
      // @ts-ignore
      if (this.$refs.form.validate()) {
        try {
          const res = await fetchRest(`${config.apiBaseUrl}/v1/accounts/${this.emailOrUsername}/verification`, {
            method: 'POST',
            body: JSON.stringify({
              serialized_verification: {
                token: this.token
              },
              password: this.password
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
            msg: `Could not verify your account: ${e.message}`
          }
        }
      }
    }
  }
})
</script>
