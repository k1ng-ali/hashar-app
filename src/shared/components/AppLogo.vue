<script setup lang="ts">
// Знак «Ҳашар»: две сплетённые линии буквы Ҳ, хвостик — монета.
// Исходники файлами — public/logo-mark.svg, public/logo.svg
withDefaults(
  defineProps<{
    size?: number
    // inverted — тёмный знак на белой плашке (для тёмного фона)
    inverted?: boolean
  }>(),
  { size: 40, inverted: false },
)
</script>

<template>
  <svg
    class="app-logo"
    :class="{ 'app-logo--inverted': inverted }"
    :width="size"
    :height="size"
    viewBox="0 0 120 120"
    role="img"
    aria-label="Ҳашар"
  >
    <rect class="app-logo__bg" width="120" height="120" rx="28" />
    <path class="app-logo__line" d="M34 30L80 82" />
    <path class="app-logo__gap" d="M80 30L34 82" />
    <path class="app-logo__line" d="M80 30L34 82" />
    <circle class="app-logo__coin" cx="92" cy="94" r="7.5" />
  </svg>
</template>

<style scoped lang="scss">
.app-logo {
  --logo-bg: #111827;
  --logo-fg: #FFFFFF;

  display: block;
  flex-shrink: 0;

  &--inverted {
    --logo-bg: #FFFFFF;
    --logo-fg: #111827;
  }
}

.app-logo__bg {
  fill: var(--logo-bg);
}

.app-logo__line {
  fill: none;
  stroke: var(--logo-fg);
  stroke-width: 14;
  stroke-linecap: round;
}

// разрыв под верхней линией — эффект «переплетения»
.app-logo__gap {
  fill: none;
  stroke: var(--logo-bg);
  stroke-width: 26;
}

.app-logo__coin {
  fill: #16A34A;
}
</style>
