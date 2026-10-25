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

console.log(falhas ? `== check: ${falhas} falha(s) ==` : "== check: ok ==");
process.exit(falhas ? 1 : 0);
