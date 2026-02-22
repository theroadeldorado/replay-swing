import type { Metadata } from 'next';
import { Playfair_Display, Inter } from 'next/font/google';
import './globals.css';

const playfair = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-serif',
  display: 'swap',
});

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  metadataBase: new URL('https://golfcamreplay.com'),
  title: 'Golf Cam Replay — Free Swing Capture & Instant Replay for Golf Simulators',
  description:
    'Record and replay your golf swings automatically. Audio-triggered capture, PiP overlay for simulators, multi-camera support. Free & open source.',
  openGraph: {
    title: 'Golf Cam Replay — Free Swing Capture & Instant Replay for Golf Simulators',
    description:
      'Record and replay your golf swings automatically. Audio-triggered capture, PiP overlay for simulators, multi-camera support. Free & open source.',
    type: 'website',
    url: 'https://golfcamreplay.com',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Golf Cam Replay — Free Swing Capture & Instant Replay',
    description:
      'Record and replay your golf swings automatically. Audio-triggered capture, PiP overlay for simulators, multi-camera support. Free & open source.',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${playfair.variable} ${inter.variable}`}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
