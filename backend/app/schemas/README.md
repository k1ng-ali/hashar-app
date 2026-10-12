# schemas — Pydantic v2

## Именование

- `*In` — тело запроса (`FundCreateIn`, `JoinIn`, `TransferCreateIn`)
- `*Out` — ответ (`FundOut`, `MemberOut`), `*OutCouncil` / `*OutAdmin` — расширенные ответы для совета и админа платформы
- `CurrentUser` — пользователь из access-токена (`id`, `is_platform_admin`)
- `FundContext` — активное членство в фонде из URL (`fund_id`, `user_id`, `member_id`, `role`, `is_council`, `is_chairman`)
- схемы из ORM — `model_config = ConfigDict(from_attributes=True)`
- частичные апдейты — все поля `X | None = None` (`FundUpdateIn`, `TargetFundUpdateIn`)
- поля в **snake_case** — фронтенд повторяет их один в один в `features/*/types.ts`

## Файлы

| Файл | Схемы |
|---|---|
| `auth.py` | `RegisterIn`, `LoginIn`, `DevLoginIn`, `TokenOut` |
| `user.py` | `CurrentUser`, `UserOut`, `DemoUserOut` |
| `fund.py` | `FundCreateIn`, `FundUpdateIn`, `RateOut`, `FundOut`, `FundPublicOut`, `MyFundOut`, `AccountOut`, `PlanInfoOut`, `FundSummaryOut`, `AccountSummaryOut`, `OperationOut` |
| `member.py` | `FundContext`, `JoinIn`, `MemberOut`, `MemberOutCouncil`, `MemberStatusUpdateIn`, `MemberRoleUpdateIn`, `ChairmanTransferIn` |
| `plan.py` | `PlanOptionOut`, `PlanRequestIn`, `PlanRequestOut`, `PlanApproveIn`, `PlanRejectIn`, `FundPlanSetIn`, `FundCouncilMemberOut`, `FundOutAdmin` |
| `account.py` | `AccountCreateIn`, `RequisiteCreateIn`, `RequisiteOut`, `TransferCreateIn`, `TransferOut` |
| `balance.py` | `ResidentBalanceOut` |
| `contribution.py` | `ContributionCreateIn`, `ContributionApproveIn`, `ContributionRejectIn`, `ContributionOut`, `CurrencyTotalOut`, `ContributionHistoryOut` |
| `expense.py` | `ExpenseCreateIn`, `ExpenseOut` |
| `target_fund.py` | `TargetFundCreateIn`, `TargetFundUpdateIn`, `TargetFundOut`, `TargetFundDetailOut`, `MonthAmountOut` |
| `announcement.py` | `AnnouncementCreateIn`, `AnnouncementOut`, `CommentCreateIn`, `CommentOut` |
| `report.py` | `FinancialReportOut`, `MonthlyLedgerRowOut`, `CategoryStatOut`, `DebtorOut` |

Роли, статусы, валюты, тарифы и категории — `str`-Enum'ы из `app/enums/` (коды на английском, подписи — в i18n фронтенда).
