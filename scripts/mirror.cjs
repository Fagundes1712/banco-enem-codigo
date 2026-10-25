"use strict";
/* Espelha o app em site/public sem depender de rm/cp (funciona no Windows). */
const fs = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");
const destino = path.join(root, "site/public");
const ESPELHO = ["index.html", "styles.css", "sw.js", "manifest.json", "icon.svg", "taxonomy.json", "questions.json"];

fs.rmSync(path.join(destino, "js"), { recursive: true, force: true });
fs.rmSync(path.join(destino, "app.js"), { force: true });
for (const f of ESPELHO) fs.copyFileSync(path.join(root, f), path.join(destino, f));
fs.cpSync(path.join(root, "js"), path.join(destino, "js"), { recursive: true });

console.log(`== mirror: ${ESPELHO.length} arquivos + js/ em site/public ==`);
