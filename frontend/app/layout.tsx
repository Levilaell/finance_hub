import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import { GoogleTagManager } from '@next/third-parties/google'
import './globals.css'
import { Providers } from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'CaixaHub - Automação Financeira',
  description: 'Conecte seu banco e deixe nossa IA automatizar suas finanças. Automação financeira para o pequeno e médio varejista brasileiro.',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1.0,
  maximumScale: 1.0,
  userScalable: false,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR" className="dark">
      <GoogleTagManager gtmId="GTM-K6CD5ZNP" />
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}