// src/shared/lib/legal.ts
// Общее для страниц «Политика конфиденциальности» и «Удаление аккаунта».
// Тексты лежат рядом со страницами (content.ts) — по языку на объект.

/** Почта для вопросов о данных и удаления аккаунта без входа. Указана и в Google Play. */
export const SUPPORT_EMAIL = 'support@hashar.app'

/** Дата последней редакции документов — менять вместе с текстом. */
export const LEGAL_UPDATED = '2026-10-15'

export interface LegalSection {
  heading: string
  paragraphs?: string[]
  items?: string[]
}

export interface LegalDocument {
  title: string
  intro: string
  sections: LegalSection[]
}
