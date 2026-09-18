import type { Metadata } from 'next';
import './globals.css';
import { AppShell } from '../components/layout/AppShell';
import { AppProviders } from '../components/providers/AppProviders';

export const metadata: Metadata = {
  title: 'MediBot AI - Hệ Thống Khám Bệnh Đa Phương Thức Thông Minh',
  description: 'Trợ Lý Y Tế AI Đa Phương Thức chuẩn hóa Bộ Y Tế & CSDL ICD-10 (Giọng nói, OCR phiếu máu, Bóc tách triệu chứng & Cấp cứu Red Flag)',
  icons: {
    icon: [
      { url: '/icon.svg', type: 'image/svg+xml' }
    ],
    shortcut: '/icon.svg',
    apple: '/icon.svg',
  }
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" className="h-full" data-font-size="md" suppressHydrationWarning>
      <body className="h-screen max-h-screen overflow-hidden bg-[#f8fafc] text-slate-900 antialiased selection:bg-blue-100 selection:text-blue-900 relative" suppressHydrationWarning>
        <AppProviders>
          <AppShell>{children}</AppShell>
        </AppProviders>
      </body>
    </html>
  );
}

