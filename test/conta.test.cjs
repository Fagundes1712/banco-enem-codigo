"use strict";
/* Telas de conta (js/conta.js) em jsdom, com a API simulada. Não é artefato do site. */
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");

const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const appJs = [...html.matchAll(/<script src="(js\/[^"]+)"/g)]
  .map((m) => fs.readFileSync(path.join(root, m[1]), "utf8"))
  .join("\n");
const banco = JSON.parse(fs.readFileSync(path.join(root, "questions.json"), "utf8"));
const tax = JSON.parse(fs.readFileSync(path.join(root, "taxonomy.json"), "utf8"));
const API = "https://api.exemplo.test";
const tick = (ms) => new Promise((r) => setTimeout(r, ms));

let pass = 0;
let fail = 0;
function ok(nome, cond) {
  cond ? pass++ : fail++;
  console.log((cond ? "  ok   " : "  FAIL ") + nome);
}

// API falsa: guarda os pedidos e responde conforme o estado da sessão.
function sobe(url, comApi = true) {
  const pagina = comApi ? html.replace('name="api-url" content=""', `name="api-url" content="${API}"`) : html;
  const dom = new JSDOM(pagina, { runScripts: "outside-only", url, pretendToBeVisual: true });
  const w = dom.window;
  const pedidos = [];
  let logado = false;
  const responde = (status, d) => Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(d) });
  w.fetch = (u, op = {}) => {
    u = String(u);
    if (!u.startsWith(API)) return responde(200, u.includes("taxonomy") ? tax : banco);
    const rota = u.slice(API.length);
    pedidos.push({ rota, corpo: op.body ? JSON.parse(op.body) : null, credentials: op.credentials });
    if (rota === "/me") return logado ? responde(200, { email: "a@b.com", assinatura_ativa: false, assinatura_ate: null }) : responde(401, {});
    if (rota === "/auth/refresh") return responde(401, {});
    if (rota === "/auth/login") return (logado = true), responde(200, { mensagem: "ok" });
    if (rota === "/planos") return responde(200, [{ id: "mensal", centavos: 2499, dias: 30 }, { id: "anual", centavos: 23988, dias: 365 }]);
    if (rota === "/pagamentos") return responde(200, { url: "https://pay.exemplo/bill_1" });
    if (rota === "/auth/confirmar") return responde(200, { mensagem: "E-mail confirmado. Agora é só entrar." });
    // Token de acesso vencido: estas duas respondem 401 para testar a renovação.
    if (rota === "/pagamentos/sincronizar" || rota === "/conta/dados") return responde(401, {});
    return responde(404, {});
  };
  w.scrollTo = () => {};
  w.turnstile = { render: (_el, o) => (o.callback("tok"), 1), reset: () => {} };
  w.eval(appJs + "\n;window.__api = api;");
  return { w, d: w.document, pedidos };
}

// O script do Turnstile não carrega em jsdom: dispara o load à mão.
function carregaTurnstile(d) {
  for (const s of d.querySelectorAll('script[src*="turnstile"]')) s.dispatchEvent(new d.defaultView.Event("load"));
}

(async () => {
  console.log("\n== Conta ==");
  const sem = sobe("https://example.test/", false);
  await tick(60);
  ok("sem api-url o botão Conta fica escondido", sem.d.getElementById("nav-conta").hidden === true);

  const { w, d, pedidos } = sobe("https://example.test/");
  await tick(60);
  const nav = d.getElementById("nav-conta");
  ok("com api-url o botão Conta aparece", nav.hidden === false);
  nav.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await tick(800);
  carregaTurnstile(d);
  await tick(20);
  ok("sem sessão abre a tela de entrar", d.querySelector("h1").textContent === "Entrar");
  ok("cookies vão junto nos pedidos", pedidos.every((p) => p.credentials === "include"));
  ok("nenhum token é guardado no navegador", w.localStorage.length === 0 || !JSON.stringify({ ...w.localStorage }).includes("tok"));

  d.querySelector('input[name="email"]').value = "a@b.com";
  d.querySelector('input[name="senha"]').value = "senha-forte-1";
  d.querySelector("form").dispatchEvent(new w.Event("submit", { cancelable: true }));
  await tick(800);
  const login = pedidos.find((p) => p.rota === "/auth/login");
  ok("login manda e-mail, senha e o token do Turnstile", login && login.corpo.email === "a@b.com" && login.corpo.turnstile === "tok");
  ok("depois de entrar mostra a conta", d.querySelector("h1").textContent === "Sua conta");
  const mensal = [...d.querySelectorAll("button")].find((b) => /^Mensal/.test(b.textContent));
  ok("preço vem da API", mensal && mensal.textContent.includes("24,99"));
  mensal.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await tick(20);
  const pg = pedidos.find((p) => p.rota === "/pagamentos");
  ok("assinar manda só o plano", pg && JSON.stringify(pg.corpo) === '{"plano":"mensal"}');

  const antes = pedidos.filter((p) => p.rota === "/auth/refresh").length;
  await Promise.all([w.__api("/pagamentos/sincronizar", {}), w.__api("/conta/dados")]);
  ok("401 simultâneos fazem um refresh só", pedidos.filter((p) => p.rota === "/auth/refresh").length - antes === 1);

  const conf = sobe("https://example.test/?confirmar=abc123");
  await tick(800);
  ok("token sai do endereço", conf.w.location.search === "");
  ok("link do e-mail pede a senha do cadastro", conf.d.querySelector("h1").textContent === "Confirmar e-mail");
  conf.d.querySelector('input[name="senha"]').value = "senha-forte-1";
  conf.d.querySelector("form").dispatchEvent(new conf.w.Event("submit", { cancelable: true }));
  await tick(800);
  const c = conf.pedidos.find((p) => p.rota === "/auth/confirmar");
  ok("confirma com o token e a senha", c && c.corpo.token === "abc123" && c.corpo.senha === "senha-forte-1");
  ok("mostra a confirmação", conf.d.querySelector('[role="status"]').textContent.includes("confirmado"));

  console.log("\n== Resultado: " + pass + " passaram, " + fail + " falharam ==\n");
  process.exit(fail ? 1 : 0);
})();
