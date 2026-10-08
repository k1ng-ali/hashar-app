import {
  User,
  BillingRate,
  TargetFund,
  Contribution,
  Expense,
  PaymentRequisite,
  Announcement,
  FundSummary,
  ResidentBalanceStatus,
  ContributionStatus,
  UserRole,
} from '@/shared/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function request<T>(endpoint: string, options: RequestInit = {}, currentUserId?: string): Promise<T> {
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');
  if (currentUserId) {
    headers.set('X-User-Id', currentUserId);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error (${response.status}): ${errorText || response.statusText}`);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const fundApi = {
  // Summary & Reports
  getSummary: () => request<FundSummary>('/reports/summary'),
  getFinancialReport: () => request<any>('/reports/financial'),
  getDebtors: () => request<ResidentBalanceStatus[]>('/reports/debtors'),
  getContributionsExportUrl: () => `${API_BASE_URL}/reports/export/contributions`,
  getExpensesExportUrl: () => `${API_BASE_URL}/reports/export/expenses`,

  // Users
  getUsers: () => request<User[]>('/users/'),
  getUser: (id: string) => request<User>(`/users/${id}`),
  getResidentStatus: (id: string) => request<ResidentBalanceStatus>(`/users/${id}/status`),
  updateUserRole: (id: string, role: UserRole, currentUserId?: string) =>
    request<User>(`/users/${id}/role?role=${role}`, { method: 'PUT' }, currentUserId),

  // Contributions
  getContributions: (params?: { userId?: string; status?: ContributionStatus; category?: string }) => {
    const query = new URLSearchParams();
    if (params?.userId) query.set('user_id', params.userId);
    if (params?.status) query.set('status', params.status);
    if (params?.category) query.set('category', params.category);
    const qs = query.toString() ? `?${query.toString()}` : '';
    return request<Contribution[]>(`/contributions/${qs}`);
  },
  createContribution: (payload: Partial<Contribution>, currentUserId: string) =>
    request<Contribution>('/contributions/', { method: 'POST', body: JSON.stringify(payload) }, currentUserId),
  verifyContribution: (id: string, payload: { status: ContributionStatus; commentAdmin?: string }, currentUserId: string) =>
    request<Contribution>(`/contributions/${id}/verify`, { method: 'POST', body: JSON.stringify(payload) }, currentUserId),

  // Expenses
  getExpenses: () => request<Expense[]>('/expenses/'),
  createExpense: (payload: Partial<Expense>, currentUserId: string) =>
    request<Expense>('/expenses/', { method: 'POST', body: JSON.stringify(payload) }, currentUserId),
  deleteExpense: (id: string, currentUserId: string) =>
    request<void>(`/expenses/${id}`, { method: 'DELETE' }, currentUserId),

  // Target Funds
  getTargetFunds: () => request<TargetFund[]>('/target-funds/'),
  createTargetFund: (payload: Partial<TargetFund>, currentUserId: string) =>
    request<TargetFund>('/target-funds/', { method: 'POST', body: JSON.stringify(payload) }, currentUserId),
  updateTargetFund: (id: number, payload: Partial<TargetFund>, currentUserId: string) =>
    request<TargetFund>(`/target-funds/${id}`, { method: 'PUT', body: JSON.stringify(payload) }, currentUserId),
  deleteTargetFund: (id: number, currentUserId: string) =>
    request<void>(`/target-funds/${id}`, { method: 'DELETE' }, currentUserId),

  // Announcements
  getAnnouncements: () => request<Announcement[]>('/announcements/'),
  createAnnouncement: (payload: Partial<Announcement>, currentUserId: string) =>
    request<Announcement>('/announcements/', { method: 'POST', body: JSON.stringify(payload) }, currentUserId),
  toggleLike: (id: string, currentUserId: string) =>
    request<Announcement>(`/announcements/${id}/like`, { method: 'POST' }, currentUserId),
  addComment: (id: string, text: string, currentUserId: string) =>
    request<any>(`/announcements/${id}/comments`, { method: 'POST', body: JSON.stringify({ text }) }, currentUserId),
  deleteAnnouncement: (id: string, currentUserId: string) =>
    request<void>(`/announcements/${id}`, { method: 'DELETE' }, currentUserId),

  // Settings & Requisites
  getBillingRate: () => request<BillingRate>('/settings/rate'),
  updateBillingRate: (amount: number, effectiveFrom: string, currentUserId: string) =>
    request<BillingRate>('/settings/rate', { method: 'POST', body: JSON.stringify({ amount, effectiveFrom }) }, currentUserId),
  getPaymentRequisites: () => request<PaymentRequisite[]>('/settings/requisites'),
  createPaymentRequisite: (payload: Partial<PaymentRequisite>, currentUserId: string) =>
    request<PaymentRequisite>('/settings/requisites', { method: 'POST', body: JSON.stringify(payload) }, currentUserId),
  togglePaymentRequisite: (id: number, currentUserId: string) =>
    request<PaymentRequisite>(`/settings/requisites/${id}/toggle`, { method: 'PUT' }, currentUserId),
};
