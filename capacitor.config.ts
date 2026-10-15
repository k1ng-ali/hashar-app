import type { CapacitorConfig } from '@capacitor/cli'

// Android-приложение: та же Vue-сборка (dist/), упакованная в WebView.
// Сборка и публикация — README.md → «Android».
const config: CapacitorConfig = {
  appId: 'com.hashar.app',
  appName: 'Hashar',
  webDir: 'dist',
  server: {
    // Приложение открывается как https://hashar.app — тот же origin, что у сайта на GitHub Pages.
    // Поэтому API принимает его без отдельной настройки CORS, а refresh-cookie от api.hashar.app
    // (SameSite=Lax) остаётся «своей», то есть тот же сайт. Файлы при этом берутся из APK, не из сети.
    hostname: 'hashar.app',
    androidScheme: 'https',
  },
  plugins: {
    SocialLogin: {
      // Вход через Google (Credential Manager); остальные провайдеры не попадают в APK
      providers: { google: true, facebook: false, apple: false, twitter: false },
    },
    SplashScreen: {
      // Сплэш прячет src/app/native.ts, когда отрисован первый экран — без белой вспышки
      launchAutoHide: false,
      launchFadeOutDuration: 200,
    },
    SystemBars: {
      // Светлые панели — тёмные значки статус-бара (интерфейс у приложения светлый)
      style: 'LIGHT',
      // index.html уже с viewport-fit=cover, отступы — через env(safe-area-inset-*) в style.css
      initialViewportFitValueHint: 'cover',
    },
  },
}

export default config
