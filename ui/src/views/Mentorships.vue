<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="6">
        <v-card>
          <v-card-title>
            Mentorships
          </v-card-title>
          <v-card-subtitle>
            Learn something you don't get to learn in college
          </v-card-subtitle>
          <v-card-text>
            <p>
              We offer mentorships which take the form of an informal class that focuses on particular subjects that are not studied in college<br/>
              Subject matter can include new languages, frameworks and tools that are more commonly seen in a workplace than an academic setting.<br/>
              They are perfect for anyone wishing to prepare for graduation/find an internship or just supplement their learning<br/><br/>

              These mentorships are open to any and all members of Netsoc<br/>
              Applications are taken on a first-come-first-served basis so be sure to apply early!<br/><br/>

              Select a mentorship from the list below to see more information:
            </p>
            <v-list flat>
              <v-subheader v-if="Object.values(mentorships).length === 0">{{ empty }}</v-subheader>
              <v-list-item-group v-else v-model="selectedIdx" color="primary">
                <v-list-item
                  v-for="(mentorship, i) in mentorships"
                  :key="i"
                >
                  <v-list-item-content>
                    <v-list-item-title v-text="mentorship.title + ' - ' + mentorship.teacher"></v-list-item-title>
                  </v-list-item-content>
                </v-list-item>
              </v-list-item-group>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6">
        <v-card v-if="selectedIdx !== undefined">
          <v-card-title>
            {{ Object.values(mentorships)[selectedIdx].title }}
          </v-card-title>
          <v-card-subtitle>
            Mentored by {{ Object.values(mentorships)[selectedIdx].teacher }}
          </v-card-subtitle>
          <v-card-text>
            <div class="markdown" style="max-width: 100%; width: 100%; height: auto" v-html="descriptionHtml"/>
          </v-card-text>
          <v-card-actions>
            <div style="width: 100vw; padding: 1em">
              <v-textarea
                v-model="enrollReason"
                label="Why do you want to participate in this mentorship?"
                counter
                maxlength="250"
                full-width
                outlined
              ></v-textarea>
              <v-btn color="primary" @click="uiRegisterEnrollment()">
                <span>Register Interest</span>
                <v-icon style="margin-left: 6px">
                  mdi-send
                </v-icon>
              </v-btn>
            </div>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    <message-dialog :visible="msg.length > 0" @okay="msg = ''">
      {{ msg }}
    </message-dialog>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import MessageDialog from '@/components/MessageDialog'
import { config } from '@/config'
import { fetchRest } from '@/api/rest'

import marked from 'marked'

interface Mentorship {
  title: string;
  description: string;
  teacher: string;
}

export default Vue.extend({
  name: 'Mentorships',
  components: {
    MessageDialog
  },

  data: () => ({
    empty: 'All mentorship places have currently been filled, check back again at a later time to see if there any new mentorships are available',
    mentorships: {},
    selectedIdx: undefined,
    descriptionHtml: undefined,
    loading: false,
    headers: [
      { text: 'Title', value: 'title' },
      { text: 'Teacher', value: 'teacher' }
    ],
    enrollReason: '',
    msg: ''
  }),

  watch: {
    selectedIdx () {
      if (this.selectedIdx !== undefined) {
        let text = Object.values(this.mentorships)[this.selectedIdx].description
        console.log(text)
        // Trim preamble if it's present
        if (text.indexOf('---') === 0) {
          const index = text.indexOf('---', 3)

          if (index > 0) {
            text = text.substring(index + 3, text.length)
          }
        }

        this.descriptionHtml = marked(text)
      } else {
        this.descriptionHtml = ''
      }
    }
  },

  mounted () {
    this.uiReloadMentorships()
  },

  computed: {
    selectedMentorshipName () {
      if (this.selectedIdx !== undefined) {
        return Object.keys(this.mentorships)[this.selectedIdx]
      } else {
        return undefined
      }
    }
  },

  methods: {
    async uiRegisterEnrollment () {
      try {
        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/mentorships/${this.selectedMentorshipName}/enroll`, {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            },
            body: JSON.stringify({
              reason: this.enrollReason
            })
          })

        const info = await res.json()
        this.msg = info.detail.msg
        this.enrollReason = ''
        this.selectedIdx = undefined
      } catch (e) {
        this.msg = `Could not submit interest in the specified mentorship: ${e}`
      }
    },

    async uiReloadMentorships () {
      this.loading = true

      try {
        const res = await fetchRest(
          `${config.apiBaseUrl}/v1/mentorships`, {
            method: 'GET',
            headers: {
              Authorization: `Bearer ${this.$store.state.auth.user.access_token}`
            }
          })

        this.mentorships = await res.json()
        this.loading = false
      } catch (e) {
        this.loading = false
        this.mentorships = {}
        this.empty = `Could not load mentorships: ${e}`
      }
    }
  }
})
</script>
