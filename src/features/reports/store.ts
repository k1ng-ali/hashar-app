// src/features/reports/store.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { downloadBlob, filenameFromDisposition } from '@/shared/lib/browser.ts'
import type { Currency } from '@/shared/lib/currency.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import * as api from './api.ts'
import type { Debtor, ExportKind, FinancialReport } from './types.ts'

export const useReportsStore = defineStore('reports', () => {
  const funds = useFundsStore()

  // ── State ─────────────────────────────────────────────────────────────
  const report = ref<FinancialReport | null>(null)
  const debtors = ref<Debtor[]>([])
  const isLoading = ref(false)
  const exportingKind = ref<ExportKind | null>(null)
  const errorMessage = ref('')

  // ── Actions ───────────────────────────────────────────────────────────
  async function fetchAll(currency?: Currency) {
    isLoading.value = true
    errorMessage.value = ''
    try {
      const [reportResponse, debtorsResponse] = await Promise.all([
        api.getFinancialReport(funds.fundId, currency),
        api.listDebtors(funds.fundId),
      ])
      report.value = reportResponse.data
      debtors.value = debtorsResponse.data
    } catch {
      errorMessage.value = 'errors.loadFailed'
    } finally {
      isLoading.value = false
    }
  }

  /** Скачивает CSV и возвращает имя файла. */
  async function exportCsv(kind: ExportKind): Promise<string> {
    exportingKind.value = kind
    try {
      const response = await api.exportCsv(funds.fundId, kind)
      const filename = filenameFromDisposition(response.headers['content-disposition'], `${kind}.csv`)
      await downloadBlob(response.data, filename)
      return filename
    } finally {
      exportingKind.value = null
    }
  }

  return {
    report,
    debtors,
    isLoading,
    exportingKind,
    errorMessage,
    fetchAll,
    exportCsv,
  }
})
