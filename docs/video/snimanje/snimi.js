// Snimanje kadrova za video: node snimi.js 1 2 3 ...  (izlaz: kadrovi/kadar-N.webm)
const { chromium } = require('playwright-core');
const path = require('path');
const SITE = 'https://abi-azan.github.io/Datathon-Portala-otvorenih-podataka-2026/';
const OUT = path.join(__dirname, 'kadrovi');

const CURSOR = `(() => {
  const el = document.createElement('div'); el.id = '__kursor';
  el.innerHTML = '<svg width="30" height="38" viewBox="0 0 28 36"><path d="M2 2 L2 28 L9 21 L14 33 L19 31 L14 19 L24 19 Z" fill="#fff" stroke="#111" stroke-width="2" stroke-linejoin="round"/></svg>';
  Object.assign(el.style, { position: 'fixed', left: '0', top: '0', width: '30px', height: '38px', pointerEvents: 'none', zIndex: '2147483647', transform: 'translate(-9999px,-9999px)', filter: 'drop-shadow(0 1px 2px rgba(0,0,0,.45))' });
  const ring = document.createElement('div');
  Object.assign(ring.style, { position: 'fixed', left: '0', top: '0', width: '36px', height: '36px', marginLeft: '-18px', marginTop: '-18px', borderRadius: '50%', border: '3px solid #0f766e', pointerEvents: 'none', zIndex: '2147483646', opacity: '0', transform: 'translate(-9999px,-9999px) scale(.4)' });
  const add = () => { document.documentElement.appendChild(el); document.documentElement.appendChild(ring); };
  if (document.documentElement) add(); else addEventListener('DOMContentLoaded', add);
  document.addEventListener('mousemove', e => { el.style.transform = 'translate(' + (e.clientX - 2) + 'px,' + (e.clientY - 2) + 'px)'; }, true);
  document.addEventListener('mousedown', e => {
    ring.style.transition = 'none'; ring.style.opacity = '.9'; ring.style.transform = 'translate(' + e.clientX + 'px,' + e.clientY + 'px) scale(.4)';
    requestAnimationFrame(() => { ring.style.transition = 'transform .45s ease-out, opacity .45s ease-out'; ring.style.opacity = '0'; ring.style.transform = 'translate(' + e.clientX + 'px,' + e.clientY + 'px) scale(1.4)'; });
  }, true);
})()`;

const ease = t => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t);
let cur = { x: 960, y: 600 };
const hold = (page, ms) => page.waitForTimeout(ms);
async function glide(page, x, y, ms = 700) {
  const n = Math.max(2, Math.round(ms / 16)), sx = cur.x, sy = cur.y;
  for (let i = 1; i <= n; i++) { const e = ease(i / n); await page.mouse.move(sx + (x - sx) * e, sy + (y - sy) * e); await page.waitForTimeout(16); }
  cur = { x, y };
}
async function center(loc) { const b = await loc.boundingBox(); if (!b) throw new Error('nema okvira: ' + loc); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }
async function klik(page, loc, { ms = 700, dx = 0, dy = 0, pause = 250 } = {}) {
  await loc.scrollIntoViewIfNeeded().catch(() => {});
  const c = await center(loc); await glide(page, c.x + dx, c.y + dy, ms); await hold(page, pause);
  await page.mouse.down(); await hold(page, 90); await page.mouse.up(); await hold(page, 150);
}
async function tipkaj(page, text, delay = 95) { for (const ch of text) { await page.keyboard.type(ch); await hold(page, delay + Math.round(Math.random() * 40)); } }
async function klizi(page, top, ms = 1500) {
  await page.evaluate(([top, ms]) => new Promise(r => { const s = window.scrollY, d = top - s, t0 = performance.now(); const f = now => { const t = Math.min(1, (now - t0) / ms), e = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t; window.scrollTo(0, s + d * e); if (t < 1) requestAnimationFrame(f); else r(); }; requestAnimationFrame(f); }), [top, ms]);
}
async function kliziDo(page, loc, offset = 120, ms = 1500) { const b = await loc.boundingBox(); const y = await page.evaluate(() => window.scrollY); await klizi(page, Math.max(0, b.y + y - offset), ms); }
async function zumKotacic(page, x, y, ticks = 10, delta = -40, gap = 110) { await glide(page, x, y, 800); for (let i = 0; i < ticks; i++) { await page.mouse.wheel(0, delta); await hold(page, gap); } }
async function karta(page) { await page.waitForSelector('canvas.maplibregl-canvas', { timeout: 30000 }); await hold(page, 2500); }
async function otvori(page, hash) { await page.goto(SITE + hash, { waitUntil: 'networkidle', timeout: 60000 }); }

