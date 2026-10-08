import { defineStore } from 'pinia';
import { ref, computed, watch } from 'vue';
import { message } from 'ant-design-vue';
import {
  User,
  BillingRate,
  TargetFund,
  Contribution,
  Expense,
  PaymentRequisite,
  Announcement,
  UserStatus,
  RolePermissions,
} from '@/shared/types';
import {
  INITIAL_USERS,
  INITIAL_BILLING_RATE,
  INITIAL_TARGET_FUNDS,
  INITIAL_PAYMENT_REQUISITES,
  INITIAL_CONTRIBUTIONS,
  INITIAL_EXPENSES,
  INITIAL_ANNOUNCEMENTS,
} from './mockData';
import { calculateFundSummary, calculateResidentStatus } from '@/shared/utils/finance';
import { fundApi } from '@/shared/api';

const STORAGE_KEYS = {
  USERS: 'district_fund_users_v2',
  CURRENT_USER_ID: 'district_fund_current_user_v2',
  CONTRIBUTIONS: 'district_fund_contributions_v2',
  EXPENSES: 'district_fund_expenses_v2',
  TARGET_FUNDS: 'district_fund_target_funds_v2',
  BILLING_RATE: 'district_fund_billing_rate_v2',
  PAYMENT_REQUISITES: 'district_fund_requisites_v2',
  ANNOUNCEMENTS: 'district_fund_announcements_v2',
};

function loadStorage<T>(key: string, fallback: T): T {
  try {
    const saved = localStorage.getItem(key);
    return saved ? JSON.parse(saved) : fallback;
  } catch {
    return fallback;
  }
}

