<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="12">
        <v-data-table
            :headers="headers"
            :items="mappings"
            :hide-default-footer="true"
            :items-per-page="999999"
          >
            <template slot="no-data">
              You have no websites, get started by adding one below:
            </template>
            <template v-slot:item.actions="{ item }">
              <v-icon
                small
                @click="deleteItem(item)"
              >
                mdi-delete
              </v-icon>
            </template>
          </v-data-table>
      </v-col>
    </v-row>
    <v-row class="center ml-1" style="margin-top: -1em">
      <v-col class="d-flex  justify-end" cols="12" sm="12">
        <v-btn @click="dialog = true" icon>
          <v-icon>
            mdi-plus
          </v-icon>
        </v-btn>
      </v-col>
    </v-row>
    <v-dialog
      v-model="dialog"
      width="420"
      persistent
    >
      <dialog-logo/>
      <v-card>
        <v-card-text>
          <v-container fluid>
            <v-row>
              <v-col class="d-flex" cols="12" sm="6">
                <v-text-field
                  label="Domain"
                  v-model="input.domain"
                  placeholder="example.netsoc.co"
                ></v-text-field>
              </v-col>
              <v-col class="d-flex" cols="12" sm="6">
                <v-text-field
                  label="Directory"
                  prefix="www"
                  v-model="input.directory"
                  placeholder="/"></v-text-field>
              </v-col>
            </v-row>
            <v-row class="d-flex justify-end">
              <v-col class="d-flex justify-end" cols="12" sm="2">
                <v-btn @click="addMapping(); dialog = false" icon>
                  <v-icon>
                    mdi-check
                  </v-icon>
                </v-btn>
                <v-btn @click="dialog = false" icon>
                  <v-icon>
                    mdi-close
                  </v-icon>
                </v-btn>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script lang='ts'>
import DialogLogo from '@/components/DialogLogo.vue'
import Vue from 'vue'

export default Vue.extend({
  name: 'DomainDirectoryMapping',
  components: {
    DialogLogo
  },

  methods: {
    addMapping () {
      this.mappings.push({
        ...this.input
      })
    }
  },

  data () {
    return {
      dialog: false,

      mappings: [
        { directory: 'ay', domain: 'b.com' }
      ],

      input: {
        directory: '',
        domain: ''
      },

      headers: [
        {
          text: 'Domain',
          sortable: false,
          value: 'domain'
        },
        { text: 'Directory in www/', sortable: false, value: 'directory' }
      ]
    }
  }
})
</script>
