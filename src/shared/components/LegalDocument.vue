<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { LuArrowLeft } from '@kalimahapps/vue-icons/lu'
import AppLogo from '@/shared/components/AppLogo.vue'
import type { AppLocale } from '@/shared/i18n/index.ts'
import { formatDate } from '@/shared/lib/format.ts'
import { LEGAL_UPDATED, type LegalDocument } from '@/shared/lib/legal.ts'

// Публичная страница-документ (политика, удаление аккаунта): открывается и без входа,
// в том числе по прямой ссылке из Google Play
const props = defineProps<{
  documents: Record<AppLocale, LegalDocument>
}>()

const { locale } = useI18n()
const router = useRouter()

const doc = computed(() => props.documents[locale.value as AppLocale] ?? props.documents.ru)

function goBack() {
  // Открыли по прямой ссылке — назад некуда, ведём на главную
  if (window.history.state?.back) router.back()
  else void router.push('/')
}
</script>

<template>
  <article class="legal-page">
    <header class="top">
      <button class="back-btn" @click="goBack">
        <LuArrowLeft />
        {{ $t('legal.back') }}
      </button>
      <AppLogo :size="32" />
    </header>

    <h1>{{ doc.title }}</h1>
    <p class="updated">{{ $t('legal.updated', { date: formatDate(LEGAL_UPDATED) }) }}</p>
    <p class="intro">{{ doc.intro }}</p>

    <section v-for="section in doc.sections" :key="section.heading" class="section">
      <h2>{{ section.heading }}</h2>
      <p v-for="paragraph in section.paragraphs" :key="paragraph">{{ paragraph }}</p>
      <ul v-if="section.items">
        <li v-for="item in section.items" :key="item">{{ item }}</li>
      </ul>
    </section>

    <!-- Действия страницы (форма удаления аккаунта) -->
    <slot />
  </article>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.legal-page {
  max-width: 720px;
  margin: 0 auto;
  padding: calc(20px + var(--sat)) 16px calc(40px + var(--sab));
  color: $navy;
  line-height: 1.6;
}

.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.back-btn {
  @include ghost-button;
  font-size: 14px;
}

h1 {
  margin: 0 0 4px;
  font-size: 26px;
  font-weight: 700;
  line-height: 1.25;
}

.updated {
  margin: 0 0 16px;
  font-size: 13px;
  color: $text-muted;
}

.intro {
  margin: 0 0 8px;
  font-size: 15px;
  color: $text-secondary;
}

.section {
  margin-top: 24px;

  h2 {
    @include section-title;
    margin-bottom: 8px;
  }

  p {
    margin: 0 0 8px;
    font-size: 14px;
  }

  ul {
    margin: 0;
    padding-left: 20px;
    font-size: 14px;
  }

  li + li {
    margin-top: 6px;
  }
}
</style>
