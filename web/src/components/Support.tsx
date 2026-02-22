import { DollarSign, Star, ExternalLink } from 'lucide-react';

export default function Support() {
  return (
    <section id="support" className="py-20 md:py-28">
      <div className="mx-auto max-w-7xl px-6">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="font-serif text-4xl md:text-5xl font-bold text-espresso">
            Support the Project
          </h2>
          <p className="mt-4 text-lg text-bronze leading-relaxed">
            Golf Cam Replay is free and open source. If it&apos;s helped your game, consider
            dropping a tip.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="https://account.venmo.com/u/theroad2eldorado?txn=pay&amount=20"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-[#008CFF] hover:bg-[#0070CC] text-white font-semibold px-6 py-3 rounded transition-colors shadow-lg shadow-[#008CFF]/20"
            >
              <DollarSign size={20} />
              Tip on Venmo
            </a>
            <a
              href="https://github.com/theroadeldorado/golf-cam-replay"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 border-2 border-sand hover:border-tan text-espresso font-semibold px-6 py-3 rounded transition-colors"
            >
              <Star size={20} />
              Star on GitHub
              <ExternalLink size={14} className="text-bronze" />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
