// Uskladi montažu s glasom: node glas.js <mapa sa 7 snimki 1.*..7.*> [timeline.json]
// Izlaz: glas.m4a (spojeno s kratkim stankama), timeline-glas.json (trajanja po blokovima), titlovi-glas.srt (titlovi pomaknuti na stvarni govor)
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const FF = require('ffmpeg-static');
const REPO = path.resolve(__dirname, '..', '..', '..');
const [, , dir, tlPath = path.join(__dirname, 'timeline.json')] = process.argv;
if (!dir) { console.log('uporaba: node glas.js <mapa sa snimkama 1..7> [timeline.json]'); process.exit(1); }

const STANKA = 0.5;           // stanka između blokova, s
const UVOD = 0.6;             // tišina prije prve riječi
// blokovi scenarija (redoslijed kao naslovi u docs/video-scenarij.md) i njihova planirana vremena, za pomicanje titlova
const BLOKOVI = [
  { n: 1, naziv: 'Problem', plan: [0, 20] },
  { n: 2, naziv: 'Ciljni korisnici', plan: [20, 36] },
  { n: 3, naziv: 'Funkcionalnosti: pregled jedinice', plan: [36, 77] },
  { n: 4, naziv: 'Funkcionalnosti: simulator i Karta reforme', plan: [77, 121] },
  { n: 5, naziv: 'Izvori podataka', plan: [121, 140] },
  { n: 6, naziv: 'Tehnička arhitektura', plan: [140, 160] },
  { n: 7, naziv: 'Korisnička vrijednost i daljnji razvoj', plan: [160, 177] },
];
// koji segment vremenske crte pripada kojem bloku: po natpisu, a natpis 3 dijeli se na pregled (kadrovi 2, 3, 4) i simulator (5, 6)
const blokSegmenta = seg => {
  if (seg.natpis === 1) return 1; if (seg.natpis === 2) return 2;
  if (seg.natpis === 3) return /kadar-(5|6)\./.test(seg.src || '') ? 4 : 3;
  if (seg.natpis === 4) return 5; if (seg.natpis === 5) return 6; return 7;
};

const probe = f => { const r = spawnSync(FF, ['-hide_banner', '-i', f], { encoding: 'utf8' }); const m = /Duration: (\d+):(\d+):([\d.]+)/.exec(r.stderr || ''); if (!m) throw new Error('ne mogu pročitati trajanje: ' + f); return (+m[1]) * 3600 + (+m[2]) * 60 + (+m[3]); };
const run = (args, label) => { const r = spawnSync(FF, ['-hide_banner', '-loglevel', 'error', '-y', ...args], { encoding: 'utf8' }); if (r.status !== 0) { console.error(label + ' nije uspjelo:\n' + r.stderr); process.exit(1); } };

// 1. snimke 1..7
const snimke = BLOKOVI.map(b => { const f = fs.readdirSync(dir).find(x => new RegExp(`^${b.n}\\D`).test(x) || x === String(b.n)); if (!f) { console.error(`nema snimke za blok ${b.n} (${b.naziv}) u ${dir}`); process.exit(1); } return path.join(dir, f); });
const traj = snimke.map(probe);
console.log('trajanja glasa po blokovima: ' + traj.map((t, i) => `${i + 1}: ${t.toFixed(1)} s`).join(', ') + `  ukupno ${traj.reduce((a, b) => a + b, 0).toFixed(1)} s`);

// 2. spoji glas: tišina + blok + stanka ... (glasnoća ujednačena po bloku)
let fc = ''; let concat = '';
snimke.forEach((f, i) => { fc += `[${i}:a]aresample=48000,aformat=channel_layouts=mono,loudnorm=I=-18:TP=-1.5:LRA=9,apad=pad_dur=${STANKA}[a${i}];`; concat += `[a${i}]`; });
fc += `${concat}concat=n=${snimke.length}:v=0:a=1,adelay=${Math.round(UVOD * 1000)}:all=1[aout]`;
const glasOut = path.join(__dirname, 'glas.m4a');
run([...snimke.flatMap(f => ['-i', f]), '-filter_complex', fc, '-map', '[aout]', '-c:a', 'aac', '-b:a', '160k', glasOut], 'spajanje glasa');

