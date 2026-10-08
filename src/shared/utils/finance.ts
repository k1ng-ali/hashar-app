import { Contribution, Expense, User, BillingRate, TargetFund, ResidentBalanceStatus, FundSummary } from '../types';

export const CURRENT_PERIOD = '2026-09'; // September 2026
export const MONTHS_MAP: Record<string, string> = {
  '01': 'Январь',
  '02': 'Февраль',
  '03': 'Март',
  '04': 'Апрель',
  '05': 'Май',
  '06': 'Июнь',
  '07': 'Июль',
  '08': 'Август',
  '09': 'Сентябрь',
  '10': 'Октябрь',
  '11': 'Ноябрь',
  '12': 'Декабрь',
};

export function formatPeriodName(period?: string): string {
  if (!period) return '—';
  const [year, month] = period.split('-');
  const monthName = MONTHS_MAP[month] || month;
  return `${monthName} ${year}`;
}

export function formatCurrency(amount: number): string {
  return amount.toLocaleString('ru-RU') + ' ₽';
}

export function formatDate(dateString: string): string {
  try {
    const d = new Date(dateString);
    return d.toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
}

export function calculateFundSummary(
  contributions: Contribution[],
  expenses: Expense[],
  users: User[],
  billingRate: BillingRate
): FundSummary {
  const approvedContribs = contributions.filter((c) => c.status === 'APPROVED');
  const pendingContribs = contributions.filter((c) => c.status === 'PENDING');

  const totalCollected = approvedContribs.reduce((sum, c) => sum + c.amount, 0);
  const totalExpenses = expenses.reduce((sum, e) => sum + e.amount, 0);
  const totalBalance = totalCollected - totalExpenses;

  // Current month (2026-09)
  const currentMonthApproved = approvedContribs.filter(
    (c) => c.createdAt.startsWith('2026-09') || c.billingPeriod === CURRENT_PERIOD
  );
  const currentMonthCollected = currentMonthApproved.reduce((sum, c) => sum + c.amount, 0);

  const currentMonthSpent = expenses
    .filter((e) => e.createdAt.startsWith('2026-09'))
    .reduce((sum, e) => sum + e.amount, 0);

  const pendingContributionsCount = pendingContribs.length;
  const pendingContributionsAmount = pendingContribs.reduce((sum, c) => sum + c.amount, 0);

  const activeResidents = users.filter((u) => u.role === 'RESIDENT' && u.status === 'ACTIVE');

  let debtorsCount = 0;
  for (const resident of activeResidents) {
    const status = calculateResidentStatus(resident.id, contributions, billingRate);
    if (status.statusType === 'DEBT') {
      debtorsCount++;
    }
  }

  return {
    totalBalance,
    totalCollected,
    totalExpenses,
    currentMonthCollected,
    currentMonthSpent,
    pendingContributionsCount,
    pendingContributionsAmount,
    activeResidentsCount: activeResidents.length,
    debtorsCount,
  };
}

export const BASE_PERIODS = [
  '2026-07',
  '2026-08',
  '2026-09',
  '2026-10',
  '2026-11',
  '2026-12',
  '2027-01',
  '2027-02',
  '2027-03',
  '2027-04',
  '2027-05',
  '2027-06',
];

export function calculateResidentStatus(
  userId: string,
  contributions: Contribution[],
  billingRate: BillingRate
): ResidentBalanceStatus {
  const rate = billingRate.amount > 0 ? billingRate.amount : 1500;
  
  // Accrued periods up to current date (July, August, September = 3 months expected so far)
  const accruedPeriods = ['2026-07', '2026-08', '2026-09'];
  const totalDue = accruedPeriods.length * rate; // 4500 ₽

  // All monthly fee contributions for this user
  const monthlyContributions = contributions.filter(
    (c) => c.userId === userId && c.category === 'MONTHLY_FEE'
  );

  const approvedPaid = monthlyContributions
    .filter((c) => c.status === 'APPROVED')
    .reduce((sum, c) => sum + c.amount, 0);

  const pendingContributions = monthlyContributions.filter(
    (c) => c.status === 'PENDING'
  );
  const pendingAmount = pendingContributions.reduce((sum, c) => sum + c.amount, 0);
  const hasPending = pendingContributions.length > 0;

  const totalPaid = approvedPaid + pendingAmount;
  const balance = totalPaid - totalDue;

  const paidMonthsCount = Math.floor(totalPaid / rate);
  const coveredPeriods = BASE_PERIODS.slice(0, paidMonthsCount);
  const paidUntilPeriod = coveredPeriods.length > 0 ? coveredPeriods[coveredPeriods.length - 1] : null;

  const unpaidPeriods = accruedPeriods.filter((p) => !coveredPeriods.includes(p));

  const nextBillingPeriod = '2026-10';
  const nextBillingDate = '1 октября 2026 г.';
  const nextBillingAmount = rate;

  if (balance < 0) {
    const debtAmount = Math.abs(balance);
    const debtMonthsCount = Math.ceil(debtAmount / rate);
    return {
      paidMonthsCount,
      paidUntilPeriod,
      debtMonthsCount,
      debtAmount,
      advanceMonthsCount: 0,
      advanceAmount: 0,
      statusType: 'DEBT',
      balance,
      totalPaid,
      totalDue,
      hasPending,
      pendingAmount,
      nextBillingPeriod,
      nextBillingDate,
      nextBillingAmount,
      coveredPeriods,
      unpaidPeriods,
    };
  }

  if (balance > 0) {
    const advanceAmount = balance;
    const advanceMonthsCount = Math.floor(advanceAmount / rate);
    return {
      paidMonthsCount,
      paidUntilPeriod: paidUntilPeriod || '2026-10',
      debtMonthsCount: 0,
      debtAmount: 0,
      advanceMonthsCount,
      advanceAmount,
      statusType: 'ADVANCE',
      balance,
      totalPaid,
      totalDue,
      hasPending,
      pendingAmount,
      nextBillingPeriod,
      nextBillingDate,
      nextBillingAmount,
      coveredPeriods,
      unpaidPeriods: [],
    };
  }

  return {
    paidMonthsCount,
    paidUntilPeriod: paidUntilPeriod || '2026-09',
    debtMonthsCount: 0,
    debtAmount: 0,
    advanceMonthsCount: 0,
    advanceAmount: 0,
    statusType: 'OK',
    balance: 0,
    totalPaid,
    totalDue,
    hasPending,
    pendingAmount,
    nextBillingPeriod,
    nextBillingDate,
    nextBillingAmount,
    coveredPeriods,
    unpaidPeriods: [],
  };
}

export function calculateTargetFundStats(
  targetFund: TargetFund,
  contributions: Contribution[]
) {
  const targetContribs = contributions.filter(
    (c) => c.category === 'TARGET_FUND' && c.targetFundId === targetFund.id && c.status === 'APPROVED'
  );
  const collected = targetContribs.reduce((sum, c) => sum + c.amount, 0);
  const percent = Math.min(100, Math.round((collected / targetFund.targetAmount) * 100));
  const remaining = Math.max(0, targetFund.targetAmount - collected);

  return {
    collected,
    percent,
    remaining,
    contributorsCount: targetContribs.length,
  };
}

export function downloadCsv(filename: string, csvContent: string) {
  const bom = '\uFEFF';
  const blob = new Blob([bom + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export function exportContributionsToCsv(contributions: Contribution[]): void {
  const headers = ['ID', 'Дата', 'Житель', 'Квартира', 'Категория', 'Период / Сбор', 'Сумма (руб)', 'Статус', 'Модератор', 'Комментарий'];
  const rows = contributions.map((c) => [
    c.id,
    c.createdAt.slice(0, 10),
    `"${c.userName}"`,
    `"${c.userUnit}"`,
    c.category === 'MONTHLY_FEE' ? 'Ежемесячный сбор' : 'Целевой сбор',
    `"${c.category === 'MONTHLY_FEE' ? formatPeriodName(c.billingPeriod) : c.targetFundTitle || 'Целевой сбор'}"`,
    c.amount,
    c.status === 'APPROVED' ? 'Одобрено' : c.status === 'PENDING' ? 'На проверке' : 'Отклонено',
    `"${c.reviewedByAdminName || '—'}"`,
    `"${(c.commentAdmin || c.commentUser || '').replace(/"/g, '""')}"`,
  ]);

  const csv = [headers.join(';'), ...rows.map((r) => r.join(';'))].join('\r\n');
  const now = new Date().toISOString().slice(0, 10);
  downloadCsv(`reestr_vznosov_${now}.csv`, csv);
}

export function exportExpensesToCsv(expenses: Expense[]): void {
  const headers = ['ID', 'Дата', 'Название расхода', 'Категория', 'Сумма (руб)', 'Ответственный', 'Описание'];
  const rows = expenses.map((e) => [
    e.id,
    e.createdAt.slice(0, 10),
    `"${e.title.replace(/"/g, '""')}"`,
    e.category,
    e.amount,
    `"${e.createdByAdminName}"`,
    `"${e.description.replace(/"/g, '""')}"`,
  ]);

  const csv = [headers.join(';'), ...rows.map((r) => r.join(';'))].join('\r\n');
  const now = new Date().toISOString().slice(0, 10);
  downloadCsv(`reestr_rashodov_${now}.csv`, csv);
}

export function exportDebtorsToCsv(users: User[], contributions: Contribution[], billingRate: BillingRate): void {
  const headers = ['ФИО', 'Квартира', 'Телефон', 'Статус', 'Оплачено месяцев', 'Оплачено по', 'Задолженность (мес)', 'Сумма задолженности (руб)'];
  const activeResidents = users.filter((u) => u.role === 'RESIDENT');

  const rows = activeResidents.map((u) => {
    const status = calculateResidentStatus(u.id, contributions, billingRate);
    const statusText = status.statusType === 'DEBT' ? 'Должник' : status.statusType === 'ADVANCE' ? 'Аванс' : 'В норме';
    return [
      `"${u.fullName}"`,
      `"${u.addressUnit}"`,
      `"${u.phone}"`,
      statusText,
      status.paidMonthsCount,
      `"${formatPeriodName(status.paidUntilPeriod || undefined)}"`,
      status.debtMonthsCount,
      status.debtAmount,
    ];
  });

  const csv = [headers.join(';'), ...rows.map((r) => r.join(';'))].join('\r\n');
  const now = new Date().toISOString().slice(0, 10);
  downloadCsv(`reestr_dolzhnikov_${now}.csv`, csv);
}
