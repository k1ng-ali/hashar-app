// src/app/native.ts
import { Capacitor } from '@capacitor/core'
import type { Router } from 'vue-router'

/**
 * Поведение Android-приложения (Capacitor). В браузере ничего не делает,
 * плагины грузятся только в приложении.
 */
export async function setupNative(router: Router) {
  if (!Capacitor.isNativePlatform()) return

  const [{ App }, { SplashScreen }] = await Promise.all([import('@capacitor/app'), import('@capacitor/splash-screen')])

  // Системная «Назад»: шаг назад по истории, на первом экране — свернуть приложение
  // (как в обычных Android-приложениях; без обработчика Activity просто закрывается)
  await App.addListener('backButton', ({ canGoBack }) => {
    if (canGoBack) router.back()
    else void App.minimizeApp()
  })

  // Сплэш висит, пока не отрисован первый экран (capacitor.config.ts → launchAutoHide: false).
  // Первый переход ждёт проверку входа — без сети это до таймаута запроса, поэтому не дольше SPLASH_MAX_MS
  const timeout = new Promise((resolve) => setTimeout(resolve, SPLASH_MAX_MS))
  await Promise.race([router.isReady().catch(() => undefined), timeout])
  await SplashScreen.hide()
}

const SPLASH_MAX_MS = 4000
