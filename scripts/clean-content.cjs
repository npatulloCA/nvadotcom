/**
 * Clean content HTML files:
 * 1. Strip inline style attributes
 * 2. Strip WordPress classes (aligncenter, size-full, wp-image-XXX, etc.)
 * 3. Remove excess blank lines (keep max 1 blank)
 * 4. Fix invalid img attributes (max-width, max-height)
 */
const fs = require('fs');
const path = require('path');

const contentDir = path.join(__dirname, '../src/data/content');

function getAllHtmlFiles(dir, files = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) getAllHtmlFiles(full, files);
    else if (e.name.endsWith('.html')) files.push(full);
  }
  return files;
}

function clean(html) {
  html = html.replace(/\s+style="[^"]*"/g, '');
  html = html.replace(/\bclass="([^"]*)"/g, (_, classes) => {
    const kept = classes
      .split(/\s+/)
      .filter(
        (c) =>
          !/^(aligncenter|alignleft|alignright|alignnone)$/.test(c) &&
          !/^size-(full|medium|thumbnail)$/.test(c) &&
          !/^wp-image-\d+$/.test(c) &&
          c !== 'widget_iframe'
      )
      .join(' ')
      .trim();
    return kept ? `class="${kept}"` : '';
  });
  html = html.replace(/\s+class=""\s*/g, ' ');
  html = html.replace(/\s+max-width="[^"]*"/g, '').replace(/\s+max-height="[^"]*"/g, '');
  html = html.replace(/\n{3,}/g, '\n\n');
  return html;
}

const files = getAllHtmlFiles(contentDir);
for (const f of files) {
  let html = fs.readFileSync(f, 'utf-8');
  fs.writeFileSync(f, clean(html), 'utf-8');
  console.log('Processed:', path.relative(contentDir, f));
}
console.log(`Done. Processed ${files.length} files.`);
