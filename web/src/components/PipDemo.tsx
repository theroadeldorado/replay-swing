export default function PipDemo() {
  return (
    <section className="py-20 md:py-28">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left: Visual */}
          <div className="relative">
            {/* Simulator screen mockup */}
            <div className="bg-charcoal rounded-2xl p-4 shadow-xl">
              <div className="bg-gradient-to-br from-green-800/40 via-green-900/60 to-neutral-900 rounded-xl aspect-[16/10] relative overflow-hidden">
                {/* Simulated golf sim UI */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="w-32 h-20 border border-white/10 rounded mb-4" />
                  <div className="flex gap-6 text-white/20 text-xs font-mono">
                    <span>CARRY: 265 yds</span>
                    <span>SPEED: 112 mph</span>
                    <span>SPIN: 2,800 rpm</span>
                  </div>
                </div>

                {/* PiP overlay */}
                <div className="absolute bottom-4 right-4 w-48 md:w-56 bg-charcoal rounded-xl p-1.5 shadow-2xl ring-2 ring-gold/40">
                  <div className="bg-neutral-900 rounded-lg aspect-video relative overflow-hidden">
                    {/* Simulated swing replay */}
                    <div className="absolute inset-0 bg-gradient-to-b from-green-900/20 to-neutral-900/80" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      {/* Stick figure golfer */}
                      <svg viewBox="0 0 100 100" className="w-16 h-16 text-white/30">
                        <circle cx="50" cy="20" r="6" fill="currentColor" />
                        <line x1="50" y1="26" x2="50" y2="55" stroke="currentColor" strokeWidth="2" />
                        <line x1="50" y1="55" x2="38" y2="80" stroke="currentColor" strokeWidth="2" />
                        <line x1="50" y1="55" x2="62" y2="80" stroke="currentColor" strokeWidth="2" />
                        <line x1="50" y1="35" x2="32" y2="45" stroke="currentColor" strokeWidth="2" />
                        <line x1="50" y1="35" x2="75" y2="20" stroke="currentColor" strokeWidth="2" />
                        <line x1="75" y1="20" x2="80" y2="10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                      </svg>
                    </div>
                    {/* Replay progress bar */}
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-neutral-700">
                      <div className="h-full w-3/5 bg-gold rounded-r" />
                    </div>
                  </div>
                  <div className="flex items-center justify-between px-2 py-1">
                    <span className="text-[9px] text-white/40 font-mono">REPLAY</span>
                    <span className="text-[9px] text-gold/60 font-mono">0.5x</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Copy */}
          <div>
            <h2 className="font-serif text-4xl md:text-5xl font-bold text-espresso leading-tight">
              Replay Without{' '}
              <span className="text-gold">Leaving Your Sim</span>
            </h2>
            <p className="mt-6 text-lg text-bronze leading-relaxed">
              The Picture-in-Picture window floats on top of everything — your simulator software,
              launch monitor, any full-screen app. After each shot, your swing replays automatically.
            </p>
            <ul className="mt-8 space-y-4">
              {[
                'Drag and resize the overlay anywhere on screen',
                'Loops automatically — study your swing on repeat',
                'Adjustable playback speed from 0.25x to 2x',
                'Always on top — works with any simulator software',
              ].map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <span className="mt-1.5 w-2 h-2 rounded-full bg-gold flex-shrink-0" />
                  <span className="text-bronze">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
