// Kadar 8: MCP Inspector, alat scenarij_spajanja za Pag + Povljana. node snimi-mcp.js <url s tokenom>
const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');
const OUT = path.join(__dirname, 'kadrovi');
const URL = process.argv[2];
if (!URL) { console.log('treba URL Inspectora s tokenom'); process.exit(1); }

const CURSOR = fs.readFileSync(path.join(__dirname, 'snimi.js'), 'utf8').match(/const CURSOR = `([\s\S]*?)`;/)[1];
const ease = t => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t);
let cur = { x: 960, y: 700 };
const hold = (page, ms) => page.waitForTimeout(ms);
async function glide(page, x, y, ms = 700) {
  const n = Math.max(2, Math.round(ms / 16)), sx = cur.x, sy = cur.y;
  for (let i = 1; i <= n; i++) { const e = ease(i / n); await page.mouse.move(sx + (x - sx) * e, sy + (y - sy) * e); await page.waitForTimeout(16); }
  cur = { x, y };
}
async function klik(page, loc, { ms = 700, pause = 250 } = {}) {
  const b = await loc.boundingBox(); if (!b) throw new Error('nema okvira');
  await glide(page, b.x + b.width / 2, b.y + b.height / 2, ms); await hold(page, pause);
  await page.mouse.down(); await hold(page, 90); await page.mouse.up(); await hold(page, 150);
}
async function tipkaj(page, text, delay = 110) { for (const ch of text) { await page.keyboard.type(ch); await hold(page, delay + Math.round(Math.random() * 40)); } }

(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'chromium' });
  const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1, locale: 'hr-HR', recordVideo: { dir: OUT, size: { width: 1920, height: 1080 } } });
  await ctx.addInitScript(CURSOR);
  const page = await ctx.newPage(); await page.mouse.move(cur.x, cur.y);
  let err = '';
  try {
    await page.goto(URL, { waitUntil: 'load', timeout: 60000 });
    await page.getByLabel(/Connect or disconnect/).first().waitFor({ timeout: 30000 }); await hold(page, 1500);
    // spoji se na server
    const sw = page.getByLabel(/Connect or disconnect/).first();
    await klik(page, sw, { ms: 900 });
    await page.getByText('Connected', { exact: false }).first().waitFor({ timeout: 30000 }); await hold(page, 1800);
    // Tools
    await klik(page, page.getByText('Tools', { exact: true }).filter({ visible: true }).first(), { ms: 800 }); await hold(page, 1200);
    await klik(page, page.getByRole('button', { name: 'scenarij_spajanja' }), { ms: 800 }); await hold(page, 1500);
    // upis argumenta u uređivač
    const ed = page.getByRole('textbox', { name: /Jedinice/ }).first();
    await klik(page, ed, { ms: 800 }); await hold(page, 300);
    await tipkaj(page, '"05738,03166"'); await hold(page, 900);
    const run = page.getByRole('button', { name: 'Execute Tool' });
    await klik(page, run, { ms: 800 });
    await page.getByText(/83[,.]6/).first().waitFor({ timeout: 30000 }).catch(() => {});
    await hold(page, 1200);
    const res = page.getByText(/83[,.]6/).first();
    const b = await res.boundingBox().catch(() => null);
    if (b) { await glide(page, b.x + b.width + 30, b.y + 10, 900); }
    await hold(page, 6000);
    await page.screenshot({ path: path.join(OUT, 'k8-kraj.png') });
  } catch (e) { err = e.message.split('\n')[0]; await page.screenshot({ path: path.join(OUT, 'k8-greska.png') }).catch(() => {}); }
  const video = page.video(); await ctx.close();
  const dest = path.join(OUT, 'kadar-8.webm'); await video.saveAs(dest); await video.delete().catch(() => {});
  console.log('kadar 8 snimljen' + (err ? '  GREŠKA: ' + err : ''));
  await browser.close();
})();
