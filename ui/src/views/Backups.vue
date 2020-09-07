<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" sm="6">
        <v-card>
          <v-card-title>
            Backups
          </v-card-title>
          <v-card-subtitle>
            For that odd mishap or two
          </v-card-subtitle>
          <v-card-text>
            <p>
              We backup your home directory on <i>hourly</i>, <i>daily</i>, <i>weekly</i> and <i>monthly</i> schedules.<br>
              We offer two methods of recovering data
            </p>
            <ul>
              <li>
                <b>To get a complete dump of your home directory:</b>
                <p>
                  Dumps of your home directory are available on this page.<br/>
                  They are in the <code>.tar.gz</code> format, you will need software like <code>tar</code>, 7zip or WinRAR to open them
                </p>
              </li>
              <li>
                <b>To view/recover a specific set of files at a specific point in time:</b>
                <p>
                  Connect to the user server by <code>ssh</code> or using the Terminal<br/>
                  Run <code>cd ~/.snaps && ls -lat</code> and you will be shown a list of possible backups<br>
                  The files in this directory will consist of compressed archives (like tar.gz, you will need <code>tar</code>, 7zip or WinRAR to open these) or a browseable file tree of the point of time of the backup<br /><br />
                  These files are read-only so you will need to copy them to back to your home directory root to manipulate them
                </p>
              </li>
            </ul>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6">
        <v-card>
          <backups-list/>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import Vue from 'vue'
import BackupsList from '@/components/BackupsList.vue'

export default Vue.extend({
  name: 'Backups',
  components: {
    BackupsList
  },

  data: () => ({
  })
})
</script>
