<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ContributionForm from '@/features/contributions/components/ContributionForm.vue'
import { useContributionForm } from '@/features/contributions/composables/useContributionForm.ts'
import { useContributionsStore } from '@/features/contributions/store.ts'
import { useDashboardStore } from '@/features/dashboard/store.ts'
import { useTargetFundsStore } from '@/features/targetFunds/store.ts'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import { errorDetail } from '@/shared/api/http.ts'
import { copyText } from '@/shared/lib/browser.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import { useNavStore } from '@/shared/stores/useNavStore.ts'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const dashboardStore = useDashboardStore()
const targetFundsStore = useTargetFundsStore()
const contributionsStore = useContributionsStore()
const headerStore = useHeaderStore()
const navStore = useNavStore()
const form = useContributionForm()

const isReady = ref(false)

onMounted(async () => {
  headerStore.setTitle(t('contribution.title'))
  // Если страницу открыли по прямой ссылке — «назад» ведёт на главную
  headerStore.setLeftAction(() => (window.history.state?.back ? router.back() : router.push('/')))
  navStore.hideTabs()

  await Promise.all([
    dashboardStore.fetchRequisites(),
    targetFundsStore.fetchList(),
    contributionsStore.fetchBalance(),
  ]).catch(() => undefined)

  form.init(Number(route.query.fund) || null)
  isReady.value = true
})

onUnmounted(() => {
  headerStore.reset()
  navStore.showTabs()
})

// ── Handlers ─────────────────────────────────────────────────────────────
async function handleCopy(value: string) {
  if (await copyText(value)) headerStore.showNotification(t('requisites.copied'))
}

function handleGenerate() {
  form.generateDemoReceipt()
  headerStore.showNotification(t('receipt.generated'))
}

async function handleSubmit() {
  try {
    const created = await form.submit()
    if (!created) return
    headerStore.showNotification(t('contribution.success'))
    // Обновляем счётчик чеков на проверке (бейдж «Админ» в навигации)
    void dashboardStore.fetchSummary()
    await router.replace('/finance/my')
  } catch (error) {
    headerStore.showNotification(errorDetail(error) ?? t('contribution.error'), 'error', 3000)
  }
}
</script>

<template>
  <div class="contribute-page">
    <p class="subtitle">{{ $t('contribution.subtitle') }}</p>

    <!-- Шаги -->
    <div class="steps">
      <span class="step"><b>1</b>{{ $t('contribution.steps.copy') }}</span>
      <span class="step"><b>2</b>{{ $t('contribution.steps.transfer') }}</span>
      <span class="step"><b>3</b>{{ $t('contribution.steps.upload') }}</span>
    </div>

    <CardSkeleton v-if="!isReady" :lines="6" />
    <div v-else class="form-card">
      <ContributionForm
        v-model:category="form.category.value"
        v-model:target-fund-id="form.targetFundId.value"
        v-model:requisite-id="form.requisiteId.value"
        v-model:amount="form.amount.value"
        v-model:credited-amount="form.creditedAmount.value"
        v-model:receipt="form.receipt.value"
        v-model:comment="form.comment.value"
        :rate="form.rate.value"
        :base-currency="form.baseCurrency.value"
        :currency="form.currency.value"
        :required-currency="form.requiredCurrency.value"
        :needs-credit="form.needsCredit.value"
        :funds="targetFundsStore.activeItems"
        :requisites="form.availableRequisites.value"
        :presets="form.presets.value"
        :debt-amount="form.debtAmount.value"
        :validation-error="form.validationError.value"
        :is-submitting="contributionsStore.isSubmitting"
        @generate="handleGenerate"
        @copy="handleCopy"
        @submit="handleSubmit"
      />
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.contribute-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 640px;
  margin: 0 auto;
  padding: 16px;
}

.subtitle {
  margin: 0;
  font-size: 14px;
  color: $text-secondary;
}

/* ── Шаги ─────────────────────────────────────────────────────────────────── */
.steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.step {
  @include glass-card(14px);
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px;
  font-size: 11px;
  font-weight: 600;
  color: $navy;

  b {
    display: grid;
    place-items: center;
    flex-shrink: 0;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: $gradient;
    color: #fff;
    font-size: 11px;
  }
}

.form-card {
  @include glass-card(24px);
  padding: 18px;
}

@media (min-width: 768px) {
  .contribute-page {
    padding: 24px;
  }
}
</style>
