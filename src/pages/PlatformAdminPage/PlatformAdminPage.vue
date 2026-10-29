<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useFundsStore } from '@/features/funds/store.ts'
import { useAnalyticsStore } from '@/features/platformAdmin/analyticsStore.ts'
import AuditPanel from '@/features/platformAdmin/components/AuditPanel.vue'
import FundsHealthPanel from '@/features/platformAdmin/components/FundsHealthPanel.vue'
import NoticeComposer from '@/features/platformAdmin/components/NoticeComposer.vue'
import OverviewPanel from '@/features/platformAdmin/components/OverviewPanel.vue'
import PlanRequestCard from '@/features/platformAdmin/components/PlanRequestCard.vue'
import PlansPanel from '@/features/platformAdmin/components/PlansPanel.vue'
import UsersPanel from '@/features/platformAdmin/components/UsersPanel.vue'
import * as platformApi from '@/features/platformAdmin/api.ts'
import { usePlatformAdminStore } from '@/features/platformAdmin/store.ts'
import type { NoticeAdmin } from '@/features/notices/types.ts'
import type {
  FundCouncilMember,
  FundHealth,
  PlanApprove,
  PlanRequest,
  PlatformTab,
  UserAdmin,
} from '@/features/platformAdmin/types.ts'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import PillTabs from '@/shared/components/PillTabs.vue'
import { errorMessage } from '@/shared/api/errors.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import { useNavStore } from '@/shared/stores/useNavStore.ts'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const store = usePlatformAdminStore()
const analytics = useAnalyticsStore()
const fundsStore = useFundsStore()
const headerStore = useHeaderStore()
const navStore = useNavStore()

// ?tab=requests — ссылка из уведомления в Telegram о новой заявке
const PLATFORM_TABS: PlatformTab[] = ['overview', 'plans', 'requests', 'funds', 'users', 'audit']
const queryTab = route.query.tab as PlatformTab
const view = ref<PlatformTab>(PLATFORM_TABS.includes(queryTab) ? queryTab : 'overview')
const tabs = computed(() => [
  { value: 'overview' as PlatformTab, label: t('platform.tabs.overview') },
  { value: 'plans' as PlatformTab, label: t('platform.tabs.plans') },
  { value: 'requests' as PlatformTab, label: t('platform.tabs.requests'), badge: store.pendingRequests.length },
  { value: 'funds' as PlatformTab, label: t('platform.tabs.funds') },
  { value: 'users' as PlatformTab, label: t('platform.tabs.users') },
  { value: 'audit' as PlatformTab, label: t('platform.tabs.audit') },
])

// Совет с контактами — из списка фондов админа (до 100 фондов)
const councils = computed<Record<number, FundCouncilMember[]>>(() =>
  Object.fromEntries(store.funds.map((f) => [f.id, f.council])),
)

onMounted(async () => {
  headerStore.setTitle(t('platform.title'))
  headerStore.setLeftAction(() => router.push(fundsStore.current ? '/' : '/funds'))
  navStore.hideTabs()
  await Promise.all([safely(store.fetchAll), safely(analytics.fetchOverview)])
})

onUnmounted(() => {
  headerStore.reset()
  navStore.showTabs()
})

// Списки грузятся при первом открытии вкладки
const loaded = new Set<PlatformTab>()
watch(view, (tab) => {
  if (loaded.has(tab)) return
  loaded.add(tab)
  if (tab === 'funds') void safely(analytics.fetchFunds)
  if (tab === 'users') void safely(analytics.fetchUsers)
  if (tab === 'audit') void safely(analytics.fetchAudit)
}, { immediate: true })

async function safely(action: () => Promise<unknown>) {
  try {
    await action()
  } catch (error) {
    headerStore.showNotification(errorMessage(error, 'errors.loadFailed'), 'error')
  }
}

// ── Handlers ─────────────────────────────────────────────────────────────
async function handleApprove(request: PlanRequest, payload: PlanApprove) {
  try {
    await store.approve(request.id, payload)
    headerStore.showNotification(t('platform.approved'))
    void safely(analytics.fetchOverview)
  } catch (error) {
    headerStore.showNotification(errorMessage(error), 'error')
  }
}

async function handleReject(request: PlanRequest, comment: string) {
  try {
    await store.reject(request.id, comment)
    headerStore.showNotification(t('platform.rejected'))
    void safely(analytics.fetchOverview)
  } catch (error) {
    headerStore.showNotification(errorMessage(error), 'error')
  }
}

function goTo(tab: PlatformTab) {
  // Из «ждут решения» — фонды с самой длинной очередью сверху
  if (tab === 'funds' && analytics.fundFilters.sort !== 'pending') {
    analytics.fundFilters = { ...analytics.fundFilters, sort: 'pending' }
    if (loaded.has('funds')) void safely(analytics.fetchFunds)
  }
  view.value = tab
}

