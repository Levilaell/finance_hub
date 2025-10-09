import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'
import PixelTracker from '@/components/PixelTracker'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'CaixaHub - Automação Financeira',
  description: 'Conecte seu banco e deixe nossa IA automatizar suas finanças. Automação financeira para o pequeno e médio varejista brasileiro.',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1.0,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR" className="dark">
      <body className={inter.className}>
        <noscript>
          <img
            height="1"
            width="1"
            style={{ display: 'none' }}
            src="https://www.facebook.com/tr?id=24169428459391565&ev=PageView&noscript=1"
            alt=""
          />
        </noscript>
        <PixelTracker />
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}