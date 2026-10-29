"use strict";
/* Testes unitários das funções puras do app (node:test). O app é carregado
   num DOM vazio, sem banco, só para expor as funções globais. */
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");

const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const appJs = [...html.matchAll(/<script src="(js\/[^"]+)"/g)]
  .map((m) => fs.readFileSync(path.join(root, m[1]), "utf8"))
  .join("\n");

const { window } = new JSDOM(html, { runScripts: "outside-only", url: "https://example.test/" });
window.fetch = () => new Promise(() => {}); // banco nunca chega: só as funções importam
window.process = { env: process.env }; // o Stryker ativa o mutante por variável de ambiente
window.eval(appJs + "\n;window.__f = { nota, uniq, canon, fmt, shuffle, rich, altc, plural };");
const f = window.__f;

const q = (area, id, extra = {}) => ({ area, id, ...extra });
const itens = (area, acertos, total) =>
  Array.from({ length: total }, (_, i) => [q(area, "x" + i), i < acertos]);

test("nota: extremos da tabela por área", () => {
  assert.equal(f.nota(itens("CN", 0, 45)), 338);
  assert.equal(f.nota(itens("CN", 45, 45)), 887);
  assert.equal(f.nota(itens("MT", 45, 45)), 976);
});

test("nota: simulado menor vai à proporção de 45", () => {
  // 3 de 5 = 27 de 45
  assert.equal(f.nota(itens("CH", 3, 5)), f.nota(itens("CH", 27, 45)));
});

test("nota: interpola entre dois números de acertos", () => {
  // 1 de 2 = 22,5 de 45: meio caminho entre 22 (622) e 23 (631) em CN, arredondado
  assert.equal(f.nota(itens("CN", 1, 2)), 627);
});

test("nota: cresce com os acertos", () => {
  for (const a of ["CN", "CH", "LC", "MT"])
    for (let k = 1; k <= 45; k++) assert.ok(f.nota(itens(a, k, 45)) >= f.nota(itens(a, k - 1, 45)));
});

test("uniq: tira anuladas e equivalentes", () => {
  const lista = [q("CN", "a"), q("CN", "b", { equivale: "a" }), q("CN", "c", { anulada: true }), q("CN", "d")];
  assert.deepEqual(
    f.uniq(lista).map((x) => x.id),
    ["a", "d"]
  );
  assert.equal(f.canon(lista[1]), "a");
});

test("fmt: minutos e segundos com dois dígitos", () => {
  assert.equal(f.fmt(0), "00:00");
  assert.equal(f.fmt(65), "01:05");
  assert.equal(f.fmt(3600), "60:00");
});

test("shuffle: mesma lista, outra ordem possível", () => {
  const a = Array.from({ length: 50 }, (_, i) => i);
  const b = f.shuffle([...a]);
  assert.deepEqual([...b].sort((x, y) => x - y), a);
});

test("rich: parágrafos e figuras com lazy loading", () => {
  const el = f.rich("Um\n\nDois ![fig](img/x.jpg) três");
  assert.deepEqual(
    [...el.querySelectorAll("p")].map((p) => p.textContent),
    ["Um", "Dois", "três"]
  );
  const img = el.querySelector("img");
  assert.equal(img.getAttribute("src"), "img/x.jpg");
  assert.equal(img.getAttribute("loading"), "lazy");
});

test("altc: texto, imagem e texto com imagem", () => {
  assert.equal(f.altc("texto"), "texto");
  assert.equal(f.altc("img:img/a.jpg").getAttribute("src"), "img/a.jpg");
  assert.equal(f.altc("antes ![x](img/b.jpg) depois").querySelectorAll("img").length, 1);
});

test("plural: singular só para 1", () => {
  assert.equal(f.plural(1, "questão", "questões"), "1 questão");
  assert.equal(f.plural(1200, "questão", "questões"), "1.200 questões");
});

test("Sentry: SDK do CDN com versão fixa e hash de integridade", () => {
  const s = window.document.querySelector('script[src*="sentry-cdn"]');
  assert.match(s.src, /\/\d+\.\d+\.\d+\/bundle\.min\.js$/);
  assert.match(s.integrity, /^sha384-/);
  assert.equal(s.crossOrigin, "anonymous");
});
