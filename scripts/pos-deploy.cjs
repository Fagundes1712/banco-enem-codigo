"use strict";
/* Confere o site publicado: espera o sw.js no ar ter a mesma VERSION do local e checa as páginas e dados. */
const fs = require("node:fs");
const path = require("node:path");

const SITE = (process.env.SITE_URL || "https://fagundes1712.github.io/banco-enem-app/").replace(/\/?$/, "/");
const ESPERA_MS = Number(process.env.ESPERA_MS || 600000); // o Pages costuma levar 1 a 3 minutos
const versao = (txt) => (txt.match(/const VERSION = "([^"]+)"/) || [])[1];

const local = versao(fs.readFileSync(path.join(__dirname, "../site/public/sw.js"), "utf8"));
if (!local) throw new Error("VERSION não encontrada em site/public/sw.js");

async function pegar(arquivo) {
  const r = await fetch(SITE + arquivo + "?t=" + Date.now(), { cache: "no-store" });
  if (!r.ok) throw new Error(`${arquivo}: HTTP ${r.status}`);
  return r.text();
}

(async () => {
  const fim = Date.now() + ESPERA_MS;
  let noAr;
  while ((noAr = versao(await pegar("sw.js").catch(() => ""))) !== local) {
    if (Date.now() > fim) {
      console.log(`✗ no ar: ${noAr || "?"}, esperado: ${local} (${SITE})`);
      process.exit(1);
    }
    await new Promise((ok) => setTimeout(ok, 15000));
  }
  const html = await pegar("index.html");
  if (!html.includes("<title>")) throw new Error("index.html sem <title>");
  const q = JSON.parse(await pegar("questions.json"));
  const n = Array.isArray(q) ? q.length : Object.keys(q).length;
  if (!n) throw new Error("questions.json vazio");
  JSON.parse(await pegar("taxonomy.json"));
  console.log(`== pós-deploy: ok (${SITE}, ${local}, questions.json com ${n} entradas) ==`);
})().catch((e) => {
  console.log("✗ " + e.message);
  process.exit(1);
});
