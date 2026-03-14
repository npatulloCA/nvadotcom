# New Vintage Amplifiers — static site

Static rebuild of [newvintageamps.com](https://newvintageamps.com) using [Astro](https://astro.build), designed to deploy to **GitHub Pages** (or any static host).

## What’s in this repo

- **Content:** Extracted from the WordPress WXR export (`_support/newvintageamplifiers.WordPress.2026-03-13.xml`) into `src/data/pages.json` (metadata), `src/data/content/` (HTML per page), and `src/data/nav.json`. Shop, cart, checkout, and customizer pages are excluded.
- **Images:** Stored in `wordpress-uploads/` and copied into `public/uploads/` at build time so the site can serve them.
- **Site:** Astro app in `src/` with layout, nav, footer, and dynamic pages driven by the extracted data.

## Prerequisites

- **Node.js** 18+ and npm
- **Python 3** (only if you re-run content extraction)

## Commands

| Command | Description |
|--------|-------------|
| `npm install` | Install dependencies |
| `npm run dev` | Start dev server at `http://localhost:4321` |
| `npm run build` | Copy uploads into `public/uploads/` and build the site into `dist/` |
| `npm run preview` | Serve the built `dist/` locally |
| `npm run extract` | Re-run the WordPress XML extraction and write `src/data/pages.json` and `nav.json` (requires Python 3) |

## Deploying to GitHub Pages

1. **Enable GitHub Pages**
   - In the repo: **Settings → Pages**
   - Under “Build and deployment”, set **Source** to **GitHub Actions**.

2. **Push to `main`**
   - The workflow in `.github/workflows/deploy.yml` runs on push to `main`.
   - It installs deps, copies `wordpress-uploads/` into `public/uploads/`, runs `npm run build`, and deploys the `dist/` artifact to GitHub Pages.

**If you see "Get Pages site failed" or "HttpError: Not Found":** GitHub Pages is not enabled or the source is wrong. In the repo go to **Settings** → **Pages** (under Code and automation). Under **Build and deployment**, set **Source** to **GitHub Actions**, then save. Re-run the workflow after that.

**If the build failed with “Dependencies lock file is not found”:** The workflow no longer requires a lockfile; it uses `npm install` without caching. To get faster, reproducible installs, run `npm install` locally, commit `package-lock.json`, then in `.github/workflows/deploy.yml` you can add back `cache: "npm"` under the Setup Node step and use `npm ci` instead of `npm install`.  
**If you see a Node.js deprecation warning:** The workflow uses `actions/setup-node@v4` with Node 20; that’s the current recommended setup. Warnings about older Node versions (e.g. 16) can be ignored.

3. **Custom domain (newvintageamps.com)**
   - In **Settings → Pages**, set **Custom domain** to `newvintageamps.com`.
   - At your DNS provider, add the record GitHub shows (usually a CNAME for `www` or an A record for the apex).
   - Wait for DNS to propagate; GitHub will then offer HTTPS for the custom domain.

## Project layout

```
├── _support/                # Tooling and source data (not part of the built site)
│   ├── content-data/        # Default extract output (orphan; use src/data instead)
│   ├── newvintageamplifiers.WordPress.2026-03-13.xml
│   └── scripts/
│       ├── extract-content.py
│       └── download_wordpress_images.py
├── src/
│   ├── components/          # Nav, Footer
│   ├── data/                # pages.json, nav.json (generated)
│   ├── layouts/
│   │   └── Layout.astro
│   ├── pages/
│   │   ├── index.astro      # Home
│   │   ├── [...slug].astro  # All other pages
│   │   └── 404.astro
│   └── styles/
│       └── global.css
├── public/
│   ├── uploads/             # Populated at build from wordpress-uploads/
│   └── favicon.svg
├── wordpress-uploads/       # Extracted images (in repo)
├── astro.config.mjs
└── package.json
```

## Re-extracting content

If you replace or update the WordPress export XML:

1. Put the new XML in `_support/` (or point the script at it).
2. Run: `npm run extract` (or `python3 _support/scripts/extract-content.py src/data`).
3. Commit the updated `src/data/pages.json`, `src/data/content/`, and `src/data/nav.json`.
4. Rebuild and deploy as usual.
