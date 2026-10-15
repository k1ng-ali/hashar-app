/** Демо-режим: быстрый вход демо-пользователями и генератор тестовых чеков. В прод-сборке — false. */
export const IS_DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true'

/** Client ID веб-клиента OAuth Google (и для Android: Credential Manager просит именно веб-клиент). Пусто — вход через Google скрыт. */
export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? ''
