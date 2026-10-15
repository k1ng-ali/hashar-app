import path from 'node:path'
import { defineConfig, loadEnv, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { AntDesignVueResolver } from 'unplugin-vue-components/resolvers'

// CSP для прод-сборки. GitHub Pages не даёт ставить заголовки, поэтому политика — <meta> в index.html.
// Скрипты только свои, стили — свои + inline от ant-design-vue, шрифт Inter с Google Fonts,
// картинки — свои, data: (чеки) и https: (аватары провайдеров входа), запросы — только к API.
// frame-ancestors в <meta> не работает — защита от встраивания во фрейм тут недоступна.
// Со входом через Google добавляется Google Identity Services: скрипт, стили и фрейм кнопки
function contentSecurityPolicy(apiUrl: string, googleSignIn: boolean): Plugin {
  const gsi = googleSignIn ? 'https://accounts.google.com/gsi/' : ''
  const policy = [
    "default-src 'self'",
    `script-src 'self' ${gsi && `${gsi}client`}`.trim(),
    `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com ${gsi && `${gsi}style`}`.trim(),
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: blob: https:",
    `connect-src 'self' ${apiUrl} ${gsi}`.trim(),
    `frame-src ${gsi || "'none'"}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ')

  return {
    name: 'content-security-policy',
    apply: 'build',
    transformIndexHtml: () => [
      { tag: 'meta', attrs: { 'http-equiv': 'Content-Security-Policy', content: policy }, injectTo: 'head-prepend' },
      { tag: 'meta', attrs: { name: 'referrer', content: 'strict-origin-when-cross-origin' }, injectTo: 'head-prepend' },
    ],
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'VITE_')

  return {
    plugins: [
      vue(),
      Components({
        dts: 'src/components.d.ts',
        resolvers: [AntDesignVueResolver({ importStyle: false })],
      }),
      contentSecurityPolicy(env.VITE_API_URL ?? '', !!env.VITE_GOOGLE_CLIENT_ID),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    server: {
      host: true,
      port: 5173,
    },
  }
})