// 3. nova trajanja segmenata: svaki blok traje koliko i njegov glas (+ stanka), raspodijeljeno razmjerno planu
const tl = JSON.parse(fs.readFileSync(tlPath, 'utf8'));
const klipTrajanje = {};
const dostupno = seg => { if (!seg.src) return Infinity; const p = path.isAbsolute(seg.src) ? seg.src : fs.existsSync(path.join(__dirname, seg.src)) ? path.join(__dirname, seg.src) : path.join(REPO, seg.src); if (!(p in klipTrajanje)) klipTrajanje[p] = probe(p); return klipTrajanje[p] - (seg.in || 0) - 0.1; };
const pocetci = []; let t0 = UVOD;
BLOKOVI.forEach((b, i) => { const cilj = traj[i] + STANKA + (i === 0 ? UVOD : 0); const segs = tl.filter(s => blokSegmenta(s) === b.n); const plan = segs.reduce((a, s) => a + s.dur, 0); let ostatak = cilj; const fiks = segs.filter(s => s.img); segs.forEach(s => { s.dur = Math.round(s.dur / plan * cilj * 10) / 10; }); let zbroj = segs.reduce((a, s) => a + s.dur, 0); segs[segs.length - 1].dur = Math.round((segs[segs.length - 1].dur + (cilj - zbroj)) * 10) / 10; segs.forEach(s => { const max = dostupno(s); if (s.dur > max) console.warn(`  upozorenje: ${s.src} od ${s.in}s ima samo ${max.toFixed(1)} s, a treba ${s.dur} s; produži snimku ili smanji "in"`); }); pocetci.push({ n: b.n, od: t0, do: t0 + cilj }); t0 += cilj; });
fs.writeFileSync(path.join(__dirname, 'timeline-glas.json'), JSON.stringify(tl, null, 1));
console.log('blokovi u videu: ' + pocetci.map(p => `${p.n}: ${p.od.toFixed(1)}-${p.do.toFixed(1)}`).join(', ') + `  ukupno ${t0.toFixed(1)} s`);

// 4. titlovi: svaki redak pomakni linearno unutar svog bloka
const srtIn = fs.readFileSync(path.join(REPO, 'docs/video/titlovi.srt'), 'utf8').replace(/\r/g, '');
const toS = s => { const m = /(\d+):(\d+):(\d+),(\d+)/.exec(s); return (+m[1]) * 3600 + (+m[2]) * 60 + (+m[3]) + (+m[4]) / 1000; };
const fmt = x => { const h = Math.floor(x / 3600), m = Math.floor(x % 3600 / 60), s = Math.floor(x % 60), ms = Math.round((x - Math.floor(x)) * 1000); return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms).padStart(3, '0')}`; };
const cues = srtIn.trim().split(/\n\s*\n/).map(b => { const l = b.split('\n'); const [a, z] = l[1].split(' --> '); return { a: toS(a), z: toS(z), txt: l.slice(2).join('\n') }; });
const mapT = x => { const b = BLOKOVI.find((bb, i) => x < bb.plan[1] || i === BLOKOVI.length - 1); const p = pocetci[b.n - 1]; const [pa, pz] = b.plan; const u = Math.min(1, Math.max(0, (x - pa) / (pz - pa))); return p.od + u * (p.do - p.od - STANKA); };
const srtOut = cues.map((c, i) => `${i + 1}\n${fmt(mapT(c.a))} --> ${fmt(Math.max(mapT(c.a) + 0.8, mapT(c.z) - 0.08))}\n${c.txt}\n`).join('\n');
fs.writeFileSync(path.join(__dirname, 'titlovi-glas.srt'), srtOut);
console.log(`gotovo: glas.m4a, timeline-glas.json, titlovi-glas.srt (${cues.length} titlova). Dalje: node montaza.js timeline-glas.json fiskalna-karta.mp4 glas.m4a`);
