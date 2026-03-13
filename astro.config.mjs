import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  // Deployed on GitHub Pages at https://npatulloca.github.io/nvadotcom/
  // so we must set both `site` and `base` so asset URLs and links
  // include the `/nvadotcom` subpath instead of assuming the domain root.
  site: 'https://npatulloca.github.io/nvadotcom/',
  base: '/nvadotcom',
  build: {
    format: 'directory',
  },
});