const SHOTS = {
  // 1. naslovnica, Pokreni, zum prema Pagu
  1: async page => {
    await otvori(page, '#/'); await karta(page); await hold(page, 1500);
    await glide(page, 600, 171, 500);
    await klik(page, page.getByRole('button', { name: 'Pokreni', exact: true }), { ms: 900 });
    await glide(page, 1180, 90, 600); await hold(page, 8800);
    await zumKotacic(page, 1005, 612, 18, -40, 120); await hold(page, 600); await glide(page, 520, 900, 900); await hold(page, 3500);
  },
  // 2. pretraga "povlj" i pregled Povljane
  2: async page => {
    await otvori(page, '#/'); await karta(page); await hold(page, 800);
    await klik(page, page.getByPlaceholder(/Pronađi svoju/), { ms: 900 });
    await tipkaj(page, 'povlj'); await hold(page, 1300);
    await klik(page, page.getByRole('option').filter({ hasText: 'Povljana' }).first(), { ms: 600 });
    await page.waitForSelector('h1', { timeout: 20000 }); await hold(page, 500);
    await glide(page, 1500, 700, 800); await hold(page, 4000);
    await klizi(page, 520, 2200); await hold(page, 4000);
  },
  // 3. Ukratko: klik na 1.045.908 € i Prikaži izračun
  3: async page => {
    await otvori(page, '#/jedinica/opcina-povljana'); await hold(page, 2500);
    const ukratko = page.getByText('Ukratko', { exact: true }).first();
    await kliziDo(page, ukratko, 110, 1600); await hold(page, 2500);
    const broj = page.locator('button, a').filter({ hasText: '1.045.908' }).first();
    await klik(page, broj, { ms: 900 }); await hold(page, 1800);
    const red = page.getByText(/LU324/).filter({ visible: true }).first();
    try { await red.waitFor({ timeout: 15000 }); const c = await center(red); await glide(page, c.x - 40, c.y + 30, 1200); } catch { await glide(page, 1100, 700, 1200); }
    await hold(page, 5500);
  },
  // 4. Stanovništvo i gospodarstvo, oznaka uživo s API-ja DZS-a
  4: async page => {
    await otvori(page, '#/jedinica/opcina-povljana'); await hold(page, 2000);
    const k = page.getByText('Stanovništvo i gospodarstvo').first();
    await kliziDo(page, k, 140, 1800);
    const oz = page.getByText(/uživo s API-ja DZS/).first(); await oz.waitFor({ timeout: 20000 });
    const c = await center(oz); await glide(page, c.x + 120, c.y + 26, 1000); await hold(page, 6500);
  },
  // 5. simulator: s pregleda Povljane, dodaj Pag
  5: async page => {
    await otvori(page, '#/jedinica/opcina-povljana'); await hold(page, 1500);
    const sim = page.getByRole('link', { name: /Simuliraj spajanje/ }).first();
    await kliziDo(page, sim, 420, 1500); await klik(page, sim, { ms: 900 });
    await karta(page); await hold(page, 1500);
    await klik(page, page.getByPlaceholder(/Dodaj susjednu/), { ms: 900 });
    await tipkaj(page, 'Pag'); await hold(page, 1200);
    await klik(page, page.getByRole('option').filter({ hasText: 'Pag' }).first(), { ms: 600 });
    await hold(page, 1500); await glide(page, 240, 760, 800); await hold(page, 4000);
    await klizi(page, 700, 2400); await hold(page, 4500);
    await klizi(page, 1300, 2400); await hold(page, 4500);
  },
  // 6. Karta reforme: klizač 2.500 -> 5.000 -> 10.000 -> 5.000, prekidač, skupina Paga
  6: async page => {
    await otvori(page, '#/reforma?prag=2500'); await karta(page); await hold(page, 1500);
    const slider = page.locator('input[type=range]').first();
    const sb = await slider.boundingBox(); await glide(page, sb.x + 8, sb.y + sb.height / 2, 900); await hold(page, 250);
    await page.mouse.down(); await hold(page, 90); await page.mouse.up(); await slider.focus(); await hold(page, 900);
    await page.keyboard.press('ArrowRight'); await hold(page, 3500);
    await page.keyboard.press('ArrowRight'); await hold(page, 2500);
    await page.keyboard.press('ArrowLeft'); await hold(page, 2500);
    const sw = page.getByRole('switch').first(); await klik(page, sw, { ms: 900 }); await hold(page, 2500);
    const sel = page.locator('select').first();
    await klik(page, sel, { ms: 800 }); await hold(page, 400);
    const opt = await sel.locator('option').filter({ hasText: /Pag/ }).first().getAttribute('value');
    await sel.selectOption(opt); await hold(page, 600); await glide(page, 240, 800, 800); await hold(page, 5000);
  },
  // 10. naslovnica za "Ciljni korisnici": kursor polako do legende, pa do popisa "Za početak"
  10: async page => {
    await otvori(page, '#/'); await karta(page); await hold(page, 1500);
    const leg = page.getByText('vrlo nestabilno', { exact: false }).first(); const c = await center(leg);
    await glide(page, c.x + 40, c.y - 60, 2200); await hold(page, 3500);
    const zp = page.getByText('ZA POČETAK', { exact: false }).first(); const z = await center(zp).catch(() => ({ x: 420, y: 640 }));
    await glide(page, z.x + 60, z.y + 36, 1800); await hold(page, 2500);
    await glide(page, z.x + 120, z.y + 96, 1400); await hold(page, 4000);
  },
  // 11. naslovnica za kraj: prikaz Tablica pa natrag na kartu
  11: async page => {
    await otvori(page, '#/'); await karta(page); await hold(page, 1200);
    await glide(page, 600, 118, 600);
    await klik(page, page.getByText('Tablica', { exact: true }).first(), { ms: 1000 }); await hold(page, 2500);
    await klizi(page, 450, 2600); await hold(page, 3000);
    await klizi(page, 0, 1400); await klik(page, page.getByText('Karta', { exact: true }).last(), { ms: 900 });
    await glide(page, 520, 900, 900); await hold(page, 5000);
  },
  // 7. Metodologija: ploča Podaci preko API-ja, zatim openapi.json i dcat.jsonld
  7: async page => {
    await otvori(page, '#/metodologija?o=podaci'); await hold(page, 1500);
    const p = page.getByText('Podaci preko API-ja').first(); await kliziDo(page, p, 120, 1600).catch(() => {});
    await page.getByText(/uživo/).first().waitFor({ timeout: 25000 }).catch(() => {});
    await glide(page, 1400, 700, 800); await hold(page, 7000);
    await page.goto(SITE + 'api/v1/openapi.json', { waitUntil: 'load' }); await hold(page, 1200);
    await glide(page, 97, 10, 900); await hold(page, 200); await page.mouse.down(); await hold(page, 90); await page.mouse.up();
    await glide(page, 1500, 600, 700); await hold(page, 3000);
    await page.goto(SITE + 'api/v1/dcat.jsonld', { waitUntil: 'load' }); await hold(page, 3000);
  },
};

