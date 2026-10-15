// src/features/auth/google.ts
import { Capacitor } from '@capacitor/core'
import { GOOGLE_CLIENT_ID } from '@/shared/lib/env.ts'

/**
 * Вход через Google: получаем ID-токен, а проверяет его backend (/auth/google).
 *
 * - сайт — Google Identity Services: кнопку рисует сам Google (во фрейме), токен приходит в колбэк;
 * - Android — нативный Credential Manager (@capgo/capacitor-social-login): в WebView Google
 *   запрещает OAuth-окна, поэтому веб-кнопка там не работает.
 */

export const isGoogleEnabled = !!GOOGLE_CLIENT_ID
export const isNativeGoogle = Capacitor.isNativePlatform()

const GIS_SRC = 'https://accounts.google.com/gsi/client'
// Языки, которые понимает кнопка Google; таджикского нет — показываем русский
const GIS_LOCALES: Record<string, string> = { ru: 'ru', tg: 'ru', en: 'en' }

// ── Сайт: Google Identity Services ───────────────────────────────────────────

interface GsiButtonOptions {
  type: 'standard'
  theme: 'outline'
  size: 'large'
  shape: 'pill'
  text: 'continue_with'
  logo_alignment: 'center'
  width: number
  locale: string
}

interface GoogleAccountsId {
  initialize(config: { client_id: string; callback: (response: { credential: string }) => void }): void
  renderButton(parent: HTMLElement, options: GsiButtonOptions): void
}

declare global {
  interface Window {
    google?: { accounts: { id: GoogleAccountsId } }
  }
}

let gisPromise: Promise<GoogleAccountsId> | null = null
let onCredential: ((idToken: string) => void) | null = null

function loadGis(): Promise<GoogleAccountsId> {
  if (!gisPromise) {
    gisPromise = new Promise<GoogleAccountsId>((resolve, reject) => {
      const script = document.createElement('script')
      script.src = GIS_SRC
      script.async = true
      script.onload = () => {
        const gis = window.google?.accounts.id
        if (!gis) return reject(new Error('Google Identity Services did not load'))
        // initialize — один раз на страницу; колбэк ведёт в ту кнопку, что отрисована последней
        gis.initialize({ client_id: GOOGLE_CLIENT_ID, callback: ({ credential }) => onCredential?.(credential) })
        resolve(gis)
      }
      script.onerror = () => {
        gisPromise = null
        reject(new Error('Google Identity Services did not load'))
      }
      document.head.appendChild(script)
    })
  }
  return gisPromise
}

/** Рисует кнопку Google в parent; по выбору аккаунта вызывает onToken с ID-токеном. */
export async function renderGoogleButton(parent: HTMLElement, locale: string, onToken: (idToken: string) => void) {
  const gis = await loadGis()
  onCredential = onToken
  parent.replaceChildren()
  gis.renderButton(parent, {
    type: 'standard',
    theme: 'outline',
    size: 'large',
    shape: 'pill',
    text: 'continue_with',
    logo_alignment: 'center',
    // Google принимает ширину 200–400 px
    width: Math.min(400, Math.max(200, Math.floor(parent.clientWidth))),
    locale: GIS_LOCALES[locale] ?? 'ru',
  })
}

// ── Android: Credential Manager ──────────────────────────────────────────────

let nativeReady: Promise<void> | null = null

/** ID-токен из системного выбора аккаунта; null — пользователь закрыл окно. */
export async function nativeGoogleSignIn(): Promise<string | null> {
  const { SocialLogin } = await import('@capgo/capacitor-social-login')
  nativeReady ??= SocialLogin.initialize({ google: { webClientId: GOOGLE_CLIENT_ID } }).catch((error) => {
    nativeReady = null
    throw error
  })
  await nativeReady

  try {
    const { result } = await SocialLogin.login({ provider: 'google', options: { scopes: ['email', 'profile'] } })
    return 'idToken' in result ? result.idToken : null
  } catch (error) {
    if (/cancel/i.test(String((error as Error)?.message ?? error))) return null
    throw error
  }
}
