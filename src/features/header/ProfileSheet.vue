<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { LuLogOut } from '@kalimahapps/vue-icons/lu'
import { useAuthStore } from '@/features/auth/store.ts'
import PhoneEditor from '@/features/auth/components/PhoneEditor.vue'
import { useFundsStore } from '@/features/funds/store.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import { LOCALES, setLocale } from '@/shared/i18n/index.ts'

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const { locale } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const fundsStore = useFundsStore()

function go(path: string) {
  emit('close')
  void router.push(path)
}

async function handleLogout() {
  emit('close')
  await authStore.logout()
}
</script>

<template>
  <BottomSheet :open="open" :title="$t('header.profile')" @close="emit('close')">
    <div v-if="authStore.user" class="profile-card">
      <div class="name">{{ authStore.user.full_name }}</div>
      <div v-if="authStore.user.email" class="meta">{{ authStore.user.email }}</div>
      <div v-if="fundsStore.current" class="fund-line">
        <span class="role-badge">{{ $t(`roles.${fundsStore.current.my_role}`) }}</span>
        <span>{{ fundsStore.current.name }} · {{ fundsStore.currentMembership?.address_unit }}</span>
      </div>
    </div>

    <PhoneEditor v-if="authStore.user" />

    <div class="links">
      <button class="link-btn" @click="go('/funds')">🏘️ {{ $t('header.myFunds') }}</button>
      <button v-if="authStore.isPlatformAdmin" class="link-btn" @click="go('/platform')">
        ⚙️ {{ $t('platform.title') }}
      </button>
    </div>

    <!-- Язык -->
    <div class="section-label">{{ $t('header.language') }}</div>
    <div class="locales">
      <button
        v-for="item in LOCALES"
        :key="item.code"
        class="locale-btn"
        :class="{ 'locale-btn--active': locale === item.code }"
        @click="setLocale(item.code)"
      >
        {{ item.label }}
      </button>
    </div>

    <button class="logout-btn" @click="handleLogout">
      <LuLogOut />
      {{ $t('header.logout') }}
    </button>

    <div class="legal-links">
      <button @click="go('/about')">{{ $t('legal.about') }}</button>
      <button @click="go('/terms')">{{ $t('legal.terms') }}</button>
      <button @click="go('/privacy')">{{ $t('legal.privacy') }}</button>
      <button class="legal-links__danger" @click="go('/account-deletion')">{{ $t('legal.deleteAccount') }}</button>
    </div>
  </BottomSheet>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.profile-card {
  @include glass-card;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 18px;
  margin-bottom: 14px;

  .name {
    font-size: 18px;
    font-weight: 700;
    color: $navy;
  }

  .meta {
    font-size: 13px;
    color: $text-secondary;
  }
}

.fund-line {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
  font-size: 12px;
  color: $text-secondary;
}

.role-badge {
  padding: 3px 10px;
  border-radius: 20px;
  background: $gradient;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}

.links {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 18px;
}

.link-btn {
  @include ghost-button;
  justify-content: flex-start;
  padding: 12px 16px;
}

.section-label {
  @include field-label;
}

.locales {
  display: flex;
  gap: 8px;
  margin-bottom: 22px;
}

.locale-btn {
  @include ghost-button;
  flex: 1;

  &--active {
    border-color: transparent;
    background: $gradient;
    color: #fff;
  }
}


.logout-btn {
  @include ghost-button;
  width: 100%;
  padding: 13px;
  color: $danger;
  border-color: rgba(239, 68, 68, 0.2);
}

.legal-links {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 4px 18px;
  margin-top: 14px;

  button {
    padding: 4px;
    border: none;
    background: none;
    color: $text-secondary;
    font-size: 12px;
    cursor: pointer;
  }

  &__danger {
    color: $danger !important;
  }
}
</style>
