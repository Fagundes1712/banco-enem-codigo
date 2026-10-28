"use strict";
/* Checagem rápida sem dependências: sintaxe, tamanho dos arquivos e espelho em site/public. */
const fs = require("node:fs");
const path = require("node:path");
const { execFileSync } = require("node:child_process");

const root = path.join(__dirname, "..");
const LIMITE = 350; // referência de linhas por arquivo de código do toolkit
const ESPELHO = ["index.html", "styles.css", "sw.js", "manifest.json", "icon.svg", "taxonomy.json", "questions.json"];
let falhas = 0;
const erro = (m) => (falhas++, console.log("  ✗ " + m));

const js = fs.readdirSync(path.join(root, "js")).map((f) => "js/" + f);
for (const f of [...js, "sw.js"]) {
  try {
    execFileSync(process.execPath, ["--check", path.join(root, f)], { stdio: "pipe" });
  } catch (e) {
    erro(`${f}: sintaxe inválida\n${e.stderr}`);
  }
  const n = fs.readFileSync(path.join(root, f), "utf8").split("\n").length;
  if (n > LIMITE) erro(`${f}: ${n} linhas (limite ${LIMITE})`);
}

for (const f of [...ESPELHO, ...js]) {
  const a = path.join(root, f);
  const b = path.join(root, "site/public", f);
  if (!fs.existsSync(b) || !fs.readFileSync(a).equals(fs.readFileSync(b)))
    erro(`site/public/${f} difere da raiz (rode npm run mirror)`);
}

// Contratos de arquitetura (docs/architecture.md): scripts clássicos, base.js
// primeiro, todo js/ no index.html e no cache do service worker, dados só em JSON.
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const sw = fs.readFileSync(path.join(root, "sw.js"), "utf8");
const carregados = [...html.matchAll(/<script src="(js\/[^"]+)"( defer)?/g)];
if (carregados[0]?.[1] !== "js/base.js") erro("index.html: js/base.js precisa ser o primeiro script");
for (const f of js) {
  const s = carregados.find((m) => m[1] === f);
  if (!s) erro(`index.html não carrega ${f}`);
  else if (!s[2]) erro(`index.html: ${f} sem defer`);
  if (!sw.includes(`"${f}"`)) erro(`sw.js: ${f} fora de SHELL_ASSETS`);
  const src = fs.readFileSync(path.join(root, f), "utf8");
  if (/^\s*(import|export)\b|\brequire\(/m.test(src)) erro(`${f}: use script clássico, sem import/export/require`);
  if (/\bfetch\(/.test(src) && f !== "js/base.js") erro(`${f}: só js/base.js busca dados (getJSON)`);
}
for (const [f, src] of [["index.html", html], ...js.map((f) => [f, fs.readFileSync(path.join(root, f), "utf8")])])
  if (/"(enunciado|gabarito|alts)"\s*:/.test(src) || /type="application\/(ld\+)?json"/.test(src))
    erro(`${f}: dados embutidos; ficam em questions.json e taxonomy.json`);

console.log(falhas ? `== check: ${falhas} falha(s) ==` : "== check: ok ==");
process.exit(falhas ? 1 : 0);
