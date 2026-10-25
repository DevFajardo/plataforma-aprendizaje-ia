// Monta el video final con FFmpeg: recorta, acelera esperas, compone el PiP de la clase en vivo y encadena con fundidos.
// Uso: node componer.js [salida.mp4]
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const { OUT, CLIPS } = require("./lib");

const FFMPEG = process.env.FFMPEG || "ffmpeg";
const FFPROBE = process.env.FFPROBE || "ffprobe";
const NORM = path.join(OUT, "norm");
fs.mkdirSync(NORM, { recursive: true });
const FADE = 0.5;

// Orden de las escenas y velocidad global (1 = tiempo real)
const ORDEN = [
  ["00_titulo", 1], ["01_landing", 1.2], ["02_docente_panel", 1.15], ["03_generar", 1], ["04_quiz_docente", 1.1],
  ["05_tutor", 1], ["06_publicar", 1.15], ["07_estudiante", 1], ["08_resultados", 1.1], ["09_vivo", 1],
  ["10_coordinador", 1.15], ["11_movil", 1], ["12_cierre", 1],
];

function run(cmd, args) {
  const r = spawnSync(cmd, args, { encoding: "utf8", maxBuffer: 1 << 28 });
  if (r.status !== 0) { console.error(r.stderr.slice(-3000)); throw new Error(cmd + " falló"); }
  return r.stdout;
}
const dur = (f) => parseFloat(run(FFPROBE, ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]));
const leer = (n) => JSON.parse(fs.readFileSync(path.join(CLIPS, n + ".json"), "utf8"));

/** Segmentos [ini, fin, factor] que cubren [desde, hasta] aplicando velocidad global y tramos acelerados. */
function segmentos(desde, hasta, global, acel) {
  const pts = new Set([desde, hasta]);
  for (const [a, b] of acel) { if (a > desde && a < hasta) pts.add(a); if (b > desde && b < hasta) pts.add(b); }
  const p = [...pts].sort((x, y) => x - y);
  const out = [];
  for (let i = 0; i < p.length - 1; i++) {
    const m = (p[i] + p[i + 1]) / 2;
    let f = global;
    for (const [a, b, k] of acel) if (m >= a && m <= b) f = Math.max(f, k || 8);
    out.push([p[i], p[i + 1], f]);
  }
  return out;
}

const SALIDA = (n) => path.join(NORM, n + ".mp4");
const ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", "30", "-an"];

function normalizar(nombre, global) {
  const j = leer(nombre);
  const f = path.join(CLIPS, nombre + ".webm");
  const total = dur(f);
  const segs = segmentos(j.inicio, total - 0.1, global, j.acelerar || []);
  const partes = segs.map(([a, b, k], i) => `[0:v]trim=start=${a.toFixed(3)}:end=${b.toFixed(3)},setpts=(PTS-STARTPTS)/${k}[s${i}]`);
  const cat = segs.map((_, i) => `[s${i}]`).join("") + `concat=n=${segs.length}:v=1:a=0[c]`;
  const movil = nombre === "11_movil";
  const fin = movil
    ? `[c]scale=-2:1000[p];color=c=0x172741:s=1920x1080:r=30[bg];[bg][p]overlay=(W-w)/2:40:shortest=1,format=yuv420p[v]`
    : `[c]scale=1920:1080:flags=lanczos,format=yuv420p[v]`;
  run(FFMPEG, ["-y", "-v", "error", "-i", f, "-filter_complex", partes.join(";") + ";" + cat + ";" + fin, "-map", "[v]", ...ENC, SALIDA(nombre)]);
}

function normalizarVivo() {
  const d = leer("09_vivo_docente"), m = leer("09_vivo_movil");
  const T0 = Math.max(d.t0Epoch + d.inicio * 1000, m.t0Epoch + m.inicio * 1000);
  const sd = (T0 - d.t0Epoch) / 1000, sm = (T0 - m.t0Epoch) / 1000;
  const fd = path.join(CLIPS, "09_vivo_docente.webm"), fm = path.join(CLIPS, "09_vivo_movil.webm");
  const largo = Math.min(dur(fd) - sd, dur(fm) - sm) - 0.2;
  const W = 296, H = 640, B = 8, R = 28;
  const ancho = W + 2 * B, alto = H + 2 * B;
  const mask = `if(gt(gt(abs(W/2-X),W/2-${R})*gt(abs(H/2-Y),H/2-${R})*gt(hypot(abs(W/2-X)-(W/2-${R}),abs(H/2-Y)-(H/2-${R})),${R}),0),0,255)`;
  const fc =
    `[0:v]trim=start=${sd.toFixed(3)}:duration=${largo.toFixed(3)},setpts=PTS-STARTPTS,scale=1920:1080,fps=30[a];` +
    `[1:v]trim=start=${sm.toFixed(3)}:duration=${largo.toFixed(3)},setpts=PTS-STARTPTS,scale=${W}:${H},fps=30,` +
    `pad=${ancho}:${alto}:${B}:${B}:color=0xE88A37,format=yuva420p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':a='${mask}'[b];` +
    `[a][b]overlay=1920-${ancho}-14:150:format=auto,format=yuv420p[v]`;
  run(FFMPEG, ["-y", "-v", "error", "-i", fd, "-i", fm, "-filter_complex", fc, "-map", "[v]", ...ENC, SALIDA("09_vivo")]);
}

function unir(destino) {
  const archivos = ORDEN.map(([n]) => SALIDA(n));
  const durs = archivos.map(dur);
  const ins = archivos.flatMap((f) => ["-i", f]);
  let filt = "", prev = "[0:v]", acum = durs[0];
  for (let i = 1; i < archivos.length; i++) {
    const off = acum - FADE;
    const out = i === archivos.length - 1 ? "[vout]" : `[x${i}]`;
    filt += `${prev}[${i}:v]xfade=transition=fade:duration=${FADE}:offset=${off.toFixed(3)}${out};`;
    prev = out;
    acum += durs[i] - FADE;
  }
  run(FFMPEG, ["-y", "-v", "error", ...ins, "-filter_complex", filt.slice(0, -1), "-map", "[vout]", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
    "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", "-an", destino]);
  // Tiempos de inicio de cada escena en el video final (para el guion)
  let t = 0;
  const tiempos = ORDEN.map(([n], i) => { const ini = t; t += durs[i] - FADE; return [n, ini.toFixed(1)]; });
  fs.writeFileSync(path.join(OUT, "tiempos.json"), JSON.stringify(tiempos, null, 1));
  console.log("duración total", (acum).toFixed(1), "s");
  console.log(tiempos.map(([n, s]) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")} ${n}`).join("\n"));
}

(() => {
  const destino = path.resolve(process.argv[2] || path.join(OUT, "demo_plataforma.mp4"));
  for (const [n, g] of ORDEN) {
    if (n === "09_vivo") normalizarVivo();
    else normalizar(n, g);
    console.log("normalizado", n);
  }
  unir(destino);
  console.log("listo:", destino);
})();
