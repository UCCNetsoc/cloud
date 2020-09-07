<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="6">
        <v-card>
          <v-card-title>
            Websites
          </v-card-title>
          <v-card-subtitle>
            Perfect for blogs, personal portfolios or societies
          </v-card-subtitle>
          <v-card-text>
            <p>
              We can host any content you store as a directory inside the <code>www</code> folder in your home directory<br>
              By pointing a domain at this directory, anyone with Internet access will be able to visit it<br>
              PHP is also served alongside static content
            </p>
            <p>
              <a>Need help?</a><br>
              Follow the tutorial on the <a>Getting Started</a> page to setup your first website
            </p>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6">
        <v-card>

        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="6">
        <v-card>
          <v-card-title>
            Using a netsoc.co subdomain
          </v-card-title>
          <v-card-text>
            <p>
              Every Netsoc member is entitled to complimentary netsoc.co <i>subdomains</i>
            </p>
            <p>
              You can point any complimentary subdomain at a directory by simply inputting <code>example.netsoc.co</code> into the Host field, where <code>example</code> is the name of the subdomain you want to use
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="6">
        <v-card>
          <v-card-title>
            <b>Using your own custom domain</b>
          </v-card-title>
          <v-card-text>
            <p>
              If you have purchased your own custom domain, there are extra steps you must perform.<br/><br/>
              You must add the records below to the DNS zone of the domain you wish to use<br/>
              and replace <code>mydomain.com</code> with the domain/subdomain you are using
            </p>
            <p>
              <code>mydomain.com</code><code>A</code> <code>84.39.234.51</code> <br>
              <code>nsa3</code><code>TXT</code> <code>ocanty</code>
            </p>
            <p>
              Once these records have been added, we can verify that you possess the domain.
              It may take up to 24hrs for any changes in DNS records you make to be updated.
            </p>
            <p>
              Your domain registrar will have tutorials for adding these records.<br/>
              If you are having trouble with this and want help, please contact us on our Discord
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'

export default Vue.extend({
  name: 'Tutorial',
  components: {
  },

  data: () => ({
  })
})
</script>
