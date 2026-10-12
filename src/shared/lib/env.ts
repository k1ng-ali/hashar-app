/** Демо-режим: быстрый вход демо-пользователями и генератор тестовых чеков. В прод-сборке — false. */
export const IS_DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true'
