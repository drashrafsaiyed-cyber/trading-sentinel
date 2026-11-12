import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Trading Sentinel - AI Sentiment Analysis',
  description: 'Real-time Bull/Bear market predictions using AI pattern recognition',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
