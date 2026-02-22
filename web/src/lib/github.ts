export interface ReleaseInfo {
  version: string;
  downloadUrl: string;
  fileName: string;
  fileSize: number;
  publishedAt: string;
  htmlUrl: string;
}

export async function getLatestRelease(): Promise<ReleaseInfo | null> {
  try {
    // Fetch all releases (includes prereleases, which /releases/latest skips)
    const headers: Record<string, string> = {
      Accept: 'application/vnd.github.v3+json',
    };
    if (process.env.GITHUB_TOKEN) {
      headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
    }
    const res = await fetch(
      'https://api.github.com/repos/theroadeldorado/golf-cam-replay/releases?per_page=5',
      {
        headers,
        next: { revalidate: 3600 },
      }
    );

    if (!res.ok) return null;

    const releases = await res.json();

    // Find the first release with an .exe asset
    for (const release of releases) {
      const exeAsset = release.assets?.find(
        (a: { name: string }) => a.name.endsWith('.exe')
      );
      if (exeAsset) {
        return {
          version: release.tag_name,
          downloadUrl: exeAsset.browser_download_url,
          fileName: exeAsset.name,
          fileSize: exeAsset.size,
          publishedAt: release.published_at,
          htmlUrl: release.html_url,
        };
      }
    }

    return null;
  } catch {
    return null;
  }
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}
