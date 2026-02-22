import {
  AudioLines,
  PictureInPicture2,
  Smartphone,
  Camera,
  RotateCcw,
  PenTool,
  Columns2,
  BrainCircuit,
  FolderOpen,
  Heart,
} from 'lucide-react';

const features = [
  {
    icon: AudioLines,
    title: 'Audio-Triggered Capture',
    description:
      'Detects the sound of club impact and automatically records 2 seconds before and 4 seconds after — hands-free.',
  },
  {
    icon: PictureInPicture2,
    title: 'Picture-in-Picture Overlay',
    description:
      'Drag a floating replay window on top of your golf simulator. No alt-tabbing, no interruption.',
  },
  {
    icon: Smartphone,
    title: 'Use Your Phone as a Camera',
    description:
      'Turn any phone into a wireless camera with free apps like DroidCam or EpocCam. No extra hardware needed.',
  },
  {
    icon: Camera,
    title: 'Multi-Camera Support',
    description:
      'Record from multiple angles at once — USB cameras, phones, or network cameras. Switch views instantly.',
  },
  {
    icon: RotateCcw,
    title: 'Instant Replay',
    description:
      'Looping playback starts automatically after every shot. Adjust speed to study your form in detail.',
  },
  {
    icon: PenTool,
    title: 'Drawing Tools',
    description:
      'Annotate your swings with lines and circles to highlight key positions and angles.',
  },
  {
    icon: Columns2,
    title: 'Swing Comparison',
    description:
      'Side-by-side synchronized playback lets you compare swings and track improvement over time.',
  },
  {
    icon: BrainCircuit,
    title: 'Smart Detection',
    description:
      'AI audio classifier learns the unique sounds of your environment for more accurate trigger detection.',
  },
  {
    icon: FolderOpen,
    title: 'Session Management',
    description:
      'Organized shot gallery with thumbnails. Browse, replay, and manage recordings from every session.',
  },
  {
    icon: Heart,
    title: 'Free & Open Source',
    description: 'MIT licensed. No subscriptions, no accounts, no data collection. Yours forever.',
  },
];

export default function Features() {
  return (
    <section id="features" className="py-20 md:py-28">
      <div className="mx-auto max-w-7xl px-6">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="font-serif text-4xl md:text-5xl font-bold text-espresso">
            Everything You Need
          </h2>
          <p className="mt-4 text-lg text-bronze">
            Built specifically for golf simulator setups. Every feature designed to help you improve
            without leaving your bay.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-warm-white rounded-2xl p-6 border border-sand/60 hover:border-tan/60 transition-colors shadow-sm hover:shadow-md hover:shadow-tan/10"
            >
              <div className="w-12 h-12 rounded-xl bg-cream flex items-center justify-center mb-4">
                <feature.icon size={24} className="text-gold" />
              </div>
              <h3 className="font-semibold text-lg text-espresso mb-2">{feature.title}</h3>
              <p className="text-bronze text-sm leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
