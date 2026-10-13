<script setup lang="ts">
import { LuDownload } from '@kalimahapps/vue-icons/lu'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import { useReceiptStore } from '@/shared/stores/useReceiptStore.ts'
import { downloadDataUrl } from '@/shared/lib/browser.ts'

const receiptStore = useReceiptStore()

function download() {
  // Скачиваем только картинку: ссылку вида javascript: клик бы выполнил
  if (!receiptStore.image.startsWith('data:image/')) return
  const isSvg = receiptStore.image.startsWith('data:image/svg')
  const extension = isSvg ? 'svg' : receiptStore.image.startsWith('data:image/png') ? 'png' : 'jpg'
  void downloadDataUrl(receiptStore.image, `receipt_${Date.now()}.${extension}`)
}
</script>

<template>
  <BottomSheet
    overlay
    :open="receiptStore.isOpen"
    :title="receiptStore.title || $t('receipt.viewerTitle')"
    @close="receiptStore.close()"
  >
    <div class="receipt-frame">
      <img :src="receiptStore.image" :alt="$t('receipt.viewerTitle')" />
    </div>

    <template #footer>
      <button class="download-btn" @click="download">
        <LuDownload />
        {{ $t('receipt.download') }}
      </button>
      <button class="close-btn" @click="receiptStore.close()">{{ $t('common.close') }}</button>
    </template>
  </BottomSheet>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.receipt-frame {
  @include glass-card;
  padding: 12px;

  img {
    display: block;
    width: 100%;
    max-height: 65vh;
    object-fit: contain;
    border-radius: 14px;
  }
}

.download-btn {
  @include cta-button;
  flex: 1;
}

.close-btn {
  @include ghost-button;
}
</style>
