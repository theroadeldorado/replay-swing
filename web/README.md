# golfcamreplay.com

Marketing website for [Golf Cam Replay](https://github.com/theroadeldorado/golf-cam-replay) — a free, open-source Windows app for recording and analyzing golf swings with audio-triggered capture, multi-camera support, and PiP overlay for golf simulators.

**Live site:** [golfcamreplaycom.vercel.app](https://golfcamreplaycom.vercel.app)

## Tech Stack

- **Next.js 16** (App Router)
- **Tailwind CSS v4**
- **TypeScript**
- **Lucide React** (icons)
- **Vercel** (hosting)

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment Variables

Copy `.env.example` to `.env` and add your GitHub token:

```
GITHUB_TOKEN=your_github_pat_here
```

The token needs **Issues: Read and write** permission on `theroadeldorado/golf-cam-replay`. It's used by:

- **Bug report form** (`/api/bug-report`) — creates GitHub issues from user submissions
- **Download section** — fetches the latest release info from the GitHub API (revalidates hourly)

## Project Structure

```
src/
├── app/
│   ├── layout.tsx              # Root layout, fonts, metadata
│   ├── page.tsx                # Single-page site (all sections)
│   ├── globals.css             # Tailwind theme + custom styles
│   └── api/bug-report/
│       └── route.ts            # GitHub Issues API proxy
├── components/
│   ├── Header.tsx              # Sticky nav with mobile menu
│   ├── Hero.tsx                # Hero with app mockup
│   ├── Features.tsx            # Feature grid (10 cards)
│   ├── HowItWorks.tsx          # 3-step setup guide
│   ├── PipDemo.tsx             # PiP overlay explanation
│   ├── Download.tsx            # Download CTA with GitHub release info
│   ├── Support.tsx             # Venmo donation section
│   ├── BugReport.tsx           # Bug report form
│   └── Footer.tsx              # Footer with links
└── lib/
    └── github.ts               # GitHub API helpers
```

## Deployment

The site auto-deploys to Vercel on push to `main`. To deploy manually:

```bash
vercel --prod
```

Add `GITHUB_TOKEN` in Vercel dashboard under Project Settings > Environment Variables.
