import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/features/auth/store.ts'
import { useFundsStore } from '@/features/funds/store.ts'

const LoginPage = () => import('@/pages/LoginPage/LoginPage.vue')
const FundsPage = () => import('@/pages/FundsPage/FundsPage.vue')
const JoinPage = () => import('@/pages/JoinPage/JoinPage.vue')
const DashboardPage = () => import('@/pages/DashboardPage/DashboardPage.vue')
const ContributePage = () => import('@/pages/ContributePage/ContributePage.vue')
const HistoryPage = () => import('@/pages/HistoryPage/HistoryPage.vue')
const TargetFundPage = () => import('@/pages/TargetFundPage/TargetFundPage.vue')
const AnnouncementsPage = () => import('@/pages/AnnouncementsPage/AnnouncementsPage.vue')
const ReportsPage = () => import('@/pages/ReportsPage/ReportsPage.vue')
const AdminPage = () => import('@/pages/AdminPage/AdminPage.vue')
const PlatformAdminPage = () => import('@/pages/PlatformAdminPage/PlatformAdminPage.vue')

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean // доступно без входа
    fund?: boolean // нужен выбранный фонд с активным членством
    council?: boolean // только совет фонда
    platformAdmin?: boolean // только админ платформы
  }
}

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/login', component: LoginPage, meta: { public: true } },
    { path: '/funds', component: FundsPage },
    { path: '/join/:code', component: JoinPage },
    { path: '/platform', component: PlatformAdminPage, meta: { platformAdmin: true } },
    { path: '/', component: DashboardPage, meta: { fund: true } },
    { path: '/contribute', component: ContributePage, meta: { fund: true } },
    { path: '/history', component: HistoryPage, meta: { fund: true } },
    { path: '/target-funds/:id', component: TargetFundPage, meta: { fund: true } },
    { path: '/news', component: AnnouncementsPage, meta: { fund: true } },
    { path: '/reports', component: ReportsPage, meta: { fund: true } },
    { path: '/admin', component: AdminPage, meta: { fund: true, council: true } },
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
