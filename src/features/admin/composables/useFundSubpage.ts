import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'

/** Экран внутри раздела «Фонд»: заголовок в шапке и «назад» к меню фонда. */
export function useFundSubpage(titleKey: string, load: () => Promise<unknown>) {
  const { t } = useI18n()
  const router = useRouter()
  const headerStore = useHeaderStore()

  onMounted(() => {
    headerStore.setTitle(t(titleKey))
    headerStore.setLeftAction(() => router.push('/fund'))
    void load()
  })

  onUnmounted(() => {
    headerStore.reset()
  })
}
