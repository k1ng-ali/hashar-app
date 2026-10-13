import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/features/auth/store.ts'
import { useFundsStore } from '@/features/funds/store.ts'

const LoginPage = () => import('@/pages/LoginPage/LoginPage.vue')
const FundsPage = () => import('@/pages/FundsPage/FundsPage.vue')
const JoinPage = () => import('@/pages/JoinPage/JoinPage.vue')
const DashboardPage = () => import('@/pages/DashboardPage/DashboardPage.vue')
const ContributePage = () => import('@/pages/ContributePage/ContributePage.vue')
const FinancePage = () => import('@/pages/FinancePage/FinancePage.vue')
const HistoryPage = () => import('@/pages/HistoryPage/HistoryPage.vue')
const ExpensesPage = () => import('@/pages/ExpensesPage/ExpensesPage.vue')
const TargetFundsPage = () => import('@/pages/TargetFundsPage/TargetFundsPage.vue')
const ReportsPage = () => import('@/pages/ReportsPage/ReportsPage.vue')
const TargetFundPage = () => import('@/pages/TargetFundPage/TargetFundPage.vue')
const AnnouncementsPage = () => import('@/pages/AnnouncementsPage/AnnouncementsPage.vue')
const FundPage = () => import('@/pages/FundPage/FundPage.vue')
const FundReceiptsPage = () => import('@/pages/FundReceiptsPage/FundReceiptsPage.vue')
const FundMembersPage = () => import('@/pages/FundMembersPage/FundMembersPage.vue')
const FundAccountsPage = () => import('@/pages/FundAccountsPage/FundAccountsPage.vue')
const FundSettingsPage = () => import('@/pages/FundSettingsPage/FundSettingsPage.vue')
const PlatformAdminPage = () => import('@/pages/PlatformAdminPage/PlatformAdminPage.vue')
const PrivacyPage = () => import('@/pages/PrivacyPage/PrivacyPage.vue')
const AccountDeletionPage = () => import('@/pages/AccountDeletionPage/AccountDeletionPage.vue')

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean // доступно без входа
    fund?: boolean // нужен выбранный фонд с активным членством
    council?: boolean // только совет фонда
    platformAdmin?: boolean // только админ платформы
  }
}

// Вкладки старой страницы «Админ» → новые экраны
const LEGACY_ADMIN_TABS: Record<string, string> = {
  verification: '/fund/receipts',
  members: '/fund/members',
  expenses: '/finance/expenses',
  funds: '/finance/funds',
  accounts: '/fund/accounts',
  settings: '/fund/settings',
}

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/login', component: LoginPage, meta: { public: true } },
    // Документы — открываются и без входа (ссылки на них указаны в Google Play)
    { path: '/privacy', component: PrivacyPage, meta: { public: true } },
    { path: '/account-deletion', component: AccountDeletionPage, meta: { public: true } },
    { path: '/funds', component: FundsPage },
    { path: '/join/:code', component: JoinPage },
    { path: '/platform', component: PlatformAdminPage, meta: { platformAdmin: true } },
    { path: '/', component: DashboardPage, meta: { fund: true } },
    { path: '/contribute', component: ContributePage, meta: { fund: true } },

    // Финансы: мои взносы, расходы, сборы, отчёты — видят все участники
    {
      path: '/finance',
      component: FinancePage,
      meta: { fund: true },
      children: [
        { path: '', redirect: '/finance/my' },
        { path: 'my', component: HistoryPage, meta: { fund: true } },
        { path: 'expenses', component: ExpensesPage, meta: { fund: true } },
        { path: 'funds', component: TargetFundsPage, meta: { fund: true } },
        { path: 'reports', component: ReportsPage, meta: { fund: true } },
      ],
    },
    { path: '/target-funds/:id', component: TargetFundPage, meta: { fund: true } },
    { path: '/news', component: AnnouncementsPage, meta: { fund: true } },

    // Фонд: карточка для всех, управление — совету
    { path: '/fund', component: FundPage, meta: { fund: true } },
    { path: '/fund/receipts', component: FundReceiptsPage, meta: { fund: true, council: true } },
    { path: '/fund/members', component: FundMembersPage, meta: { fund: true, council: true } },
    { path: '/fund/accounts', component: FundAccountsPage, meta: { fund: true, council: true } },
    { path: '/fund/settings', component: FundSettingsPage, meta: { fund: true, council: true } },

    // Старые адреса (закладки, ссылки в сообщениях)
    { path: '/history', redirect: '/finance/my' },
    { path: '/expenses', redirect: (to) => ({ path: '/finance/expenses', query: to.query }) },
    { path: '/reports', redirect: '/finance/reports' },
    { path: '/admin', redirect: (to) => LEGACY_ADMIN_TABS[String(to.query.tab)] ?? '/fund' },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  // Дожидаемся восстановления сессии по refresh-cookie
  await auth.bootstrap()

  if (to.meta.public) {
    return to.path === '/login' && auth.isAuthenticated ? { path: '/' } : true
  }
  if (!auth.isAuthenticated) {
    // Сохраняем цель (например, ссылку-приглашение), чтобы вернуться после входа
    return { path: '/login', query: to.fullPath !== '/' ? { redirect: to.fullPath } : undefined }
  }

  if (to.meta.platformAdmin && !auth.isPlatformAdmin) return { path: '/' }

  const funds = useFundsStore()
  if (!funds.isLoaded) await funds.restore()

  if (to.meta.fund && !funds.current) {
    // Нет ни одного фонда — на экран «создать или найти фонд»
    return { path: '/funds' }
  }
  if (to.meta.council && !funds.permissions.isCouncil) return { path: '/' }
  return true
})
