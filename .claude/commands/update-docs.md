# /update-docs — Sync documentation with current app code

Read all app source files, build a feature inventory, and update documentation to match. Optionally update homepage components.

**Argument:** `$ARGUMENTS` (pass `homepage` to also update Features.tsx and HowItWorks.tsx)

## Step 1: Read all app source files

Read every Python source file to build a complete inventory:

```
app/swing_capture.py    — keyboard shortcuts, UI tabs, dialogs, state machine
app/camera_engine.py    — camera types, transforms, network camera protocols
app/audio_engine.py     — audio features, classifier modes, thresholds
app/recording.py        — buffer sizes, clip saving, session structure
app/config.py           — all config fields, defaults, ranges
app/drawing_overlay.py  — shape types, tools, coordinate system
app/comparison_view.py  — comparison controls, frame offset
app/ui_components.py    — PiP window, gallery, video player
```

Extract:
- All keyboard shortcuts (key → action mappings from `keyPressEvent`)
- All config dataclass fields with defaults, min/max ranges
- Camera setup options (USB backends, network protocols, transform types)
- Audio features list, classifier modes, scoring rules
- Recording workflow (pre/post buffer, trigger flow)
- Playback controls and speed options
- PiP window capabilities
- Drawing tool types and operations
- Comparison view controls
- Session folder structure and metadata format

## Step 2: Read existing documentation

Read these files:
- `web/src/data/docs.ts` — current docs page content
- `app/README.md` — current app README

Compare against the inventory from Step 1. Identify sections that need updating.

## Step 3: Update `web/src/data/docs.ts`

Update the content of any section where the code inventory differs from what's documented. The file has 13 sections:

1. `getting-started` — prerequisites, installation, first launch
2. `camera-setup` — USB cameras, multi-camera, per-camera transforms
3. `phone-as-camera` — DroidCam, IP Webcam, EpocCam, custom URL
4. `audio-trigger` — heuristic vs learned classifier, threshold, mic tips
5. `recording` — arm/disarm, manual trigger, pre-buffer + post-trigger timing
6. `playback` — looping, speed control, frame stepping, multi-camera view
7. `pip` — overlay, drag/resize, always-on-top, simulator integration
8. `drawing-tools` — line/circle tools, select/move/delete, persistence
9. `swing-comparison` — side-by-side sync, frame offset
10. `session-management` — folders, thumbnails, gallery, clip operations
11. `keyboard-shortcuts` — complete table from code
12. `settings` — config options, file locations, auto-save
13. `troubleshooting` — camera, audio, video, PyAudio, general tips

Each section has: `id`, `title`, `iconName` (lucide-react icon name), `content` (HTML string).

**Content format rules:**
- Use HTML (not markdown) — `<h3>`, `<p>`, `<ul>`, `<ol>`, `<table>`, `<code>`, `<kbd>`, `<pre><code>`
- Use `&mdash;`, `&ndash;`, `&times;`, `&rarr;`, `&larr;`, `&asymp;` for typographic characters
- Use `<kbd>Space</kbd>`, `<kbd>A</kbd>` etc. for keyboard keys
- Use `<code>...</code>` for file paths, config values, commands
- Use `<strong>...</strong>` for emphasis within prose
- Tables: `<table><thead><tr><th>...</th></tr></thead><tbody><tr><td>...</td></tr></tbody></table>`

## Step 4: Update `app/README.md`

Sync the README with the same inventory. The README should cover:
- Feature list (matching current capabilities)
- Installation (prerequisites, setup, PyAudio)
- Usage (basic workflow)
- Keyboard shortcuts (complete table from code)
- Camera setup (USB + phone apps)
- Audio trigger (classifier modes, threshold, tips)
- Drawing tools (tool table, usage)
- Swing comparison (brief description)
- PiP (brief description)
- File organisation (folder structure)
- Troubleshooting (camera, audio, video, PyAudio, PiP, drawings)
- Settings reference (config table with defaults and ranges)

## Step 5: (Optional) Update homepage components

Only if `$ARGUMENTS` contains `homepage`:

- **`web/src/components/Features.tsx`** — Update the `features` array if any feature title/description no longer matches the code. Keep exactly 10 features, same icon imports.
- **`web/src/components/HowItWorks.tsx`** — Update the `steps` array if the workflow has changed. Keep exactly 3 steps.

Do NOT modify these files unless `homepage` was passed as an argument.

## Step 6: Verify navigation links

Check that `web/src/components/Header.tsx` has a `{ label: 'Docs', href: '/docs' }` entry in `navLinks` (after "How It Works", before "Download"). If missing, add it.

Check that `web/src/components/Footer.tsx` has a `{ label: 'Docs', href: '/docs', icon: BookOpen, external: false }` entry in `links`. If missing, add it (with `BookOpen` import from lucide-react).

## Step 7: Print summary

Print a summary showing:
- Number of docs sections updated vs unchanged
- Whether app/README.md was updated
- Whether homepage components were updated (if `homepage` flag was passed)
- Whether nav links were added

Format:
```
## /update-docs summary

| Target | Status |
|--------|--------|
| web/src/data/docs.ts | Updated 3 of 13 sections (camera-setup, audio-trigger, keyboard-shortcuts) |
| app/README.md | Updated |
| Header.tsx nav link | Already present |
| Footer.tsx nav link | Already present |
| Features.tsx | Skipped (no `homepage` flag) |
| HowItWorks.tsx | Skipped (no `homepage` flag) |
```
