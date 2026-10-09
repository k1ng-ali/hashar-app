<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useFundsStore } from '@/features/funds/store.ts'
import PlanRequestCard from '@/features/platformAdmin/components/PlanRequestCard.vue'
import { usePlatformAdminStore } from '@/features/platformAdmin/store.ts'
import type { PlanApprove, PlanRequest, PlatformTab } from '@/features/platformAdmin/types.ts'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import PillTabs from '@/shared/components/PillTabs.vue'
import { errorDetail } from '@/shared/api/http.ts'
import { formatDate } from '@/shared/lib/format.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import { useNavStore } from '@/shared/stores/useNavStore.ts'

const { t } = useI18n()
const router = useRouter()
const store = usePlatformAdminStore()
const fundsStore = useFundsStore()
const headerStore = useHeaderStore()
const navStore = useNavStore()

const view = ref<PlatformTab>('requests')
const tabs = computed(() => [
  { value: 'requests' as PlatformTab, label: t('platform.tabs.requests'), badge: store.pendingRequests.length },
  { value: 'funds' as PlatformTab, label: t('platform.tabs.funds') },
])

onMounted(async () => {
  headerStore.setTitle(t('platform.title'))
  headerStore.setLeftAction(() => router.push(fundsStore.current ? '/' : '/funds'))
  navStore.hideTabs()
  await store.fetchAll()
})

onUnmounted(() => {
  headerStore.reset()
  navStore.showTabs()
})

// ── Handlers ─────────────────────────────────────────────────────────────
async function handleApprove(request: PlanRequest, payload: PlanApprove) {
  try {
    await store.approve(request.id, payload)
    headerStore.showNotification(t('platform.approved'))
  } catch (error) {
    headerStore.showNotification(errorDetail(error) ?? t('errors.generic'), 'error')
  }
}

async function handleReject(request: PlanRequest, comment: string) {
  try {
    await store.reject(request.id, comment)
    headerStore.showNotification(t('platform.rejected'))
  } catch (error) {
    headerStore.showNotification(errorDetail(error) ?? t('errors.generic'), 'error')
  }
}
</script>

<template>
  <div class="platform-page">
    <PillTabs v-model="view" :options="tabs" />

    <template v-if="store.isLoading && !store.requests.length">
      <CardSkeleton v-for="i in 2" :key="i" :lines="3" />
    </template>

    <Transition v-else name="slide" mode="out-in">
      <!-- 1. Заявки на тарифы -->
      <section v-if="view === 'requests'" key="requests" class="section">
        <div v-if="store.pendingRequests.length" class="list">
          <PlanRequestCard
            v-for="request in store.pendingRequests"
            :key="request.id"
            :request="request"
            :is-submitting="store.isSubmitting"
            @approve="handleApprove"
            @reject="handleReject"
          />
        </div>
        <EmptyState v-else icon="✅" :title="$t('platform.noPending')" />

        <template v-if="store.reviewedRequests.length">
          <h2 class="section-title">{{ $t('platform.history') }}</h2>
          <div class="list">
            <PlanRequestCard
              v-for="request in store.reviewedRequests"
              :key="request.id"
              :request="request"
              :is-submitting="store.isSubmitting"
            />
          </div>
        </template>
      </section>

      <!-- 2. Все фонды -->
      <section v-else key="funds" class="section">
        <div class="list">
          <div v-for="fund in store.funds" :key="fund.id" class="fund">
            <div>
              <b>{{ fund.name }}</b>
              <span class="meta">{{ fund.code }} · {{ $t('funds.membersCount', { n: fund.members_count }) }}</span>
            </div>
            <div class="plan">
              <span class="badge">{{ $t(`plans.${fund.effective_plan}`) }}</span>
              <span v-if="fund.plan_expires_at" class="meta">
                {{ $t('plans.until', { date: formatDate(fund.plan_expires_at) }) }}
              </span>
            </div>
          </div>
        </div>
      </section>
    </Transition>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.platform-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 720px;
  margin: 0 auto;
  padding: 16px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  @include section-title;
  font-size: 16px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.fund {
  @include glass-card(16px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;

  b {
    display: block;
    color: $navy;
  }
}

.plan {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.meta {
  font-size: 12px;
  color: $text-muted;
}

.badge {
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(78, 190, 194, 0.16);
  color: #0E7C80;
  font-size: 12px;
  font-weight: 700;
}
</style>
