<template>
  <file-manager />
</template>

<script lang="ts">
import Vue from 'vue'
import FileManager from '@/components/FileManager.vue'

export default Vue.extend({
  name: 'FileManager',
  components: { FileManager },

  data: () => ({
  })
})
</script>
