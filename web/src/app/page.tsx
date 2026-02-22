import Header from '@/components/Header';
import Hero from '@/components/Hero';
import Features from '@/components/Features';
import HowItWorks from '@/components/HowItWorks';
import PipDemo from '@/components/PipDemo';
import Download from '@/components/Download';
import Support from '@/components/Support';
import BugReport from '@/components/BugReport';
import Footer from '@/components/Footer';

export default function Home() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <Features />
        <HowItWorks />
        <PipDemo />
        <Download />
        <Support />
        <BugReport />
      </main>
      <Footer />
    </>
  );
}
