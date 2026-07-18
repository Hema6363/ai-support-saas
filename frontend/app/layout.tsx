import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Support SaaS',
  description: 'AI customer support platform frontend',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
