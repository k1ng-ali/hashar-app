<script setup lang="ts">
import LegalDocument from '@/shared/components/LegalDocument.vue'
import { PRIVACY } from './content.ts'
</script>

<template>
  <LegalDocument :documents="PRIVACY" />
</template>
