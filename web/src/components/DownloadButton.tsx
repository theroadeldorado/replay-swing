'use client';

import { Download as DownloadIcon } from 'lucide-react';

declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
  }
}

function trackDownload(fileName?: string, version?: string) {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'file_download', {
      file_name: fileName ?? 'unknown',
      file_extension: '.exe',
      link_text: `Download ${version ?? 'Latest'}`,
    });
  }
}

export default function DownloadButton({
  href,
  version,
  fileName,
  fallback,
}: {
  href: string;
  version?: string;
  fileName?: string;
  fallback?: boolean;
}) {
  return (
    <a
      href={href}
      {...(fallback ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
      onClick={() => trackDownload(fileName, version)}
      className="inline-flex items-center gap-2 bg-green-accent hover:bg-green-hover text-white font-semibold px-8 py-4 rounded transition-colors shadow-lg shadow-green-accent/20 text-lg"
    >
      <DownloadIcon size={22} />
      Download {version ?? 'Latest'}
    </a>
  );
}
