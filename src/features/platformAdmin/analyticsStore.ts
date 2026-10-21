// src/features/platformAdmin/analyticsStore.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from './api.ts'
import type {
  AuditEventAdmin,
  AuditFilters,
  FundHealth,
  FundHealthFilters,
  PlatformOverview,
  PlatformPlans,
  UserAdmin,
  UserDetailAdmin,
  UserFilter,
} from './types.ts'

/** Аналитика админа платформы: сводка, тарифы, здоровье фондов, пользователи, журнал. Только чтение. */
export const useAnalyticsStore = defineStore('platformAnalytics', () => {
  // ── State ─────────────────────────────────────────────────────────────
  const overview = ref<PlatformOverview | null>(null)
  const plans = ref<PlatformPlans | null>(null)

  const funds = ref<FundHealth[]>([])
  const fundsTotal = ref(0)
  const fundFilters = ref<FundHealthFilters>({ q: '', plan: null, inactive: false, sort: 'created' })

  const users = ref<UserAdmin[]>([])
  const usersTotal = ref(0)
  const userQuery = ref('')
  const userFilter = ref<UserFilter>('all')
  const userDetail = ref<UserDetailAdmin | null>(null)

  const audit = ref<AuditEventAdmin[]>([])
  const auditHasMore = ref(false)
  const auditFilters = ref<AuditFilters>({ fund_id: null, fund_name: null, entity: null })

  const isLoading = ref(false)
  const isLoadingMore = ref(false)

  // ── Actions ───────────────────────────────────────────────────────────
  async function load<T>(action: () => Promise<T>, more = false): Promise<T> {
    const flag = more ? isLoadingMore : isLoading
    flag.value = true
    try {
      return await action()
    } finally {
      flag.value = false
    }
  }

  const fetchOverview = () =>
    load(async () => {
      const [overviewRes, plansRes] = await Promise.all([api.getOverview(), api.getPlansStats()])
      overview.value = overviewRes.data
      plans.value = plansRes.data
    })

  const fetchFunds = (more = false) =>
    load(async () => {
      const { data } = await api.listFundHealth(fundFilters.value, more ? funds.value.length : 0)
      funds.value = more ? [...funds.value, ...data.items] : data.items
      fundsTotal.value = data.total
    }, more)

  const fetchUsers = (more = false) =>
    load(async () => {
      const { data } = await api.listUsers(userQuery.value, userFilter.value, more ? users.value.length : 0)
      users.value = more ? [...users.value, ...data.items] : data.items
      usersTotal.value = data.total
    }, more)

  async function openUser(id: number) {
    const { data } = await api.getUser(id)
    userDetail.value = data
  }

  const fetchAudit = (more = false) =>
    load(async () => {
      const { data } = await api.listAudit(auditFilters.value, more ? audit.value.length : 0)
      audit.value = more ? [...audit.value, ...data] : data
      auditHasMore.value = data.length === api.PAGE_SIZE
    }, more)

  return {
    overview,
    plans,
    funds,
    fundsTotal,
    fundFilters,
    users,
    usersTotal,
    userQuery,
    userFilter,
    userDetail,
    audit,
    auditHasMore,
    auditFilters,
    isLoading,
    isLoadingMore,
    fetchOverview,
    fetchFunds,
    fetchUsers,
    openUser,
    fetchAudit,
  }
})
