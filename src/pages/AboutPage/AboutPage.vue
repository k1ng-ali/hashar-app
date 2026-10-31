<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { LuCheck } from '@kalimahapps/vue-icons/lu'
import { useAuthStore } from '@/features/auth/store.ts'
import { discountValueLabel } from '@/features/funds/planSale.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import type { Plan } from '@/features/funds/types.ts'
import AppLogo from '@/shared/components/AppLogo.vue'
import { LOCALES, setLocale, type AppLocale } from '@/shared/i18n/index.ts'
import { SUPPORT_EMAIL } from '@/shared/lib/legal.ts'
import { ABOUT } from './content.ts'

// Публичная главная для гостей: что такое Ҳашар, для кого, тарифы, ссылки на документы.
// Гость на «/» попадает сюда (router.ts); в Android-приложении — сразу на вход

const { locale } = useI18n()
const authStore = useAuthStore()
const fundsStore = useFundsStore()

// Цены Pro и Max приходят с сервера: их меняет админ платформы. Без ответа цена просто не показывается
onMounted(() => {
  fundsStore.fetchPlans().catch(() => {})
})
const planOption = (plan: Plan) => fundsStore.plans.find((option) => option.plan === plan)

const c = computed(() => ABOUT[locale.value as AppLocale] ?? ABOUT.ru)
const year = new Date().getFullYear()

const REGISTER = { path: '/login', query: { mode: 'register' } }
</script>

<template>
  <div class="about">
    <header class="topbar">
      <router-link to="/about" class="brand">
        <AppLogo :size="34" />
        <span>{{ $t('app.name') }}</span>
      </router-link>
      <div class="topbar__actions">
        <div class="locales">
          <button
            v-for="item in LOCALES"
            :key="item.code"
            type="button"
            :class="{ active: locale === item.code }"
            @click="setLocale(item.code)"
          >
            {{ item.code.toUpperCase() }}
          </button>
        </div>
        <router-link v-if="authStore.isAuthenticated" to="/" class="nav-btn">{{ c.nav.open }}</router-link>
        <router-link v-else to="/login" class="nav-btn">{{ c.nav.login }}</router-link>
      </div>
    </header>

    <!-- Первый экран -->
    <section class="hero">
      <div class="hero__text">
        <span class="badge">{{ c.hero.badge }}</span>
        <h1>{{ c.hero.title }}</h1>
        <p class="lead">{{ c.hero.lead }}</p>
        <div class="cta-row">
          <router-link v-if="authStore.isAuthenticated" to="/" class="cta">{{ c.hero.open }}</router-link>
          <template v-else>
            <router-link :to="REGISTER" class="cta">{{ c.hero.start }}</router-link>
            <router-link to="/login" class="ghost">{{ c.hero.login }}</router-link>
          </template>
        </div>
      </div>

      <figure class="demo" aria-hidden="true">
        <div class="demo__card">
          <div class="demo__fund">🏠 {{ c.demo.fund }}</div>
          <div class="demo__stats">
            <div>
              <span>{{ c.demo.balance }}</span>
              <strong>{{ c.demo.balanceValue }}</strong>
            </div>
            <div>
              <span>{{ c.demo.paid }}</span>
              <strong>{{ c.demo.paidValue }}</strong>
            </div>
          </div>
          <ul class="demo__rows">
            <li v-for="row in c.demo.rows" :key="row.title">
              <div>
                <div class="demo__title">{{ row.title }}</div>
                <div class="demo__meta">{{ row.meta }}</div>
              </div>
              <span :class="['demo__amount', `demo__amount--${row.kind}`]">{{ row.amount }}</span>
            </li>
          </ul>
        </div>
        <figcaption>{{ c.demo.caption }}</figcaption>
      </figure>
    </section>

    <section class="block">
      <h2>{{ c.audience.title }}</h2>
      <div class="grid grid--3">
        <article v-for="item in c.audience.items" :key="item.title" class="card">
          <span class="icon">{{ item.icon }}</span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.text }}</p>
        </article>
      </div>
    </section>

    <section class="block">
      <h2>{{ c.steps.title }}</h2>
      <ol class="steps">
        <li v-for="(step, index) in c.steps.items" :key="step.title" class="card">
          <span class="step-num">{{ index + 1 }}</span>
          <div>
            <h3>{{ step.title }}</h3>
            <p>{{ step.text }}</p>
          </div>
        </li>
      </ol>
    </section>

    <section class="block">
      <h2>{{ c.features.title }}</h2>
      <div class="grid grid--3">
        <article v-for="item in c.features.items" :key="item.title" class="card">
          <span class="icon">{{ item.icon }}</span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.text }}</p>
        </article>
      </div>
    </section>

    <section class="block trust">
      <h2>{{ c.trust.title }}</h2>
      <p class="block__lead">{{ c.trust.lead }}</p>
      <ul>
        <li v-for="item in c.trust.items" :key="item">
          <LuCheck class="check" />
          <span>{{ item }}</span>
        </li>
      </ul>
      <router-link to="/privacy" class="text-link">{{ c.trust.link }} →</router-link>
    </section>

    <section class="block">
      <h2>{{ c.plans.title }}</h2>
      <p class="block__lead">{{ c.plans.lead }}</p>
      <div class="grid grid--4">
        <article v-for="plan in c.plans.items" :key="plan.name" class="card plan">
          <h3>{{ plan.name }}</h3>
          <div class="plan__price">
            <template v-if="plan.price">{{ plan.price }}</template>
            <template v-else-if="planOption(plan.plan)?.price_tjs">
              <s v-if="planOption(plan.plan)?.sale" class="plan__old">{{ planOption(plan.plan)?.list_price_tjs }}</s>
              {{ $t('plans.price', { price: planOption(plan.plan)?.price_tjs ?? 0 }) }}
            </template>
            <template v-else>—</template>
          </div>
          <div v-if="planOption(plan.plan)?.sale" class="plan__sale">
            🏷 {{ planOption(plan.plan)?.sale?.title }} ·
            {{ discountValueLabel(planOption(plan.plan)!.sale!, $t) }}
          </div>
          <div class="plan__limit">{{ plan.limit }}</div>
          <p>{{ plan.note }}</p>
        </article>
      </div>
      <p class="note">{{ c.plans.payment }}</p>
    </section>

    <section class="block">
      <h2>{{ c.faq.title }}</h2>
      <div class="faq">
        <details v-for="item in c.faq.items" :key="item.q" class="card">
          <summary>{{ item.q }}</summary>
          <p>{{ item.a }}</p>
        </details>
      </div>
    </section>

    <section v-if="!authStore.isAuthenticated" class="final">
      <h2>{{ c.final.title }}</h2>
      <p>{{ c.final.text }}</p>
      <router-link :to="REGISTER" class="cta cta--inverted">{{ c.final.cta }}</router-link>
    </section>

    <footer class="footer">
      <div class="footer__brand">
        <AppLogo :size="28" />
        <p>{{ c.footer.about }}</p>
      </div>
      <nav class="footer__links">
        <router-link to="/terms">{{ $t('legal.terms') }}</router-link>
        <router-link to="/privacy">{{ $t('legal.privacy') }}</router-link>
        <router-link to="/account-deletion">{{ $t('legal.deleteAccount') }}</router-link>
        <a :href="`mailto:${SUPPORT_EMAIL}`">{{ c.footer.contact }}: {{ SUPPORT_EMAIL }}</a>
      </nav>
      <p class="footer__copy">© {{ year }} Ҳашар · hashar.app</p>
    </footer>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.about {
  max-width: 1040px;
  margin: 0 auto;
  padding: calc(12px + var(--sat)) 16px calc(24px + var(--sab));
  color: $navy;
}

