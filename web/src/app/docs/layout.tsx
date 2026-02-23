import type { Metadata } from 'next';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  title: 'Documentation — Golf Cam Replay',
  description:
    'Complete documentation for Golf Cam Replay: camera setup, audio trigger, recording, playback, PiP overlay, drawing tools, swing comparison, keyboard shortcuts, and more.',
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