export const useFundStore = defineStore('fund', () => {
  const users = ref<User[]>(loadStorage(STORAGE_KEYS.USERS, INITIAL_USERS));
  const savedCurrentUserId = loadStorage(STORAGE_KEYS.CURRENT_USER_ID, 'user-3');
  const currentUserId = ref<string>(savedCurrentUserId);

  const currentUser = computed<User>(() => {
    return users.value.find((u) => u.id === currentUserId.value) || users.value[0];
  });

  const contributions = ref<Contribution[]>(
    loadStorage(STORAGE_KEYS.CONTRIBUTIONS, INITIAL_CONTRIBUTIONS)
  );
  const expenses = ref<Expense[]>(loadStorage(STORAGE_KEYS.EXPENSES, INITIAL_EXPENSES));
  const targetFunds = ref<TargetFund[]>(
    loadStorage(STORAGE_KEYS.TARGET_FUNDS, INITIAL_TARGET_FUNDS)
  );
  const billingRate = ref<BillingRate>(
    loadStorage(STORAGE_KEYS.BILLING_RATE, INITIAL_BILLING_RATE)
  );
  const paymentRequisites = ref<PaymentRequisite[]>(
    loadStorage(STORAGE_KEYS.PAYMENT_REQUISITES, INITIAL_PAYMENT_REQUISITES)
  );
  const announcements = ref<Announcement[]>(
    loadStorage(STORAGE_KEYS.ANNOUNCEMENTS, INITIAL_ANNOUNCEMENTS)
  );

  const activeTab = ref<string>('dashboard');
  const isApiConnected = ref(false);
  const isInitializing = ref(false);

  // Modal State for Viewing Receipts
  const receiptModal = ref<{
    isOpen: boolean;
    title: string;
    imagePath: string;
    details?: Record<string, string | number>;
  }>({
    isOpen: false,
    title: '',
    imagePath: '',
  });

  // Watchers to persist to localStorage
  watch(users, (val) => localStorage.setItem(STORAGE_KEYS.USERS, JSON.stringify(val)), { deep: true });
  watch(currentUserId, (val) => localStorage.setItem(STORAGE_KEYS.CURRENT_USER_ID, JSON.stringify(val)));
  watch(contributions, (val) => localStorage.setItem(STORAGE_KEYS.CONTRIBUTIONS, JSON.stringify(val)), { deep: true });
  watch(expenses, (val) => localStorage.setItem(STORAGE_KEYS.EXPENSES, JSON.stringify(val)), { deep: true });
  watch(targetFunds, (val) => localStorage.setItem(STORAGE_KEYS.TARGET_FUNDS, JSON.stringify(val)), { deep: true });
  watch(billingRate, (val) => localStorage.setItem(STORAGE_KEYS.BILLING_RATE, JSON.stringify(val)), { deep: true });
  watch(paymentRequisites, (val) => localStorage.setItem(STORAGE_KEYS.PAYMENT_REQUISITES, JSON.stringify(val)), { deep: true });
  watch(announcements, (val) => localStorage.setItem(STORAGE_KEYS.ANNOUNCEMENTS, JSON.stringify(val)), { deep: true });

  async function initializeFromApi() {
    if (isInitializing.value || isApiConnected.value) return;

    isInitializing.value = true;
    try {
      const [apiUsers, apiContributions, apiExpenses, apiTargetFunds, apiAnnouncements, apiRate, apiRequisites] =
        await Promise.all([
          fundApi.getUsers(),
          fundApi.getContributions(),
          fundApi.getExpenses(),
          fundApi.getTargetFunds(),
          fundApi.getAnnouncements(),
          fundApi.getBillingRate(),
          fundApi.getPaymentRequisites(),
        ]);

      users.value = apiUsers;
      contributions.value = apiContributions;
      expenses.value = apiExpenses;
      targetFunds.value = apiTargetFunds;
      announcements.value = apiAnnouncements;
      billingRate.value = apiRate;
      paymentRequisites.value = apiRequisites;

      if (!users.value.some((user) => user.id === currentUserId.value)) {
        currentUserId.value = users.value[0]?.id || currentUserId.value;
      }
      isApiConnected.value = true;
      message.success('Данные синхронизированы с сервером.');
    } catch (error) {
      console.warn('Backend недоступен, используется локальный режим:', error);
      message.warning('Сервер недоступен. Работаем с локальными данными.');
    } finally {
      isInitializing.value = false;
    }
  }

  // Computed Summaries
  const summary = computed(() => {
    return calculateFundSummary(
      contributions.value,
      expenses.value,
      users.value,
      billingRate.value
    );
  });

  const currentUserStatus = computed(() => {
    return calculateResidentStatus(
      currentUser.value.id,
      contributions.value,
      billingRate.value
    );
  });

  const pendingContributions = computed(() => {
    return contributions.value.filter((c) => c.status === 'PENDING');
  });

  const isAdmin = computed(() => {
    return currentUser.value.role === 'ADMIN' || currentUser.value.role === 'SUPERADMIN';
  });

  const isSuperAdmin = computed(() => {
    return currentUser.value.role === 'SUPERADMIN';
  });

  const permissions = computed<RolePermissions>(() => {
    const role = currentUser.value.role;
    if (role === 'SUPERADMIN') {
      return {
        canAccessAdminPanel: true,
        canVerifyReceipts: true,
        canAddExpense: true,
        canDeleteExpense: true,
        canManageResidents: true,
        canManageSettings: true,
        canCreateTargetFund: true,
        canDeleteTargetFund: true,
        canToggleTargetFund: true,
        canPinAnnouncements: true,
        canDeleteAnnouncements: true,
      };
    }
    if (role === 'ADMIN') {
      return {
        canAccessAdminPanel: true,
        canVerifyReceipts: true,
        canAddExpense: true,
        canDeleteExpense: false, // only Chairman (SUPERADMIN) can delete expenses
        canManageResidents: true,
        canManageSettings: false, // only Chairman (SUPERADMIN) can alter billing rate / bank accounts
        canCreateTargetFund: true,
        canDeleteTargetFund: false, // only Chairman can delete target funds
        canToggleTargetFund: true,
        canPinAnnouncements: true,
        canDeleteAnnouncements: false,
      };
    }
    // RESIDENT
    return {
      canAccessAdminPanel: false,
      canVerifyReceipts: false,
      canAddExpense: false,
      canDeleteExpense: false,
      canManageResidents: false,
      canManageSettings: false,
      canCreateTargetFund: false,
      canDeleteTargetFund: false,
      canToggleTargetFund: false,
      canPinAnnouncements: false,
      canDeleteAnnouncements: false,
    };
  });

  // Actions
  function switchUser(userId: string) {
    const found = users.value.find((u) => u.id === userId);
    if (found) {
      currentUserId.value = userId;
      message.info(`Переключено на: ${found.fullName} (${found.addressUnit})`);
    }
  }

  function openReceipt(title: string, imagePath: string, details?: Record<string, string | number>) {
    receiptModal.value = {
      isOpen: true,
      title,
      imagePath,
      details,
    };
  }

  function closeReceipt() {
    receiptModal.value.isOpen = false;
  }

  async function submitContribution(data: {
    amount: number;
    category: 'MONTHLY_FEE' | 'TARGET_FUND';
    targetFundId?: number;
    billingPeriod?: string;
    receiptImagePath: string;
    commentUser?: string;
  }) {
    if (isApiConnected.value) {
      try {
        const contribution = await fundApi.createContribution(data, currentUser.value.id);
        contributions.value = [contribution, ...contributions.value];
        message.success('Чек отправлен на модерацию.');
        return;
      } catch (error) {
        console.warn('Не удалось отправить взнос на backend:', error);
        message.error('Не удалось сохранить взнос на сервере.');
        return;
      }
    }

    let targetFundTitle: string | undefined;
    if (data.category === 'TARGET_FUND' && data.targetFundId) {
      const tf = targetFunds.value.find((t) => t.id === data.targetFundId);
      targetFundTitle = tf?.title;
    }

    const newContrib: Contribution = {
      id: `cont-${Date.now()}`,
      userId: currentUser.value.id,
      userName: currentUser.value.fullName,
      userUnit: currentUser.value.addressUnit,
      amount: data.amount,
      category: data.category,
      targetFundId: data.targetFundId,
      targetFundTitle,
      billingPeriod: data.billingPeriod,
      receiptImagePath: data.receiptImagePath,
      status: 'PENDING',
      commentUser: data.commentUser,
      createdAt: new Date().toISOString(),
    };

    contributions.value = [newContrib, ...contributions.value];
    message.success('Чек отправлен на модерацию. Статус платежа изменится после проверки.');
  }

  async function approveContribution(id: string, commentAdmin?: string) {
    if (isApiConnected.value) {
      try {
        const contribution = await fundApi.verifyContribution(
          id,
          { status: 'APPROVED', commentAdmin },
          currentUser.value.id
        );
        contributions.value = contributions.value.map((item) => (item.id === id ? contribution : item));
        message.success(`Взнос от ${contribution.userName} (${contribution.amount} ₽) успешно одобрен!`);
        return;
      } catch (error) {
        console.warn('Не удалось подтвердить взнос на backend:', error);
        message.error('Не удалось подтвердить взнос на сервере.');
        return;
      }
    }

    const index = contributions.value.findIndex((c) => c.id === id);
    if (index !== -1) {
      const contrib = contributions.value[index];
      contributions.value[index] = {
        ...contrib,
        status: 'APPROVED',
        commentAdmin,
        reviewedByAdminId: currentUser.value.id,
        reviewedByAdminName: currentUser.value.fullName,
        reviewedAt: new Date().toISOString(),
      };
      message.success(`Взнос от ${contrib.userName} (${contrib.amount} ₽) успешно одобрен!`);
    }
  }

  async function rejectContribution(id: string, reason: string) {
    if (isApiConnected.value) {
      try {
        const contribution = await fundApi.verifyContribution(
          id,
          { status: 'REJECTED', commentAdmin: reason },
          currentUser.value.id
        );
        contributions.value = contributions.value.map((item) => (item.id === id ? contribution : item));
        message.warning(`Взнос от ${contribution.userName} отклонен.`);
        return;
      } catch (error) {
        console.warn('Не удалось отклонить взнос на backend:', error);
        message.error('Не удалось отклонить взнос на сервере.');
        return;
      }
    }

    const index = contributions.value.findIndex((c) => c.id === id);
    if (index !== -1) {
      const contrib = contributions.value[index];
      contributions.value[index] = {
        ...contrib,
        status: 'REJECTED',
        commentAdmin: reason,
        reviewedByAdminId: currentUser.value.id,
        reviewedByAdminName: currentUser.value.fullName,
        reviewedAt: new Date().toISOString(),
      };
      message.warning(`Взнос от ${contrib.userName} отклонен с причиной: ${reason}`);
    }
  }

  async function addExpense(data: Omit<Expense, 'id' | 'createdAt' | 'createdByAdminId' | 'createdByAdminName'>) {
    if (isApiConnected.value) {
      try {
        const expense = await fundApi.createExpense(data, currentUser.value.id);
        expenses.value = [expense, ...expenses.value];
        message.success(`Расход «${expense.title}» (${expense.amount} ₽) успешно добавлен.`);
        return;
      } catch (error) {
        console.warn('Не удалось добавить расход на backend:', error);
        message.error('Не удалось сохранить расход на сервере.');
        return;
      }
    }

    const newExpense: Expense = {
      ...data,
      id: `exp-${Date.now()}`,
      createdByAdminId: currentUser.value.id,
      createdByAdminName: currentUser.value.fullName,
      createdAt: new Date().toISOString(),
    };

    expenses.value = [newExpense, ...expenses.value];
    message.success(`Расход «${data.title}» (${data.amount} ₽) успешно добавлен.`);
  }

  async function deleteExpense(id: string) {
    if (isApiConnected.value) {
      try {
        await fundApi.deleteExpense(id, currentUser.value.id);
      } catch (error) {
        console.warn('Не удалось удалить расход на backend:', error);
        message.error('Не удалось удалить расход на сервере.');
        return;
      }
    }
    expenses.value = expenses.value.filter((e) => e.id !== id);
    message.info('Расход удален из фонда.');
  }

  async function updateBillingRate(amount: number) {
    const effectiveFrom = new Date().toISOString().slice(0, 10);
    if (isApiConnected.value) {
      try {
        billingRate.value = await fundApi.updateBillingRate(amount, effectiveFrom, currentUser.value.id);
        message.success(`Новый тариф взносов установлен: ${amount} ₽ / месяц.`);
        return;
      } catch (error) {
        console.warn('Не удалось обновить тариф на backend:', error);
        message.error('Не удалось сохранить тариф на сервере.');
        return;
      }
    }

    billingRate.value = {
      id: Date.now(),
      amount,
      effectiveFrom: new Date().toISOString().slice(0, 10),
      createdByAdminId: currentUser.value.id,
      createdAt: new Date().toISOString(),
    };
    message.success(`Новый тариф взносов установлен: ${amount} ₽ / месяц.`);
  }

  async function addTargetFund(data: {
    title: string;
    description: string;
    targetAmount: number;
    category: TargetFund['category'];
  }) {
    if (isApiConnected.value) {
      try {
        const targetFund = await fundApi.createTargetFund(
          { ...data, isActive: true },
          currentUser.value.id
        );
        targetFunds.value = [targetFund, ...targetFunds.value];
        message.success(`Целевой сбор «${data.title}» открыт.`);
        return;
      } catch (error) {
        console.warn('Не удалось создать целевой сбор на backend:', error);
        message.error('Не удалось сохранить целевой сбор на сервере.');
        return;
      }
    }

    const newFund: TargetFund = {
      ...data,
      id: Date.now(),
      isActive: true,
      createdByAdminId: currentUser.value.id,
      createdAt: new Date().toISOString(),
    };

    targetFunds.value = [newFund, ...targetFunds.value];
    message.success(`Целевой сбор «${data.title}» открыт.`);
  }

  async function deleteTargetFund(id: number) {
    if (isApiConnected.value) {
      try {
        await fundApi.deleteTargetFund(id, currentUser.value.id);
      } catch (error) {
        console.warn('Не удалось удалить целевой сбор на backend:', error);
        message.error('Не удалось удалить целевой сбор на сервере.');
        return;
      }
    }
    targetFunds.value = targetFunds.value.filter((tf) => tf.id !== id);
    message.info('Целевой сбор удален.');
  }

  async function toggleTargetFundActive(id: number) {
    const targetFund = targetFunds.value.find((tf) => tf.id === id);
    if (!targetFund) return;
    if (isApiConnected.value) {
      try {
        const updatedFund = await fundApi.updateTargetFund(
          id,
          { isActive: !targetFund.isActive },
          currentUser.value.id
        );
        targetFunds.value = targetFunds.value.map((tf) => (tf.id === id ? updatedFund : tf));
        message.info('Статус целевого сбора обновлен.');
        return;
      } catch (error) {
        console.warn('Не удалось обновить целевой сбор на backend:', error);
        message.error('Не удалось обновить сбор на сервере.');
        return;
      }
    }
    targetFunds.value = targetFunds.value.map((tf) =>
      tf.id === id ? { ...tf, isActive: !tf.isActive } : tf
    );
    message.info('Статус целевого сбора обновлен.');
  }

  async function addPaymentRequisite(data: Omit<PaymentRequisite, 'id'>) {
    if (isApiConnected.value) {
      try {
        const requisite = await fundApi.createPaymentRequisite(data, currentUser.value.id);
        paymentRequisites.value = [...paymentRequisites.value, requisite];
        message.success(`Счет ${data.bankName} добавлен в фонд.`);
        return;
      } catch (error) {
        console.warn('Не удалось добавить реквизит на backend:', error);
        message.error('Не удалось сохранить реквизит на сервере.');
        return;
      }
    }

    const newReq: PaymentRequisite = {
      ...data,
      id: Date.now(),
    };
    paymentRequisites.value = [...paymentRequisites.value, newReq];
    message.success(`Счет ${data.bankName} добавлен в фонд.`);
  }

  function deletePaymentRequisite(id: number) {
    paymentRequisites.value = paymentRequisites.value.filter((r) => r.id !== id);
    message.info('Счет удален из списка реквизитов.');
  }

  async function toggleRequisiteActive(id: number) {
    if (isApiConnected.value) {
      try {
        const requisite = await fundApi.togglePaymentRequisite(id, currentUser.value.id);
        paymentRequisites.value = paymentRequisites.value.map((item) => (item.id === id ? requisite : item));
        return;
      } catch (error) {
        console.warn('Не удалось обновить реквизит на backend:', error);
        message.error('Не удалось обновить реквизит на сервере.');
        return;
      }
    }
    paymentRequisites.value = paymentRequisites.value.map((r) =>
      r.id === id ? { ...r, isActive: !r.isActive } : r
    );
  }

  function updateUserStatus(userId: string, status: UserStatus) {
    users.value = users.value.map((u) => (u.id === userId ? { ...u, status } : u));
    message.info(`Статус жильца обновлен на: ${status}`);
  }

  function registerResident(data: {
    fullName: string;
    addressUnit: string;
    phone: string;
    email?: string;
  }) {
    const newUser: User = {
      id: `user-${Date.now()}`,
      fullName: data.fullName,
      addressUnit: data.addressUnit,
      phone: data.phone,
      email: data.email,
      role: 'RESIDENT',
      status: 'ACTIVE',
      createdAt: new Date().toISOString(),
    };
    users.value = [...users.value, newUser];
    message.success(`Жилец ${data.fullName} (${data.addressUnit}) добавлен в реестр.`);
  }

  async function addAnnouncement(
    payload:
      | { title: string; content: string; category?: string; isPinned?: boolean }
      | string,
    contentArg?: string,
    isPinnedArg = false
  ) {
    let title = '';
    let content = '';
    let category = 'Новости';
    let isPinned = false;

    if (typeof payload === 'object') {
      title = payload.title;
      content = payload.content;
      category = payload.category || 'Новости';
      isPinned = payload.isPinned || false;
    } else {
      title = payload;
      content = contentArg || '';
      isPinned = isPinnedArg;
    }

    if (isApiConnected.value) {
      try {
        const announcement = await fundApi.createAnnouncement(
          { title, content, category, isPinned },
          currentUser.value.id
        );
        announcements.value = [announcement, ...announcements.value];
        message.success('Объявление опубликовано на доске дома.');
        return;
      } catch (error) {
        console.warn('Не удалось опубликовать объявление на backend:', error);
        message.error('Не удалось сохранить объявление на сервере.');
        return;
      }
    }

    const newAnn: Announcement = {
      id: `ann-${Date.now()}`,
      title,
      content,
      category,
      isPinned,
      authorId: currentUser.value.id,
      authorName: currentUser.value.fullName,
      authorRole:
        currentUser.value.role === 'SUPERADMIN'
          ? 'Председатель ТСЖ'
          : currentUser.value.role === 'ADMIN'
          ? 'Совет дома'
          : 'Житель',
      createdAt: new Date().toISOString(),
      comments: [],
      likesCount: 0,
      likedByUserIds: [],
    };
    announcements.value = [newAnn, ...announcements.value];
    message.success('Объявление опубликовано на доске дома.');
  }

  async function likeAnnouncement(id: string) {
    if (isApiConnected.value) {
      try {
        const announcement = await fundApi.toggleLike(id, currentUser.value.id);
        announcements.value = announcements.value.map((item) => (item.id === id ? announcement : item));
        return;
      } catch (error) {
        console.warn('Не удалось обновить лайк на backend:', error);
        message.error('Не удалось обновить реакцию на сервере.');
        return;
      }
    }

    const ann = announcements.value.find((a) => a.id === id);
    if (!ann) return;
    if (!ann.likedByUserIds) ann.likedByUserIds = [];
    const uid = currentUser.value.id;
    if (ann.likedByUserIds.includes(uid)) {
      ann.likedByUserIds = ann.likedByUserIds.filter((u) => u !== uid);
      ann.likesCount = Math.max(0, (ann.likesCount || 1) - 1);
    } else {
      ann.likedByUserIds.push(uid);
      ann.likesCount = (ann.likesCount || 0) + 1;
      message.success('Спасибо за отклик!');
    }
  }

  async function addCommentToAnnouncement(announcementId: string, text: string) {
    if (isApiConnected.value) {
      try {
        const comment = await fundApi.addComment(announcementId, text, currentUser.value.id);
        announcements.value = announcements.value.map((item) =>
          item.id === announcementId
            ? { ...item, comments: [...item.comments, comment] }
            : item
        );
        message.success('Комментарий добавлен.');
        return;
      } catch (error) {
        console.warn('Не удалось добавить комментарий на backend:', error);
        message.error('Не удалось сохранить комментарий на сервере.');
        return;
      }
    }

    const ann = announcements.value.find((a) => a.id === announcementId);
    if (ann) {
      ann.comments.push({
        id: `comm-${Date.now()}`,
        announcementId,
        userId: currentUser.value.id,
        userName: currentUser.value.fullName,
        userUnit: currentUser.value.addressUnit,
        text,
        createdAt: new Date().toISOString(),
      });
      message.success('Комментарий добавлен.');
    }
  }

  async function deleteAnnouncement(id: string) {
    if (isApiConnected.value) {
      try {
        await fundApi.deleteAnnouncement(id, currentUser.value.id);
      } catch (error) {
        console.warn('Не удалось удалить объявление на backend:', error);
        message.error('Не удалось удалить объявление на сервере.');
        return;
      }
    }
    announcements.value = announcements.value.filter((a) => a.id !== id);
    message.info('Объявление удалено.');
  }

  return {
    users,
    currentUserId,
    currentUser,
    contributions,
    expenses,
    targetFunds,
    billingRate,
    paymentRequisites,
    announcements,
    activeTab,
    receiptModal,
    isApiConnected,
    isInitializing,
    summary,
    currentUserStatus,
    pendingContributions,
    isAdmin,
    isSuperAdmin,
    permissions,
    initializeFromApi,
    switchUser,
    openReceipt,
    closeReceipt,
    submitContribution,
    approveContribution,
    rejectContribution,
    addExpense,
    deleteExpense,
    updateBillingRate,
    addTargetFund,
    deleteTargetFund,
    toggleTargetFundActive,
    addPaymentRequisite,
    deletePaymentRequisite,
    toggleRequisiteActive,
    updateUserStatus,
    registerResident,
    addAnnouncement,
    likeAnnouncement,
    addCommentToAnnouncement,
    deleteAnnouncement,
  };
});
