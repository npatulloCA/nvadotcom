import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://newvintageamps.com',
  // GitHub Pages may serve from repo root or project subpath; use base only if needed
  // base: '/nvadotcom/',
  build: {
    format: 'directory',
  },
});
