import { Download as DownloadIcon, ExternalLink } from 'lucide-react';
import { getLatestRelease, formatBytes } from '@/lib/github';
import DownloadButton from './DownloadButton';

function WindowsIcon({ size = 20 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M0 3.449L9.75 2.1v9.451H0m10.949-9.602L24 0v11.4H10.949M0 12.6h9.75v9.451L0 20.699M10.949 12.6H24V24l-12.9-1.801" />
    </svg>
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

          <div className="mt-10 flex justify-center">
            <div className="bg-cream rounded-2xl border border-sand p-8 flex flex-col items-center max-w-md w-full">
              <div className="flex items-center justify-center gap-2 text-bronze mb-6">
                <WindowsIcon size={20} />
                <span className="text-sm font-medium">Windows 10 / 11</span>
              </div>

              {release?.windows && release.version ? (
                <>
                  <DownloadButton
                    href={release.windows.downloadUrl}
                    version={release.version}
                    fileName={release.windows.fileName}
                  />
                  <p className="mt-4 text-sm text-bronze">
                    {release.windows.fileName} &middot; {formatBytes(release.windows.fileSize)}
                  </p>
                </>
              ) : (
                <DownloadButton
                  href="https://github.com/theroadeldorado/replay-swing/releases/latest"
                  fallback
                />
              )}
            </div>
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
