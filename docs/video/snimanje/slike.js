// Natpisi (prozirni PNG 1920x1080) i shema arhitekture kao PNG, s fontovima stranice.
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');
const REPO = path.resolve(__dirname, '..', '..', '..');
const OUT = path.join(__dirname, 'slike');
fs.mkdirSync(OUT, { recursive: true });
const font = (p) => 'file:///' + path.join(REPO, 'web/node_modules/@fontsource-variable', p).replace(/\\/g, '/');
const CSS = `
@font-face { font-family: 'Public Sans'; font-style: normal; font-weight: 100 900; src: url('${font('public-sans/files/public-sans-latin-ext-wght-normal.woff2')}') format('woff2'), url('${font('public-sans/files/public-sans-latin-wght-normal.woff2')}') format('woff2'); }
@font-face { font-family: 'Source Serif 4'; font-style: normal; font-weight: 200 900; src: url('${font('source-serif-4/files/source-serif-4-latin-ext-wght-normal.woff2')}') format('woff2'), url('${font('source-serif-4/files/source-serif-4-latin-wght-normal.woff2')}') format('woff2'); }
html, body { margin: 0; width: 1920px; height: 1080px; }`;

const NATPISI = ['Problem', 'Ciljni korisnici', 'Funkcionalnosti', 'Izvori podataka', 'Tehnička arhitektura', 'Korisnička vrijednost', 'Daljnji razvoj'];

(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'chromium' });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  // natpisi: tamna pločica dolje lijevo
  for (let i = 0; i < NATPISI.length; i++) {
    const html = `<!doctype html><html><head><meta charset="utf-8"><style>${CSS}
      body { background: transparent; position: relative; }
      .n { position: absolute; left: 48px; bottom: 44px; background: #0b0b0b; color: #faf9f6; font: 600 24px/1 'Public Sans', sans-serif; letter-spacing: 2.6px; text-transform: uppercase; padding: 16px 22px 15px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,.22); }
      .n b { color: #7fd1c0; font-weight: 600; margin-right: 10px; }
    </style></head><body><div class="n"><b>${i + 1}/7</b>${NATPISI[i]}</div></body></html>`;
    await page.setContent(html); await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(OUT, `natpis-${i + 1}.png`), omitBackground: true });
  }
  // pitanje asistentu za MCP kadar (dolje desno)
  await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>${CSS}
    body { background: transparent; position: relative; }
    .p { position: absolute; right: 48px; bottom: 44px; max-width: 980px; background: #faf9f6; border: 1.5px solid #dedcd5; color: #0b0b0b; font: 400 26px/1.35 'Public Sans', sans-serif; padding: 16px 24px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,.18); }
    .p b { font-weight: 600; color: #087664; }
  </style></head><body><div class="p"><b>Pitanje asistentu:</b> „Što bi bilo da se Povljana spoji s Pagom?” → MCP alat <b>scenarij_spajanja</b></div></body></html>`);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(OUT, 'natpis-pitanje.png'), omitBackground: true });
  // shema arhitekture 1920x1080
  const svg = fs.readFileSync(path.join(REPO, 'docs/arhitektura.svg'), 'utf8').replace(/<\?xml[^>]*>/, '');
  await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>${CSS}
    body { background: #faf9f6; display: grid; place-items: center; }
    svg { width: 1792px; height: 1008px; display: block; }
  </style></head><body>${svg}</body></html>`);
  await page.evaluate(() => document.fonts.ready); await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(OUT, 'arhitektura.png') });
  await browser.close();
  console.log('gotovo: ' + fs.readdirSync(OUT).join(', '));
})();
