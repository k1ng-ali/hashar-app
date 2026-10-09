<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import JoinForm from '@/features/funds/components/JoinForm.vue'
import { useFundsStore } from '@/features/funds/store.ts'
import type { FundPublic, JoinPayload } from '@/features/funds/types.ts'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import { errorDetail } from '@/shared/api/http.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import { useNavStore } from '@/shared/stores/useNavStore.ts'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const store = useFundsStore()
const headerStore = useHeaderStore()
const navStore = useNavStore()

const fund = ref<FundPublic | null>(null)
const isLoading = ref(true)

onMounted(async () => {
  headerStore.setTitle(t('funds.join.title'))
  headerStore.setLeftAction(() => router.push('/funds'))
  navStore.hideTabs()
  try {
    fund.value = await store.findByCode(String(route.params.code))
  } catch {
    fund.value = null
  } finally {
    isLoading.value = false
  }
})

onUnmounted(() => {
  headerStore.reset()
  navStore.showTabs()
})

// ── Handlers ─────────────────────────────────────────────────────────────
async function handleSubmit(payload: JoinPayload) {
  if (!fund.value) return
  try {
    await store.join(fund.value.id, payload)
    headerStore.showNotification(t('funds.join.sent'))
    await router.replace('/funds')
  } catch (error) {
    headerStore.showNotification(errorDetail(error) ?? t('errors.generic'), 'error')
  }
}

async function openFund() {
  if (!fund.value) return
  await store.select(fund.value.id)
  await router.replace('/')
}
</script>

<template>
  <div class="join-page">
    <CardSkeleton v-if="isLoading" :lines="4" />

    <EmptyState v-else-if="!fund" icon="🔍" :title="$t('funds.join.notFound')">
      <button class="ghost-btn" @click="router.push('/funds')">{{ $t('funds.title') }}</button>
    </EmptyState>

    <!-- Уже участник -->
    <EmptyState v-else-if="fund.my_status === 'active'" icon="✅" :title="$t('funds.join.alreadyMember')">
      <button class="cta-btn" @click="openFund">{{ $t('funds.join.open') }}</button>
    </EmptyState>

    <!-- Заявка уже подана -->
    <EmptyState v-else-if="fund.my_status === 'pending'" icon="⏱" :title="$t('funds.join.pending')" />

    <EmptyState v-else-if="fund.my_status === 'blocked'" icon="🚫" :title="$t('memberStatus.blocked')" />

    <div v-else class="card">
      <JoinForm :fund="fund" :is-submitting="store.isSubmitting" @submit="handleSubmit" />
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.join-page {
  max-width: 520px;
  margin: 0 auto;
  padding: 16px;
}

.card {
  @include glass-card(24px);
  padding: 18px;
}

.ghost-btn {
  @include ghost-button;
}

.cta-btn {
  @include cta-button;
}
</style>
