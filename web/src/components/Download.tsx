import { Download as DownloadIcon, ExternalLink, Monitor } from 'lucide-react';
import { getLatestRelease, formatBytes } from '@/lib/github';

export default async function Download() {
  const release = await getLatestRelease();

  return (
    <section id="download" className="py-20 md:py-28 bg-warm-white">
      <div className="mx-auto max-w-7xl px-6">
        <div className="text-center max-w-2xl mx-auto">
          <h2 className="font-serif text-4xl md:text-5xl font-bold text-espresso">
            Download Golf Cam Replay
          </h2>
          <p className="mt-4 text-lg text-bronze">
            Free and open source. No account needed, no strings attached.
          </p>

          <div className="mt-10 bg-cream rounded-2xl border border-sand p-8 md:p-10 max-w-md mx-auto">
            <div className="flex items-center justify-center gap-2 text-bronze mb-6">
              <Monitor size={20} />
              <span className="text-sm font-medium">Windows 10 / 11</span>
            </div>

            {release ? (
              <>
                <a
                  href={release.downloadUrl}
                  className="inline-flex items-center gap-2 bg-green-accent hover:bg-green-hover text-white font-semibold px-8 py-4 rounded transition-colors shadow-lg shadow-green-accent/20 text-lg"
                >
                  <DownloadIcon size={22} />
                  Download {release.version}
                </a>
                <p className="mt-4 text-sm text-bronze">
                  {release.fileName} &middot; {formatBytes(release.fileSize)}
                </p>
              </>
            ) : (
              <a
                href="https://github.com/theroadeldorado/golf-cam-replay/releases/latest"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 bg-green-accent hover:bg-green-hover text-white font-semibold px-8 py-4 rounded transition-colors shadow-lg shadow-green-accent/20 text-lg"
              >
                <DownloadIcon size={22} />
                Download Latest
              </a>
            )}

            <div className="mt-6 pt-6 border-t border-sand">
              <a
                href="https://github.com/theroadeldorado/golf-cam-replay/releases"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-sm text-gold hover:text-espresso transition-colors font-medium"
              >
                View all releases on GitHub
                <ExternalLink size={14} />
              </a>
            </div>

            <p className="mt-4 text-xs text-bronze/60">macOS &amp; Linux coming soon</p>
          </div>
        </div>
      </div>
    </section>
  );
}
