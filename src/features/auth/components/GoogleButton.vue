<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { isNativeGoogle, nativeGoogleSignIn, renderGoogleButton } from '../google.ts'

/** Кнопка Google: вход на странице входа и подтверждение личности. Показывать только при isGoogleEnabled. */
defineProps<{
  disabled: boolean
}>()

const emit = defineEmits<{
  (e: 'token', idToken: string): void
  (e: 'error'): void
}>()

const { locale } = useI18n()

// На сайте кнопку рисует Google (во фрейме) в этот контейнер; в Android — своя кнопка
const googleSlot = ref<HTMLElement | null>(null)
const googleFailed = ref(false)

async function renderWebButton() {
  await nextTick()
  if (!googleSlot.value) return
  try {
    await renderGoogleButton(googleSlot.value, locale.value, (idToken) => emit('token', idToken))
    googleFailed.value = false
  } catch {
    // Скрипт Google не загрузился (нет сети, блокировщик) — показываем неактивную кнопку
    googleFailed.value = true
  }
}

async function handleNative() {
  try {
    const idToken = await nativeGoogleSignIn()
    if (idToken) emit('token', idToken)
  } catch {
    emit('error')
  }
}

onMounted(() => {
  if (!isNativeGoogle) void renderWebButton()
})
watch(locale, () => {
  if (!isNativeGoogle) void renderWebButton()
})
</script>

<template>
  <button v-if="isNativeGoogle" type="button" class="provider-btn" :disabled="disabled" @click="handleNative">
    <svg class="g-logo" viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
    </svg>
    {{ $t('auth.google') }}
  </button>
  <button v-else-if="googleFailed" type="button" class="provider-btn" disabled>{{ $t('auth.googleUnavailable') }}</button>
  <div v-else ref="googleSlot" class="google-slot" :class="{ 'google-slot--disabled': disabled }" />
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.google-slot {
  display: flex;
  justify-content: center;
  min-height: 44px;

  &--disabled {
    opacity: 0.6;
    pointer-events: none;
  }
}

.provider-btn {
  @include ghost-button;
  gap: 10px;
  padding: 12px;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.g-logo {
  width: 18px;
  height: 18px;
}
</style>
