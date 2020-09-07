<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="12">
        <v-card>
          <v-container fluid class="d-flex flex-xs-wrap flex-sm-wrap flex-md-nowrap py-2">
            <v-card flat>
              <v-card-title>
                Blogs &amp; Websites
              </v-card-title>
              <v-card-subtitle>
                Perfect for personal websites, portfolios or societies
              </v-card-subtitle>
              <v-card-text>
                <p>
                  We can host any content you store inside the <code>www</code> folder in your home directory<br>
                  By having a folder named after a domain name in this directory, anyone with Internet access
                  will be able to visit it (given that the domain is setup correctly)<br>
                  <br>
                  PHP is also served alongside static content. More runtimes such as Python WSGI, NodeJS and Go are coming soon
                </p>
                <p>
                  <a>Need help?</a><br>
                  Follow the <a v-on:click="$router.push('/tutorial')">Tutorial</a> page to setup your first website
                </p>
              </v-card-text>
            </v-card>
            <v-divider vertical class="hidden-sm-and-down"/>
            <v-card flat>
              <v-card-title>
                <b>Using your netsoc.co subdomain</b>
              </v-card-title>
              <v-card-text>
                <p>
                  Every user is entitled to a netsoc.co subdomain, your subdomain is:
                  <code>{{ $store.state.auth.user.profile.preferred_username }}.netsoc.co</code>
                </p>
                <p>
                  If you have just created your account, you will have a blank website setup.
                  All you need to do is insert an <code>index.html</code>/<code>index.php</code> and it
                  will then be available at your subdomain
                </p>
                <p>
                  If you want to set up a blog like WordPress, see the section on Installing Software
                </p>
              </v-card-text>
            </v-card>
            <v-divider vertical class="hidden-sm-and-down"/>
            <v-card flat>
              <v-card-title>
                <b>Using your own custom domain</b>
              </v-card-title>
              <v-card-text>
                <p>
                  If you have purchased your own custom domain, there are extra steps you must perform.<br/><br/>
                  You must add the records shown below to the DNS zone of the domain you wish to use,<br/>replace <code>mydomain.com</code> with the domain/subdomain you are using
                </p>
                <p>
                  <code>mydomain.com</code><code>A</code> <code>84.39.234.51</code> <br>
                  <code>mydomain.com</code><code>A</code> <code>84.39.234.50</code> <br>
                  <code>_netsoc</code><code>TXT</code> <code>{{ $store.state.auth.user.profile.preferred_username }}</code>
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
            <v-divider vertical class="hidden-sm-and-down"/>
            <v-card flat>
              <v-card-title>
                <b>Installing Software</b>
              </v-card-title>
              <v-card-text>
                <p>
                  We can automate the installation of some software such as WordPress.<br/><br />
                  To first install software your website directory must be empty except for the config file <code>netsoc.json</code> (dont delete this!).<br/>
                  If you have just created your website, you will able to install software right away<br/>
                </p>
                <p>
                  The <a v-on:click="$router.push('/tutorial')">Tutorial</a> page covers a WordPress installation
                </p>
              </v-card-text>
            </v-card>
          </v-container>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="12" align="stretch">
        <v-card>
          <websites-list/>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import WebsitesList from '@/components/WebsitesList.vue'

export default Vue.extend({
  name: 'Websites',
  components: {
    WebsitesList
  },

  data: () => ({
  })
})
</script>
