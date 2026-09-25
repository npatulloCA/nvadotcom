import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  // Custom domain (root). If you ever deploy only to github.io/<repo> again,
  // set site to that URL and base to '/<repo-name>'.
  site: 'https://newvintageamps.com/',
  build: {
    format: 'directory',
  },
});
