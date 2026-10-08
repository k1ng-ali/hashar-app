export type UserRole = 'RESIDENT' | 'ADMIN' | 'SUPERADMIN';

export type UserStatus = 'PENDING_APPROVAL' | 'ACTIVE' | 'BLOCKED';

export interface User {
  id: string;
  phone: string;
  fullName: string;
  addressUnit: string; // e.g. "кв. 12", "кв. 24", "дом 5"
  role: UserRole;
  status: UserStatus;
  createdAt: string;
  email?: string;
  avatarUrl?: string;
}

export interface BillingRate {
  id: number;
  amount: number; // e.g. 1500 ₽
  effectiveFrom: string; // YYYY-MM-DD
  createdByAdminId: string;
  createdAt: string;
}

export interface TargetFund {
  id: number;
  title: string;
  description: string;
  targetAmount: number;
  isActive: boolean;
  createdByAdminId: string;
  createdAt: string;
  category: 'Безопасность' | 'Благоустройство' | 'Капремонт' | 'Инфраструктура';
}

export type ContributionCategory = 'MONTHLY_FEE' | 'TARGET_FUND';
export type ContributionStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface Contribution {
  id: string;
  userId: string;
  userName: string;
  userUnit: string;
  amount: number;
  category: ContributionCategory;
  targetFundId?: number;
  targetFundTitle?: string;
  billingPeriod?: string; // e.g. "2026-09" (Сентябрь 2026)
  receiptImagePath: string;
  status: ContributionStatus;
  commentUser?: string;
  commentAdmin?: string; // Reason for rejection or note
  reviewedByAdminId?: string;
  reviewedByAdminName?: string;
  reviewedAt?: string;
  createdAt: string;
}

export type ExpenseCategory = 
  | 'Ремонт' 
  | 'Электрика' 
  | 'Аварийные работы' 
  | 'Хознужды' 
  | 'Озеленение' 
  | 'Видеонаблюдение';

export interface Expense {
  id: string;
  title: string;
  category: ExpenseCategory;
  amount: number;
  description: string;
  receiptImagePaths: string[];
  targetFundId?: number;
  targetFundTitle?: string;
  createdByAdminId: string;
  createdByAdminName: string;
  createdAt: string;
}

export interface PaymentRequisite {
  id: number;
  bankName: string;
  cardOrAccountNumber: string;
  recipientName: string;
  phoneNumber?: string;
  isActive: boolean;
  note?: string;
}

export interface AnnouncementComment {
  id: string;
  announcementId: string;
  userId: string;
  userName: string;
  userUnit: string;
  text: string;
  createdAt: string;
}

export interface Announcement {
  id: string;
  title: string;
  content: string;
  category?: string;
  imageUrls?: string[];
  isPinned: boolean;
  authorId: string;
  authorName: string;
  authorRole: string;
  createdAt: string;
  comments: AnnouncementComment[];
  likesCount?: number;
  likedByUserIds?: string[];
}

export interface RolePermissions {
  canAccessAdminPanel: boolean;
  canVerifyReceipts: boolean;
  canAddExpense: boolean;
  canDeleteExpense: boolean;
  canManageResidents: boolean;
  canManageSettings: boolean;
  canCreateTargetFund: boolean;
  canDeleteTargetFund: boolean;
  canToggleTargetFund: boolean;
  canPinAnnouncements: boolean;
  canDeleteAnnouncements: boolean;
}

export interface ResidentBalanceStatus {
  paidMonthsCount: number;
  paidUntilPeriod: string | null;
  debtMonthsCount: number;
  debtAmount: number;
  advanceMonthsCount: number;
  advanceAmount: number;
  statusType: 'OK' | 'DEBT' | 'ADVANCE';
  balance: number;
  totalPaid: number;
  totalDue: number;
  hasPending: boolean;
  pendingAmount: number;
  nextBillingPeriod: string;
  nextBillingDate: string;
  nextBillingAmount: number;
  coveredPeriods: string[];
  unpaidPeriods: string[];
}

export interface FundSummary {
  totalBalance: number;
  totalCollected: number;
  totalExpenses: number;
  currentMonthCollected: number;
  currentMonthSpent: number;
  pendingContributionsCount: number;
  pendingContributionsAmount: number;
  activeResidentsCount: number;
  debtorsCount: number;
}
