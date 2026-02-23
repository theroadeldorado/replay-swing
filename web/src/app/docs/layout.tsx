import type { Metadata } from 'next';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  title: 'Documentation — ReplaySwing',
  description:
    'Complete documentation for ReplaySwing: camera setup, audio trigger, recording, playback, PiP overlay, drawing tools, swing comparison, keyboard shortcuts, and more.',
};

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Header />
      <main>{children}</main>
      <Footer />
    </>
  );
}
