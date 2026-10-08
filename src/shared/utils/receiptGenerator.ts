/**
 * Generates an elegant, realistic banking transaction receipt SVG as Data URI
 * for realistic visual display and testing of verification workflow.
 */
export function generateReceiptSvg(params: {
  bankName: string;
  amount: number;
  date: string;
  senderName: string;
  recipientName: string;
  purpose: string;
  transactionId?: string;
}): string {
  const {
    bankName,
    amount,
    date,
    senderName,
    recipientName,
    purpose,
    transactionId = 'TX-' + Math.floor(100000000 + Math.random() * 900000000)
  } = params;

  const formattedAmount = amount.toLocaleString('ru-RU') + ' ₽';

  const svg = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 580" width="100%" height="100%">
  <defs>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a" />
      <stop offset="100%" stop-color="#1e293b" />
    </linearGradient>
    <filter id="cardShadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="6" stdDeviation="8" flood-opacity="0.12" flood-color="#000" />
    </filter>
  </defs>

  <!-- Background Paper -->
  <rect x="15" y="15" width="390" height="550" rx="16" fill="#ffffff" filter="url(#cardShadow)" stroke="#e2e8f0" stroke-width="1.5"/>

  <!-- Bank Top Bar -->
  <path d="M 15 31 Q 15 15 31 15 L 389 15 Q 405 15 405 31 L 405 95 L 15 95 Z" fill="url(#headerGrad)"/>
  
  <!-- Bank Brand & Title -->
  <circle cx="48" cy="55" r="18" fill="#10b981" />
  <path d="M42 55 L46 59 L55 50" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
  
  <text x="76" y="50" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="14" font-weight="700" fill="#ffffff">${bankName}</text>
  <text x="76" y="68" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11" font-weight="500" fill="#94a3b8">Чек по операции • УСПЕШНО</text>

  <!-- Amount Display -->
  <text x="210" y="145" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="600" fill="#64748b" text-transform="uppercase" letter-spacing="1">Сумма перевода</text>
  <text x="210" y="185" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="32" font-weight="800" fill="#0f172a">${formattedAmount}</text>
  
  <!-- Status Chip -->
  <rect x="145" y="202" width="130" height="26" rx="13" fill="#dcfce7" />
  <text x="210" y="219" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11" font-weight="700" fill="#15803d">ИСПОЛНЕН</text>

  <!-- Dashed Divider -->
  <line x1="35" y1="245" x2="385" y2="245" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="6 4"/>

  <!-- Transaction Details Block -->
  <text x="40" y="280" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="500" fill="#64748b">Дата и время</text>
  <text x="380" y="280" text-anchor="end" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="600" fill="#1e293b">${date}</text>

  <text x="40" y="315" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="500" fill="#64748b">Отправитель</text>
  <text x="380" y="315" text-anchor="end" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="600" fill="#1e293b">${senderName}</text>

  <text x="40" y="350" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="500" fill="#64748b">Получатель</text>
  <text x="380" y="350" text-anchor="end" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="600" fill="#1e293b">${recipientName}</text>

  <text x="40" y="385" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="500" fill="#64748b">Назначение</text>
  <text x="380" y="385" text-anchor="end" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="600" fill="#1e293b">${purpose}</text>

  <text x="40" y="420" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="500" fill="#64748b">Номер документа</text>
  <text x="380" y="420" text-anchor="end" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11" font-weight="600" fill="#64748b" font-family="monospace">${transactionId}</text>

  <g transform="translate(145, 455)">
    <rect width="130" height="42" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
    <text x="65" y="18" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="9" font-weight="700" fill="#475569" letter-spacing="0.5">ЭЛЕКТРОННАЯ ПОДПИСЬ</text>
    <text x="65" y="32" text-anchor="middle" font-family="monospace" font-size="8" font-weight="500" fill="#64748b">ЦЕНТРАЛЬНЫЙ БАНК РФ</text>
  </g>

  <text x="210" y="530" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="10" font-weight="500" fill="#94a3b8">Документ сформирован онлайн • Общественный фонд дома</text>
</svg>
`.trim();

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}
