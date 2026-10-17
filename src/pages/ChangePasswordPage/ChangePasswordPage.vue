<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/features/auth/store.ts'
import VerificationStep from '@/features/auth/components/VerificationStep.vue'
import { errorDetail } from '@/shared/api/http.ts'

// Смена (или первая установка) пароля — только после повторного подтверждения личности
const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const errorMessage = ref('')

onMounted(async () => {
  try {
    await authStore.startPasswordChange()
  } catch (error) {
    errorMessage.value =
      errorDetail(error) === 'Verification is unavailable' ? t('auth.verify.unavailable') : t('errors.generic')
  }
})

// Ушли со страницы, не подтвердив, — challenge не должен всплыть на странице входа
onBeforeUnmount(() => authStore.cancelChallenge())

function goBack() {
  if (window.history.state?.back) router.back()
  else void router.replace('/')
}

async function handleDone() {
  message.success(t('auth.verify.passwordChanged'))
  await router.replace('/')
}
</script>

<template>
  <div class="password-page">
    <div class="card">
      <VerificationStep
        v-if="authStore.challenge"
        :key="authStore.challenge.challenge"
        :challenge="authStore.challenge"
        @done="handleDone"
        @cancel="goBack"
      />
      <template v-else-if="errorMessage">
        <p class="error">{{ errorMessage }}</p>
        <button type="button" class="back-btn" @click="goBack">← {{ $t('auth.verify.back') }}</button>
      </template>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.password-page {
  max-width: 460px;
  margin: 0 auto;
  padding: 16px;
}

.card {
  @include glass-card(24px);
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px;
}

.error {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: $danger;
}

.back-btn {
  align-self: flex-start;
  padding: 0;
  border: none;
  background: none;
  font-size: 13px;
  font-weight: 600;
  color: $text-secondary;
  cursor: pointer;
}
</style>
