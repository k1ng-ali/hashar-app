<script setup lang="ts">
import LegalDocument from '@/shared/components/LegalDocument.vue'
import { TERMS } from './content.ts'
</script>

<template>
  <LegalDocument :documents="TERMS" />
</template>