/* ── Шапка ──────────────────────────────────────────────────────────────── */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;

  &__actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: $navy;
  font-size: 18px;
  font-weight: 700;
  text-decoration: none;
}

.locales {
  display: flex;
  padding: 3px;
  border-radius: 999px;
  background: $surface-muted;

  button {
    padding: 5px 9px;
    border: none;
    border-radius: 999px;
    background: none;
    color: $text-secondary;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;

    &.active {
      background: $surface;
      color: $navy;
      box-shadow: 0 1px 2px rgba(17, 24, 39, 0.08);
    }
  }
}

.nav-btn {
  @include cta-button;
  padding: 9px 16px;
  border-radius: 999px;
  font-size: 14px;
  white-space: nowrap;
  text-decoration: none;
}

/* ── Первый экран ───────────────────────────────────────────────────────── */
.hero {
  display: grid;
  gap: 32px;
  padding: 40px 0 24px;

  @media (min-width: 880px) {
    grid-template-columns: 1.15fr 1fr;
    align-items: center;
    padding: 72px 0 40px;
  }

  h1 {
    margin: 14px 0 14px;
    font-size: clamp(30px, 6vw, 46px);
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -0.02em;
  }
}

.badge {
  display: inline-block;
  padding: 5px 12px;
  border-radius: 999px;
  background: rgba(22, 163, 74, 0.1);
  color: $success;
  font-size: 13px;
  font-weight: 600;
}

.lead {
  margin: 0;
  font-size: 16px;
  line-height: 1.6;
  color: $text-secondary;
}

.cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
}

.cta {
  @include cta-button;
  text-decoration: none;

  &--inverted {
    background: #fff;
    color: $navy;
  }
}

