import { Download as DownloadIcon, ExternalLink } from 'lucide-react';
import { getLatestRelease, formatBytes, AssetInfo } from '@/lib/github';

function WindowsIcon({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M0 3.449L9.75 2.1v9.451H0m10.949-9.602L24 0v11.4H10.949M0 12.6h9.75v9.451L0 20.699M10.949 12.6H24V24l-12.9-1.801" />
    </svg>
  );
}

function AppleIcon({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" />
    </svg>
  );
}

function PlatformCard({
  icon,
  label,
  asset,
  version,
}: {
  icon: React.ReactNode;
  label: string;
  asset: AssetInfo | null;
  version: string | null;
}) {
  return (
    <div className="bg-cream rounded-2xl border border-sand p-8 flex flex-col items-center">
      <div className="flex items-center justify-center gap-2 text-bronze mb-6">
        {icon}
        <span className="text-sm font-medium">{label}</span>
      </div>

      {asset && version ? (
        <>
          <a
            href={asset.downloadUrl}
            className="inline-flex items-center gap-2 bg-green-accent hover:bg-green-hover text-white font-semibold px-8 py-4 rounded transition-colors shadow-lg shadow-green-accent/20 text-lg"
          >
            <DownloadIcon size={22} />
            Download {version}
          </a>
          <p className="mt-4 text-sm text-bronze">
            {asset.fileName} &middot; {formatBytes(asset.fileSize)}
          </p>
        </>
      ) : (
        <a
          href="https://github.com/theroadeldorado/replay-swing/releases/latest"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 bg-green-accent hover:bg-green-hover text-white font-semibold px-8 py-4 rounded transition-colors shadow-lg shadow-green-accent/20 text-lg"
        >
          <DownloadIcon size={22} />
          Download Latest
        </a>
      )}
    </div>
  );
}

export default async function Download() {
  const release = await getLatestRelease();

  return (
    <section id="download" className="py-20 md:py-28 bg-warm-white">
      <div className="mx-auto max-w-7xl px-6">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="font-serif text-4xl md:text-5xl font-bold text-espresso">
            Download ReplaySwing
          </h2>
          <p className="mt-4 text-lg text-bronze">
            Free and open source. No account needed, no strings attached.
          </p>

          <div className="mt-10 grid sm:grid-cols-2 gap-4 max-w-4xl mx-auto">
            <PlatformCard
              icon={<WindowsIcon size={20} />}
              label="Windows 10 / 11"
              asset={release?.windows ?? null}
              version={release?.version ?? null}
            />
            <PlatformCard
              icon={<AppleIcon size={20} />}
              label="macOS"
              asset={release?.mac ?? null}
              version={release?.version ?? null}
            />
          </div>

          <div className="mt-6">
            <a
              href="https://github.com/theroadeldorado/replay-swing/releases"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-gold hover:text-espresso transition-colors font-medium"
            >
              View all releases on GitHub
              <ExternalLink size={14} />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