(async () => {
  const shots = process.argv.slice(2).map(Number).filter(n => SHOTS[n]);
  if (!shots.length) { console.log('kadrovi: ' + Object.keys(SHOTS).join(' ')); process.exit(1); }
  const browser = await chromium.launch({ headless: true, channel: 'chromium' });
  for (const n of shots) {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1, locale: 'hr-HR', timezoneId: 'Europe/Zagreb', recordVideo: { dir: OUT, size: { width: 1920, height: 1080 } } });
    await ctx.addInitScript(CURSOR);
    const page = await ctx.newPage(); cur = { x: 500, y: 950 };
    const errs = []; page.on('pageerror', e => errs.push(e.message)); page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    const t0 = Date.now(); let err = '';
    try { await page.mouse.move(cur.x, cur.y); await SHOTS[n](page); } catch (e) { err = e.message.split('\n')[0]; }
    const video = page.video(); await ctx.close();
    const dest = path.join(OUT, `kadar-${n}.webm`); await video.saveAs(dest); await video.delete().catch(() => {});
    console.log(`kadar ${n}: ${((Date.now() - t0) / 1000).toFixed(1)} s${err ? '  GREŠKA: ' + err : ''}${errs.length ? '  konzola: ' + errs.slice(0, 2).join(' | ') : ''}`);
  }
  await browser.close();
})();