.ghost {
  @include ghost-button;
  padding: 14px 22px;
  border-radius: 16px;
  font-size: 15px;
  text-decoration: none;
}

/* Пример фонда */
.demo {
  margin: 0;

  &__card {
    @include glass-card(24px);
    padding: 20px;
    box-shadow: 0 24px 48px -24px rgba(17, 24, 39, 0.25);
  }

  &__fund {
    font-size: 14px;
    font-weight: 600;
    color: $text-secondary;
  }

  &__stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin: 14px 0;

    > div {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 14px;
      border-radius: 16px;
      background: $surface-muted;
    }

    span {
      font-size: 12px;
      color: $text-secondary;
    }

    strong {
      font-size: 20px;
      font-weight: 700;
    }
  }

  &__rows {
    margin: 0;
    padding: 0;
    list-style: none;

    li {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 0;
      border-top: 1px solid $hairline;
    }
  }

  &__title {
    font-size: 14px;
    font-weight: 600;
  }

  &__meta {
    font-size: 12px;
    color: $text-muted;
  }

  &__amount {
    flex-shrink: 0;
    font-size: 14px;
    font-weight: 700;

    &--in {
      color: $success;
    }
  }

  figcaption {
    margin-top: 10px;
    font-size: 12px;
    text-align: center;
    color: $text-muted;
  }
}

/* ── Блоки ──────────────────────────────────────────────────────────────── */
.block {
  padding: 32px 0;

  h2 {
    margin: 0 0 16px;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.01em;
  }

  &__lead {
    max-width: 680px;
    margin: -6px 0 18px;
    font-size: 15px;
    line-height: 1.6;
    color: $text-secondary;
  }
}

.grid {
  display: grid;
  gap: 12px;

  @media (min-width: 640px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (min-width: 880px) {
    &--3 {
      grid-template-columns: repeat(3, 1fr);
    }

    &--4 {
      grid-template-columns: repeat(4, 1fr);
    }
  }
}

.card {
  @include glass-card;
  padding: 18px;

  h3 {
    margin: 0 0 6px;
    font-size: 16px;
    font-weight: 700;
  }

  p {
    margin: 0;
    font-size: 14px;
    line-height: 1.55;
    color: $text-secondary;
  }
}

.icon {
  @include icon-circle(44px);
  margin-bottom: 12px;
  background: $surface-muted;
  font-size: 22px;
}

.steps {
  display: grid;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;

  @media (min-width: 640px) {
    grid-template-columns: repeat(2, 1fr);
  }

  li {
    display: flex;
    gap: 14px;
  }
}

.step-num {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: $navy;
  color: #fff;
  font-size: 14px;
  font-weight: 700;
}

.trust {
  ul {
    display: grid;
    gap: 10px;
    margin: 0 0 16px;
    padding: 0;
    list-style: none;
  }

  li {
    display: flex;
    gap: 10px;
    font-size: 15px;
    line-height: 1.5;
  }

  .check {
    flex-shrink: 0;
    margin-top: 3px;
    color: $success;
  }
}

.text-link {
  color: $navy;
  font-size: 14px;
  font-weight: 600;
}

.plan {
  &__price {
    font-size: 22px;
    font-weight: 800;
  }

  &__old {
    font-size: 15px;
    font-weight: 500;
    color: $text-muted;
  }

  &__sale {
    margin-top: 2px;
    font-size: 12px;
    font-weight: 600;
    color: $success;
  }

  &__limit {
    margin: 2px 0 10px;
    font-size: 13px;
    font-weight: 600;
    color: $success;
  }
}

.note {
  margin: 14px 0 0;
  font-size: 13px;
  line-height: 1.55;
  color: $text-secondary;
}

.faq {
  display: grid;
  gap: 10px;

  summary {
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
  }

  p {
    margin-top: 10px;
  }
}

.final {
  margin: 24px 0 8px;
  padding: 36px 24px;
  border-radius: 28px;
  background: $navy;
  color: #fff;
  text-align: center;

  h2 {
    margin: 0 0 8px;
    font-size: 26px;
    font-weight: 800;
  }

  p {
    margin: 0 0 20px;
    color: rgba(255, 255, 255, 0.7);
  }
}

/* ── Подвал ─────────────────────────────────────────────────────────────── */
.footer {
  display: grid;
  gap: 16px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid $hairline;
  font-size: 13px;
  color: $text-secondary;

  &__brand {
    display: flex;
    align-items: center;
    gap: 10px;

    p {
      margin: 0;
    }
  }

  &__links {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 18px;

    a {
      color: $text-secondary;
      text-decoration: underline;
      overflow-wrap: anywhere;
    }
  }

  &__copy {
    margin: 0;
    color: $text-muted;
  }
}
</style>