function openFundAudit(fund: FundHealth) {
  analytics.auditFilters = { ...analytics.auditFilters, fund_id: fund.id, fund_name: fund.name }
  if (loaded.has('audit')) void safely(analytics.fetchAudit)
  view.value = 'audit'
}

const openUser = (user: UserAdmin) => safely(() => analytics.openUser(user.id))

// ── Уведомление совету фонда ─────────────────────────────────────────────
const notifyFund = ref<FundHealth | null>(null)
const sentNotices = ref<NoticeAdmin[]>([])
const isSending = ref(false)

async function openNotify(fund: FundHealth) {
  notifyFund.value = fund
  sentNotices.value = []
  await safely(async () => {
    const { data } = await platformApi.listSentNotices(fund.id)
    if (notifyFund.value?.id === fund.id) sentNotices.value = data
  })
}

async function sendNotice(text: string) {
  const fund = notifyFund.value
  if (!fund) return
  isSending.value = true
  try {
    await platformApi.sendNotice(fund.id, text)
    headerStore.showNotification(t('platform.notify.done'))
    notifyFund.value = null
  } catch (error) {
    headerStore.showNotification(errorMessage(error), 'error')
  } finally {
    isSending.value = false
  }
}
</script>

<template>
  <div class="platform-page">
    <PillTabs v-model="view" :options="tabs" />

    <Transition name="slide" mode="out-in">
      <!-- 1. Обзор -->
      <section v-if="view === 'overview'" key="overview" class="section">
        <OverviewPanel v-if="analytics.overview" :overview="analytics.overview" @go="goTo" />
        <template v-else>
          <CardSkeleton v-for="i in 3" :key="i" :lines="3" />
        </template>
      </section>

      <!-- 2. Тарифы и выручка -->
      <section v-else-if="view === 'plans'" key="plans" class="section">
        <PlansPanel v-if="analytics.plans" :plans="analytics.plans" @go="goTo" />
        <template v-else>
          <CardSkeleton v-for="i in 3" :key="i" :lines="3" />
        </template>
      </section>

      <!-- 3. Заявки на тарифы -->
      <section v-else-if="view === 'requests'" key="requests" class="section">
        <template v-if="store.isLoading && !store.requests.length">
          <CardSkeleton v-for="i in 2" :key="i" :lines="3" />
        </template>
        <template v-else>
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
        </template>
      </section>

      <!-- 4. Фонды: поиск и здоровье -->
      <section v-else-if="view === 'funds'" key="funds" class="section">
        <FundsHealthPanel
          v-model:filters="analytics.fundFilters"
          :class="{ refetching: analytics.isLoading }"
          :funds="analytics.funds"
          :total="analytics.fundsTotal"
          :councils="councils"
          :is-loading-more="analytics.isLoadingMore"
          @change="safely(analytics.fetchFunds)"
          @more="safely(() => analytics.fetchFunds(true))"
          @audit="openFundAudit"
          @notify="openNotify"
        />
      </section>

      <!-- 5. Пользователи -->
      <section v-else-if="view === 'users'" key="users" class="section">
        <UsersPanel
          v-model:query="analytics.userQuery"
          v-model:filter="analytics.userFilter"
          :class="{ refetching: analytics.isLoading }"
          :users="analytics.users"
          :total="analytics.usersTotal"
          :detail="analytics.userDetail"
          :is-loading-more="analytics.isLoadingMore"
          @change="safely(analytics.fetchUsers)"
          @more="safely(() => analytics.fetchUsers(true))"
          @open="openUser"
          @close="analytics.userDetail = null"
        />
      </section>

      <!-- 6. Журнал действий -->
      <section v-else key="audit" class="section">
        <AuditPanel
          v-model:filters="analytics.auditFilters"
          :class="{ refetching: analytics.isLoading }"
          :events="analytics.audit"
          :has-more="analytics.auditHasMore"
          :is-loading-more="analytics.isLoadingMore"
          @change="safely(analytics.fetchAudit)"
          @more="safely(() => analytics.fetchAudit(true))"
        />
      </section>
    </Transition>

    <NoticeComposer
      :open="!!notifyFund"
      :fund-name="notifyFund?.name ?? ''"
      :sent="sentNotices"
      :is-submitting="isSending"
      @close="notifyFund = null"
      @send="sendNotice"
    />
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

// Перезагрузка по фильтру: прежний список остаётся, но приглушён
.refetching {
  opacity: 0.55;
  transition: opacity 0.2s ease;
}
</style>
