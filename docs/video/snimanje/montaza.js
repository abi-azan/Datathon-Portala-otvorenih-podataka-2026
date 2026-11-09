// Montaža: node montaza.js timeline.json izlaz.mp4 [glas.m4a]
// timeline.json: [{ "src": "kadrovi/kadar-1.webm", "in": 4.5, "dur": 14, "natpis": 1 }, { "img": "slike/arhitektura.png", "dur": 6, "natpis": 5 }, ...]
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const FF = require('ffmpeg-static');
const REPO = path.resolve(__dirname, '..', '..', '..');
const [, , tlPath, outPath, glas] = process.argv;
if (!tlPath || !outPath) { console.log('uporaba: node montaza.js timeline.json izlaz.mp4 [glas.m4a]'); process.exit(1); }
const tl = JSON.parse(fs.readFileSync(tlPath, 'utf8'));
const work = path.join(__dirname, 'montaza'); fs.mkdirSync(work, { recursive: true });
const abs = p => (path.isAbsolute(p) ? p : fs.existsSync(path.join(__dirname, p)) ? path.join(__dirname, p) : path.join(REPO, p));
const run = (args, label) => { const r = spawnSync(FF, ['-hide_banner', '-loglevel', 'error', '-y', ...args], { encoding: 'utf8' }); if (r.status !== 0) { console.error(label + ' nije uspjelo:\n' + r.stderr); process.exit(1); } };

// 1. normalizirani segmenti
const list = []; let t = 0; const ranges = [];
tl.forEach((seg, i) => {
  const out = path.join(work, `seg-${String(i + 1).padStart(2, '0')}.mp4`);
  const vf = 'scale=1920:1080:flags=lanczos,fps=25,format=yuv420p';
  if (seg.img) run(['-loop', '1', '-framerate', '25', '-t', String(seg.dur), '-i', abs(seg.img), '-vf', vf, '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', out], `slika ${seg.img}`);
  else run(['-ss', String(seg.in || 0), '-t', String(seg.dur), '-i', abs(seg.src), '-an', '-vf', vf, '-c:v', 'libx264', '-preset', 'fast', '-crf', '16', out], `isječak ${seg.src}`);
  list.push(`file '${out.replace(/\\/g, '/')}'`);
  if (seg.natpis) { const file = path.join(__dirname, 'slike', `natpis-${seg.natpis}.png`); const last = ranges.filter(r => r.pad).pop(); if (last && last.file === file && Math.abs(last.b - t) < 0.01) last.b = t + seg.dur; else ranges.push({ file, a: t, b: t + seg.dur, pad: 0.3 }); }
  if (seg.slika) ranges.push({ file: abs(seg.slika), a: t + 0.4, b: t + seg.dur - 0.2, pad: 0 });
  t += seg.dur;
});
const total = t;
fs.writeFileSync(path.join(work, 'popis.txt'), list.join('\n'));
const spojeno = path.join(work, 'spojeno.mp4');
run(['-f', 'concat', '-safe', '0', '-i', path.join(work, 'popis.txt'), '-c', 'copy', spojeno], 'spajanje');

// 2. natpisi, fade, zvuk
const inputs = ['-i', spojeno];
const files = [...new Set(ranges.map(r => r.file))];
files.forEach(f => inputs.push('-loop', '1', '-framerate', '25', '-t', String(total), '-i', f));
let fc = `[0:v]fade=t=in:st=0:d=0.5,fade=t=out:st=${(total - 1).toFixed(2)}:d=1[v0]`; let cur = 'v0';
ranges.forEach((r, k) => { const idx = files.indexOf(r.file) + 1; const nxt = `v${k + 1}`; fc += `;[${cur}][${idx}:v]overlay=0:0:format=auto:enable='between(t,${(r.a + r.pad).toFixed(2)},${(r.b - r.pad).toFixed(2)})'[${nxt}]`; cur = nxt; });
let audioArgs;
if (glas) { inputs.push('-i', abs(glas)); fc += `;[${files.length + 1}:a]aresample=48000,apad[aout]`; audioArgs = ['-map', '[aout]', '-c:a', 'aac', '-b:a', '160k']; }
else { inputs.push('-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo'); audioArgs = ['-map', `${files.length + 1}:a`, '-c:a', 'aac', '-b:a', '96k']; }
run([...inputs, '-filter_complex', fc, '-map', `[${cur}]`, ...audioArgs, '-shortest', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', outPath], 'završni izvoz');
const m = Math.floor(total / 60), s = (total % 60).toFixed(1);
console.log(`gotovo: ${outPath}  trajanje ${m}:${s.padStart(4, '0')} (${tl.length} segmenata, preklopi: ${ranges.map(r => `${path.basename(r.file)}@${r.a.toFixed(1)}-${r.b.toFixed(1)}`).join(' ')})`);
