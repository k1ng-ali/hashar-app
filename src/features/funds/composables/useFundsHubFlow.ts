import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { errorDetail } from '@/shared/api/http.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import { useNavStore } from '@/shared/stores/useNavStore.ts'
import { useFundsStore } from '../store.ts'
import type { FundCreate, FundPublic, JoinPayload, MyFund } from '../types.ts'

export type FundsHubView = 'list' | 'create' | 'find'

/** Экран «Мои фонды»: список, создание фонда, поиск и заявка на вступление. */
export function useFundsHubFlow() {
  const { t } = useI18n()
  const router = useRouter()
  const store = useFundsStore()
  const headerStore = useHeaderStore()
  const navStore = useNavStore()

  // ── View ──────────────────────────────────────────────────────────────
  // Без фондов сразу показываем «найти», чтобы не было пустого экрана
  const view = ref<FundsHubView>('list')
  const query = ref('')
  const joinTarget = ref<FundPublic | null>(null)
  let searchTimer: ReturnType<typeof setTimeout> | null = null

  const tabs = computed(() => [
    { value: 'list' as FundsHubView, label: t('funds.tabs.list'), badge: store.requests.filter((r) => r.status === 'pending').length },
    { value: 'find' as FundsHubView, label: t('funds.tabs.find') },
    { value: 'create' as FundsHubView, label: t('funds.tabs.create') },
  ])

  // ── Lifecycle ─────────────────────────────────────────────────────────
  async function initView() {
    headerStore.setTitle(t('funds.title'))
    // На главную вернуться можно, только если уже выбран фонд
    headerStore.setLeftAction(store.current ? () => router.push('/') : null)
    navStore.hideTabs()
    await store.fetchMy()
    if (!store.myFunds.length) view.value = 'find'
  }

  function dispose() {
    headerStore.reset()
    navStore.showTabs()
    if (searchTimer) clearTimeout(searchTimer)
  }

  // ── Handlers ──────────────────────────────────────────────────────────
  async function openFund(fund: MyFund) {
    await store.select(fund.id)
    await router.push('/')
  }

  async function cancelRequest(fund: MyFund) {
    await store.cancelJoin(fund.id)
    headerStore.showNotification(t('funds.requestCancelled'))
  }

  function onQueryInput(value: string) {
    query.value = value
    if (searchTimer) clearTimeout(searchTimer)
    // Небольшая задержка, чтобы не слать запрос на каждую букву
    searchTimer = setTimeout(() => void store.search(value), 300)
  }

  async function createFund(payload: FundCreate) {
    try {
      await store.create(payload)
      headerStore.showNotification(t('funds.create.success'))
      await router.push('/')
    } catch (error) {
      headerStore.showNotification(errorDetail(error) ?? t('errors.generic'), 'error')
    }
  }

  async function submitJoin(payload: JoinPayload) {
    if (!joinTarget.value) return
    try {
      await store.join(joinTarget.value.id, payload)
      joinTarget.value = null
      view.value = 'list'
      headerStore.showNotification(t('funds.join.sent'))
      void store.search(query.value)
    } catch (error) {
      headerStore.showNotification(errorDetail(error) ?? t('errors.generic'), 'error')
    }
  }

  return {
    view,
    tabs,
    query,
    joinTarget,
    initView,
    dispose,
    openFund,
    cancelRequest,
    onQueryInput,
    createFund,
    submitJoin,
  }
}
