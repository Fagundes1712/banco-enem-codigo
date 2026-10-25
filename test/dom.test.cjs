"use strict";
/* Teste de comportamento em DOM real (jsdom). Não é artefato do site. */
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");

const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
// Os scripts do app, na ordem em que index.html os carrega.
const appJs = [...html.matchAll(/<script src="(js\/[^"]+)"/g)]
  .map((m) => fs.readFileSync(path.join(root, m[1]), "utf8"))
  .join("\n");
// BANCO permite apontar outro arquivo só para depuração local; o padrão é o banco real.
const banco = JSON.parse(
  fs.readFileSync(process.env.BANCO || path.join(root, "questions.json"), "utf8")
);
const tax = JSON.parse(fs.readFileSync(path.join(root, "taxonomy.json"), "utf8"));
const TOP = {};
const SUB = {};
for (const a of tax.areas)
  for (const s of a.subjects) {
    SUB[s.id] = { ...s, area: a.id };
    for (const t of s.topics) TOP[t.id] = { ...t, area: a.id, materia: s.id };
  }
const valida = (q) =>
  !!q.topico && !!TOP[q.topico] && TOP[q.topico].area === q.area &&
  (!q.materia || q.materia === TOP[q.topico].materia);
// Contagem de questões únicas calculada aqui, independente do app.
function unicas(list) {
  const s = new Set();
  return list.filter((q) => {
    const k = q.equivale || q.id;
    if (q.anulada || s.has(k)) return false;
    s.add(k);
    return true;
  });
}
const tick = (ms) => new Promise((r) => setTimeout(r, ms));
// Questão exibida: o DOM separa parágrafos e troca ![..](url) por <img>, então
// compara sem espaços e, quando há figura, pela própria imagem (as questões
// recortadas da prova têm o mesmo texto de abertura).
const semEsp = (s) => s.replace(/!\[[^\]]*\]\([^)]*\)/g, "").replace(/\s+/g, "");
function questaoNaTela(doc, lista) {
  const enun = doc.querySelector(".enun");
  const img = enun.querySelector("img");
  const src = img && img.getAttribute("src");
  const texto = semEsp(enun.textContent).slice(0, 60);
  return lista.find(
    (x) =>
      !x.anulada &&
      (src ? x.enunciado.includes("(" + src + ")") : semEsp(x.enunciado).startsWith(texto))
  );
}

let pass = 0;
let fail = 0;
function ok(name, cond, extra) {
  if (cond) {
    pass += 1;
    console.log("  ok   " + name);
  } else {
    fail += 1;
    console.log("  FAIL " + name + (extra ? "  -> " + extra : ""));
  }
}

function boot() {
  const dom = new JSDOM(html, {
    runScripts: "outside-only",
    url: "https://example.test/",
    pretendToBeVisual: true,
  });
  const { window } = dom;
  window.fetch = (u) =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(String(u).includes("taxonomy") ? tax : banco),
    });
  window.alert = () => {};
  window.scrollTo = () => {};

  // jsdom não implementa <dialog>.showModal(); no navegador é nativo.
  const dp = window.HTMLDialogElement && window.HTMLDialogElement.prototype;
  if (dp && !dp.showModal) {
    dp.showModal = function () {
      this.setAttribute("open", "");
      this.open = true;
    };
    dp.close = function () {
      this.removeAttribute("open");
      this.open = false;
      this.dispatchEvent(new window.Event("close"));
    };
  }

  // "use strict" no app.js mantém as declarações fora do escopo global.
  window.eval(appJs + "\n;window.__tri = tri;");
  return window;
}

const click = (w, el) =>
  el.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));

// Vai da barra lateral até um tópico, como o estudante faria.
async function irTopico(w, id) {
  const d = w.document;
  const t = TOP[id];
  click(w, d.getElementById("nav-inicio"));
  await tick(20);
  click(w, d.getElementById("tab-" + t.area));
  await tick(20);
  const mat = [...d.querySelectorAll(".item.sub")].find((b) => b.querySelector(".item-name").textContent === SUB[t.materia].nome);
  click(w, mat);
  await tick(20);
  const top = [...d.querySelectorAll(".item.top-item")].find((b) => b.querySelector(".item-name").textContent === t.nome);
  if (top) click(w, top);
  await tick(20);
}

(async () => {
  console.log("\n== Boot e Home ==");
  const w = boot();
  await new Promise((r) => setTimeout(r, 60));
  const d = w.document;

  ok("app renderizado", d.getElementById("app").children.length > 0);
  ok("h1 do hero presente", d.querySelector("h1").textContent.includes("ENEM"));
  ok("4 abas de área", d.querySelectorAll(".tab").length === 4);
  ok(
    "aba CN selecionada por padrão",
    d.querySelector('.tab[aria-selected="true"]').textContent === "Ciências da Natureza"
  );
  ok("sem filtro de ano na home", !d.querySelector("label.f select"));
  ok(
    "home não cita anos das provas",
    !/20\d\d/.test(d.getElementById("app").textContent),
    d.getElementById("app").textContent.slice(0, 160)
  );
  ok("2 modos: por conteúdo e aleatório", d.querySelectorAll(".chip.mode").length === 2);
  ok(
    "modo padrão é por conteúdo",
    d.querySelector('.chip.mode[aria-pressed="true"]').textContent === "Por conteúdo"
  );
  ok(
    "por conteúdo lista as 3 matérias de CN",
    [...d.querySelectorAll(".item.sub .item-name")].map((x) => x.textContent).join("|") ===
      "Biologia|Química|Física",
    [...d.querySelectorAll(".item.sub .item-name")].map((x) => x.textContent).join("|")
  );
  click(w, [...d.querySelectorAll(".chip.mode")].find((b) => /aleatório/.test(b.textContent)));
  await tick(20);
  ok("chips de quantidade no aleatório", d.querySelectorAll(".chip:not(.mode)").length === 4);

  const availNote = () => d.querySelector(".panel .note.avail");

  const cnCount = unicas(banco.filter((q) => q.area === "CN")).length;
  ok(
    "contagem reflete a área filtrada (CN = " + cnCount + ")",
    availNote().textContent.includes(String(cnCount)) &&
      !availNote().textContent.includes(String(banco.length)),
    availNote().textContent
  );
  ok(
    "lead mostra o total de " + unicas(banco).length + " questões únicas",
    d.querySelector(".lead").textContent.includes(unicas(banco).length.toLocaleString("pt-BR") + " questões"),
    d.querySelector(".lead").textContent
  );
  ok(
    "nota rodapé é disclaimer",
    d.querySelector("footer").textContent.includes("estimativa")
  );

  console.log("\n== Troca de área ==");
  click(w, d.querySelectorAll(".tab")[1]); // MT
  await new Promise((r) => setTimeout(r, 20));
  const nMT = unicas(banco.filter((q) => q.area === "MT")).length;
  const noteMT = availNote().textContent;
  ok(
    "MT tem " + nMT + " questões",
    noteMT.includes(String(nMT)) && !noteMT.includes(String(banco.length)),
    noteMT
  );
  ok(
    "h2 do painel mostra Matemática",
    d.querySelector(".panel h2").textContent === "Matemática"
  );

  console.log("\n== Semântica ARIA dos tabs ==");
  ok(
    "tablist rotulado",
    d.querySelector('.tabs[role="tablist"][aria-label]') !== null
  );
  ok(
    "cada tab tem aria-controls apontando para o painel",
    [...d.querySelectorAll(".tab")].every((t) =>
      d.getElementById(t.getAttribute("aria-controls"))
    )
  );
  const painel = d.querySelector(".panel");
  ok("painel é tabpanel", painel.getAttribute("role") === "tabpanel");
  ok(
    "painel rotulado pelo tab ativo",
    painel.getAttribute("aria-labelledby") ===
      d.querySelector('.tab[aria-selected="true"]').id
  );
  ok(
    "tab ativo é o único tabstop (roving tabindex)",
    [...d.querySelectorAll(".tab")].filter((t) => t.getAttribute("tabindex") === "0")
      .length === 1
  );
  ok(
    "todos os tabs declaram aria-selected explícito",
    [...d.querySelectorAll(".tab")].every((t) =>
      ["true", "false"].includes(t.getAttribute("aria-selected"))
    )
  );
  ok(
    "tabs são type=button (não submetem formulário)",
    [...d.querySelectorAll(".tab")].every((t) => t.getAttribute("type") === "button")
  );

  const focoAntes = d.querySelector('.tab[aria-selected="true"]').id;
  d
    .querySelector('.tab[aria-selected="true"]')
    .dispatchEvent(new w.KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
  await new Promise((r) => setTimeout(r, 20));
  const focoDepois = d.querySelector('.tab[aria-selected="true"]').id;
  ok(
    "ArrowRight na tablist troca de área",
    focoAntes !== focoDepois,
    focoAntes + " -> " + focoDepois
  );
  ok(
    "foco acompanha a aba selecionada",
    d.activeElement && d.activeElement.id === focoDepois,
    d.activeElement && d.activeElement.id
  );
  ok(
    "aba selecionada preservada após re-render",
    d.querySelector('.tab[tabindex="0"]').id === focoDepois
  );




  console.log("\n== Simulado completo ==");
  click(w, d.querySelectorAll(".chip:not(.mode)")[0]); // 5 questões
  await new Promise((r) => setTimeout(r, 20));
  click(w, d.querySelector(".btn.primary"));
  await new Promise((r) => setTimeout(r, 20));

  ok("barra do simulado", !!d.querySelector(".bar"));
  ok("timer visível", !!d.getElementById("tm"));
  ok("barra de progresso com aria", !!d.querySelector(".prog[aria-valuenow]"));
  ok("fieldset de alternativas", !!d.querySelector("fieldset.alts"));
  ok(
    "legend oculto para leitor de tela",
    !!d.querySelector("fieldset legend.skip")
  );
  ok("5 alternativas A–E", d.querySelectorAll(".alt").length === 5);
  ok(
    "bolhas A–E em ordem",
    [...d.querySelectorAll(".bub")]
      .map((b) => b.textContent)
      .join("") === "ABCDE"
  );
  ok("5 dots de navegação", d.querySelectorAll(".dot").length === 5);
  ok(
    "meta mostra a área",
    /Ciências da Natureza|Matemática|Ciências Humanas|Linguagens/.test(
      d.querySelector(".meta").textContent
    )
  );
  ok(
    "meta não repete o ano",
    !/20\d\d/.test(d.querySelector(".meta").textContent),
    d.querySelector(".meta").textContent
  );
  ok(
    "ano no canto da questão (badge .q-year)",
    /^ENEM \d{4}$/.test((d.querySelector(".q-year") || {}).textContent || ""),
    (d.querySelector(".q-year") || {}).textContent
  );
  ok(
    "badge é o último item da linha de topo, depois da área",
    !!d.querySelector(".q-top .meta") &&
      d.querySelector(".q-top").lastElementChild.classList.contains("q-year"),
    d.querySelector(".q-top") && d.querySelector(".q-top").innerHTML.slice(0, 120)
  );

  // Responder 3 corretamente, deixar 2 em branco.
  const radioPorLetra = (letra) =>
    [...d.querySelectorAll('.alt input[type="radio"]')].find((i) => i.value === letra);

  // Acha a questão atual pelo enunciado e responde o gabarito.
  function responderAtual() {
    const q = questaoNaTela(d, banco);
    const r = radioPorLetra(q.gab);
    r.checked = true;
    r.dispatchEvent(new w.Event("change", { bubbles: true }));
  }

  for (let i = 0; i < 3; i += 1) {
    responderAtual();
    await new Promise((r) => setTimeout(r, 10));
    const prox = [...d.querySelectorAll(".nav .btn")].find((b) =>
      /Próxima/.test(b.textContent)
    );
    click(w, prox);
    await new Promise((r) => setTimeout(r, 10));
  }

  // Ir para a última questão (a 5ª) para expor "Finalizar simulado".
  click(w, d.querySelectorAll(".dot")[4]);
  await new Promise((r) => setTimeout(r, 10));
  ok(
    "dot leva à última questão",
    /Questão 5 de 5/.test(d.querySelector(".bar-row span").textContent),
    d.querySelector(".bar-row span").textContent
  );

  ok(
    "progresso atualizado para 3",
    d.querySelector(".prog").getAttribute("aria-valuenow") === "3",
    d.querySelector(".prog").getAttribute("aria-valuenow")
  );
  ok(
    "dots marcados como respondidos",
    d.querySelectorAll(".dot.on").length === 3,
    d.querySelectorAll(".dot.on").length
  );

  console.log("\n== Confirmação nativa substituída por <dialog> ==");
  let confirmChamado = false;
  w.confirm = () => {
    confirmChamado = true;
    return true;
  };
  const fin = [...d.querySelectorAll(".nav .btn")].find((b) =>
    /Finalizar/.test(b.textContent)
  );
  click(w, fin);
  await new Promise((r) => setTimeout(r, 20));

  ok("window.confirm NÃO foi chamado", confirmChamado === false);
  ok("<dialog> aberto", !!d.querySelector("dialog.modal[open]"));
  ok(
    "diálogo avisa sobre em branco",
    d.querySelector("dialog.modal .note").textContent.includes("2"),
    d.querySelector("dialog.modal .note") && d.querySelector("dialog.modal .note").textContent
  );
  ok("2 ações no diálogo", d.querySelectorAll("dialog.modal .modal-actions .btn").length === 2);

  console.log("\n== Resultado ==");
  const voltar = [...d.querySelectorAll("dialog.modal .btn")].find((b) =>
    /Continuar prova/.test(b.textContent)
  );
  click(w, voltar);
  await new Promise((r) => setTimeout(r, 20));
  ok("cancelar fecha o diálogo", !d.querySelector("dialog.modal[open]"));

  click(w, fin);
  await new Promise((r) => setTimeout(r, 20));
  const finalizar = [...d.querySelectorAll("dialog.modal .btn")].find((b) =>
    /Finalizar mesmo assim/.test(b.textContent)
  );
  click(w, finalizar);
  await new Promise((r) => setTimeout(r, 30));

  ok("nota estimada exibida", !!d.querySelector(".score"));
  const nota = Number(d.querySelector(".score").textContent);
  ok("nota é número entre 0 e 1000", nota >= 0 && nota <= 1000, String(nota));
  ok("3 acertos reportados", d.querySelector(".stats b").textContent === "3 de 5",
    d.querySelector(".stats b").textContent);
  ok(
    "estatística de em branco presente",
    [...d.querySelectorAll(".stats b")].some((b) => b.textContent === "2")
  );
  ok(
    "disclaimer do TRI presente",
    d.querySelector(".note").textContent.includes("TRI")
  );
  ok(
    "resultado sem desempenho por ano",
    d.querySelectorAll(".row").length === 0 &&
      !d.getElementById("app").textContent.includes("Desempenho por ano")
  );

  console.log("\n== Correções ==");
  click(w, [...d.querySelectorAll(".btn")].find((b) => /Ver correções/.test(b.textContent)));
  await new Promise((r) => setTimeout(r, 20));

  ok("5 seções de correção", d.querySelectorAll(".cor").length === 5);
  ok("3 tags 'Acertou'", d.querySelectorAll(".tag.ok").length === 3,
    d.querySelectorAll(".tag.ok").length);
  ok("2 tags 'Em branco'", d.querySelectorAll(".tag.nil").length === 2,
    d.querySelectorAll(".tag.nil").length);
  ok("gabarito marcado", d.querySelectorAll(".alt.gab").length === 5);
  ok(
    "correção não mostra o ano da prova",
    [...d.querySelectorAll(".cor .meta")].every((m) => !/20\d\d/.test(m.textContent)),
    (d.querySelector(".cor .meta") || {}).textContent
  );
  ok(
    "nenhum erro marcado (em branco não é erro visual)",
    d.querySelectorAll(".alt.err").length === 0
  );
  ok(
    "rótulo 'gabarito' em cada alternativa certa",
    d.querySelectorAll(".gab-label").length === 5,
    d.querySelectorAll(".gab-label").length
  );

  const temResolucao = banco.some((q) => q.resolucao);
  ok(
    temResolucao ? "resolução renderizada" : "fallback de resolução",
    temResolucao
      ? d.querySelectorAll(".cor .enun").length > 0
      : d.body.textContent.includes("Resolução ainda não cadastrada")
  );

  console.log("\n== Voltar ao resultado e novo simulado ==");
  ok(
    "sem '[object HTMLElement]' na tela de correções",
    !d.getElementById("app").textContent.includes("[object"),
    d.getElementById("app").textContent.slice(0, 200)
  );
  click(w, [...d.querySelectorAll(".btn")].find((b) => /Voltar ao resultado/.test(b.textContent)));
  await new Promise((r) => setTimeout(r, 20));
  ok("volta para o resultado", !!d.querySelector(".score"));

  click(w, [...d.querySelectorAll(".btn")].find((b) => /Novo simulado/.test(b.textContent)));
  await new Promise((r) => setTimeout(r, 20));
  ok("volta para a home", !!d.querySelector("h1") && !!d.querySelector(".tabs"));

  console.log("\n== Navegação por teclado ==");
  click(w, d.querySelector(".btn.primary"));
  await new Promise((r) => setTimeout(r, 20));
  const antes = d.querySelector(".bar-row span").textContent;
  d.dispatchEvent(new w.KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
  await new Promise((r) => setTimeout(r, 20));
  ok(
    "ArrowRight avança questão",
    d.querySelector(".bar-row span").textContent !== antes,
    antes + " -> " + d.querySelector(".bar-row span").textContent
  );
  d.dispatchEvent(new w.KeyboardEvent("keydown", { key: "ArrowLeft", bubbles: true }));
  await new Promise((r) => setTimeout(r, 20));
  ok(
    "ArrowLeft volta questão",
    d.querySelector(".bar-row span").textContent === antes
  );

  console.log("\n== TRI: monotonia ==");
  const triMod = w.__tri;
  const mk = (nAcertos) => {
    const qs = banco.slice(0, 10);
    return triMod(qs.map((q, i) => [q, i < nAcertos]));
  };
  const notas = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(mk);
  ok(
    "nota cresce com os acertos",
    notas.every((v, i) => i === 0 || v >= notas[i - 1]),
    notas.join(",")
  );
  ok("0 acertos < 500", notas[0] < 500, String(notas[0]));
  ok("10 acertos > 500", notas[10] > 500, String(notas[10]));

  console.log("\n== Banco de dados ==");
  ok(
    "banco não vazio, ids únicos",
    banco.length > 0 && new Set(banco.map((q) => q.id)).size === banco.length,
    String(banco.length)
  );
  ok(
    "nenhuma questão com comp/hab (código morto removido)",
    banco.every((q) => q.comp === undefined && q.hab === undefined)
  );
  ok(
    "todo gabarito existe em alts (fora as anuladas)",
    banco.every(
      (q) => q.anulada || (q.alts && Object.prototype.hasOwnProperty.call(q.alts, q.gab))
    )
  );
  ok(
    "imagens, quando existem, são caminhos não vazios",
    banco.every(
      (q) =>
        !q.imagens ||
        q.imagens.every((u) => typeof u === "string" && u.trim().length > 0)
    )
  );
  // Integridade do banco extraído das provas oficiais (só faz sentido no banco real).
  if (!process.env.BANCO) {
    const porProva = {};
    for (const q of banco) {
      const k = q.ano + "-" + q.area;
      porProva[k] = (porProva[k] || 0) + 1;
    }
    const anos = [...new Set(banco.map((q) => q.ano))].sort();
    ok(
      "anos 2015–2019 e 2021–2025, sem 2020",
      anos.join() === "2015,2016,2017,2018,2019,2021,2022,2023,2024,2025",
      anos.join()
    );
    ok(
      "cada prova tem 45 questões (LC: 40 + 5 inglês + 5 espanhol)",
      Object.entries(porProva).every(([k, n]) => n === (k.endsWith("LC") ? 50 : 45)),
      JSON.stringify(porProva)
    );
    ok(
      "número da questão bate com o id e com a faixa do dia",
      banco.every((q) => q.id.startsWith(q.ano + "-" + q.area + "-") && q.numero >= 1 && q.numero <= 180)
    );
    ok(
      "toda questão tem 5 alternativas A–E não vazias",
      banco.every((q) => Object.keys(q.alts).join("") === "ABCDE" && Object.values(q.alts).every((t) => t.trim()))
    );
    ok(
      "gabarito A–E, ou anulada sem gabarito",
      banco.every((q) => (q.anulada ? q.gab === null : /^[A-E]$/.test(q.gab)))
    );
    ok(
      "aplicação regular, caderno azul e fonte oficial em todas",
      banco.every((q) => q.aplicacao === "regular" && q.caderno === "Azul" && /INEP/.test(q.fonte))
    );
    const refs = new Set();
    for (const q of banco)
      for (const t of [q.enunciado, ...Object.values(q.alts), ...(q.imagens || []).map((u) => "(" + u + ")")])
        for (const m of t.matchAll(/\((img\/[^)\s]+)\)|^img:(\S+)/g)) refs.add(m[1] || m[2]);
    const faltam = [...refs].filter((u) => !fs.existsSync(path.join(root, u)));
    ok("toda figura referenciada existe em img/", faltam.length === 0, faltam.slice(0, 5).join(" "));
    const recortes = banco.filter((q) => q.recorte);
    ok(
      "questão recortada da prova traz a imagem do original",
      recortes.every((q) => /!\[[^\]]*\]\(img\/[^)]+\)/.test(q.enunciado)),
      String(recortes.length)
    );
    ok(
      "nenhuma resolução inventada (campo vazio até haver fonte)",
      banco.every((q) => q.resolucao === null || q.resolucao === undefined)
    );
  }

  console.log("\n== PWA / offline ==");
  ok(
    "index.html linka manifest e ícone SVG",
    /rel="manifest" href="manifest\.json"/.test(html) &&
      /href="icon\.svg" type="image\/svg\+\xml"/.test(html)
  );
  ok(
    "app.js registra sw.js protegido por protocolo/host",
    /serviceWorker" in navigator/.test(appJs) &&
      /location\.protocol === "https:"/.test(appJs) &&
      /navigator\.serviceWorker\.register\("sw\.js"\)/.test(appJs)
  );
  const manifest = JSON.parse(
    fs.readFileSync(path.join(root, "manifest.json"), "utf8")
  );
  ok("manifest: name, start_url, display standalone",
    !!manifest.name && manifest.start_url === "." && manifest.display === "standalone");
  ok("manifest: ícone existe e é o icon.svg",
    manifest.icons.some((i) => i.src === "icon.svg" && i.type === "image/svg+xml") &&
      fs.existsSync(path.join(root, "icon.svg")));
  const sw = fs.readFileSync(path.join(root, "sw.js"), "utf8");
  ok("sw.js: cache versionado + skipWaiting/claim",
    /const VERSION = "v\d+"/.test(sw) && /skipWaiting\(\)/.test(sw) && /clients\.claim\(\)/.test(sw));
  ok("sw.js: questions.json em stale-while-revalidate",
    /questions\.json/.test(sw) && /staleWhileRevalidate/.test(sw));
  ok("sw.js: não cacheia status >= 500 nem não-GET",
    /res\.status < 500/.test(sw) && /req\.method !== "GET"/.test(sw));

  console.log("\n== Taxonomia: exatamente 3 níveis ==");
  ok("4 áreas", tax.areas.map((a) => a.id).sort().join() === "CH,CN,LC,MT");
  ok(
    "níveis declarados: área, matéria, tópico",
    JSON.stringify(tax.niveis) === '["area","materia","topico"]'
  );
  const tops = Object.values(TOP);
  ok(
    "nenhum tópico tem filhos (sem 4º nível)",
    tops.every((t) => Object.keys(t).every((k) => ["id", "nome", "desc", "antes", "area", "materia"].includes(k)))
  );
  ok(
    "antes lista só ids antigos (texto), nunca filhos",
    tops.every((t) => !t.antes || (t.antes.length && t.antes.every((v) => typeof v === "string" && v.startsWith(t.materia + "."))))
  );
  ok(
    "toda matéria tem tópicos e nada além de id/nome/topics",
    tax.areas.every((a) =>
      a.subjects.length > 0 &&
      a.subjects.every((s) => s.topics.length > 0 &&
        Object.keys(s).every((k) => ["id", "nome", "topics"].includes(k)))
    )
  );
  ok("ids de tópico únicos", new Set(tops.map((t) => t.id)).size === tops.length);
  ok(
    "id de cada tópico nasce do id da sua matéria e área",
    tops.every((t) => t.id.startsWith(t.materia + ".") && t.materia.startsWith(t.area + "."))
  );
  ok("todo tópico tem descrição", tops.every((t) => t.desc && t.desc.length > 10));
  const nomes = (sid) => SUB[sid].topics.map((t) => t.nome);
  // Tema vazio sai; tema pequeno é reunido a outro para o filtro ter peso.
  const nTop = {};
  for (const q of unicas(banco)) nTop[q.topico] = (nTop[q.topico] || 0) + 1;
  ok("nenhum tópico vazio", tops.every((t) => nTop[t.id] > 0), tops.filter((t) => !nTop[t.id]).map((t) => t.nome).join(", "));
  ok(
    "nenhum tópico com menos de 4 questões",
    tops.every((t) => nTop[t.id] >= 4),
    tops.filter((t) => nTop[t.id] < 4).map((t) => t.nome + "=" + nTop[t.id]).join(", ")
  );
  ok(
    "Inglês e Espanhol têm um tópico só (sem escolha de tema)",
    SUB["LC.en"].topics.length === 1 && SUB["LC.es"].topics.length === 1
  );
  ok("ids antigos não se repetem entre tópicos", (() => {
    const v = tops.flatMap((t) => t.antes || []);
    return new Set(v).size === v.length;
  })());
  ok(
    "matérias obrigatórias por área",
    ["CN:Biologia,Química,Física", "MT:Matemática e suas Tecnologias",
      "CH:História,Geografia,Filosofia,Sociologia",
      "LC:Língua Portuguesa,Literatura,Língua Inglesa,Língua Espanhola,Artes,Educação Física,Tecnologias da Informação e Comunicação"]
      .every((x) => {
        const [a, l] = x.split(":");
        return tax.areas.find((y) => y.id === a).subjects.map((s) => s.nome).join() === l;
      })
  );
  ok(
    "História tem História Geral, do Brasil e da América",
    ["História Geral — ", "História do Brasil — ", "História da América"].every((p) =>
      nomes("CH.his").some((n) => n.startsWith(p))
    )
  );
  ok(
    "Filosofia cobre períodos, ética, política e conhecimento",
    ["Filosofia Antiga", "Filosofia Moderna", "Ética e Moral", "Filosofia Política", "Conhecimento, Ciência e Estética"]
      .every((n) => nomes("CH.fil").includes(n))
  );
  ok(
    "nenhum nome de tópico repetido dentro da mesma matéria",
    Object.keys(SUB).every((s) => new Set(nomes(s)).size === nomes(s).length)
  );

  console.log("\n== Classificação do banco ==");
  const classif = banco.filter((q) => q.topico);
  ok(
    "toda classificação aponta para tópico existente da mesma área e matéria",
    classif.every(valida),
    classif.filter((q) => !valida(q)).map((q) => q.id).slice(0, 5).join(", ")
  );
  ok(
    "tags auxiliares, quando existem, são tópicos válidos",
    banco.every((q) => !q.tags || q.tags.every((t) => TOP[t]))
  );
  ok(
    "equivalências apontam para questão existente",
    banco.every((q) => !q.equivale || banco.some((x) => x.id === q.equivale))
  );
  console.log("     classificadas: " + classif.length + " de " + banco.length);

  console.log("\n== Navegação área → matéria → tópico → questões ==");
  const w2 = boot();
  await tick(60);
  const d2 = w2.document;
  // Escolhe o tópico com mais questões para exercitar filtros.
  const qPorTop = {};
  for (const q of unicas(banco.filter(valida))) qPorTop[q.topico] = (qPorTop[q.topico] || 0) + 1;
  const alvo = Object.keys(qPorTop).sort((a, b) => qPorTop[b] - qPorTop[a])[0];
  ok("há ao menos um tópico com questões", !!alvo);
  const tA = TOP[alvo];
  click(w2, d2.getElementById("tab-" + tA.area));
  await tick(20);
  ok(
    "nível 1 → nível 2: área mostra suas matérias",
    d2.querySelectorAll(".item.sub").length === tax.areas.find((a) => a.id === tA.area).subjects.length
  );
  const subBtn = [...d2.querySelectorAll(".item.sub")].find(
    (b) => b.querySelector(".item-name").textContent === SUB[tA.materia].nome
  );
  click(w2, subBtn);
  await tick(20);
  ok("matéria abre a tela da matéria", d2.querySelector("h1").textContent === SUB[tA.materia].nome);
  ok(
    "nível 2 → nível 3: matéria lista todos os seus tópicos",
    d2.querySelectorAll(".item.top-item").length === SUB[tA.materia].topics.length
  );
  ok("tela da matéria não mostra questões", d2.querySelectorAll(".qcard").length === 0);
  const topBtn = [...d2.querySelectorAll(".item.top-item")].find(
    (b) => b.querySelector(".item-name").textContent === tA.nome
  );
  click(w2, topBtn);
  await tick(20);
  const uniTop = unicas(banco.filter((q) => valida(q) && q.topico === alvo));
  ok("tópico abre direto nas questões", d2.querySelectorAll(".qcard").length === uniTop.length,
    d2.querySelectorAll(".qcard").length + " vs " + uniTop.length);
  ok("tópico não oferece nível abaixo", d2.querySelectorAll(".item").length === 0);
  ok("contagem de únicas no tópico", d2.getElementById("n-uni").textContent === String(uniTop.length));
  ok("descrição do tópico", d2.querySelector(".lead").textContent === tA.desc);
  const anosT = [...new Set(uniTop.map((q) => q.ano))].sort();
  ok("distribuição por ano tem uma linha por ano", d2.querySelectorAll(".dist .row").length === anosT.length);
  ok(
    "distribuição por ano soma as únicas",
    [...d2.querySelectorAll(".dist .row b")].reduce((s, b) => s + Number(b.textContent), 0) === uniTop.length
  );

  console.log("\n== Filtros do tópico ==");
  const setF = async (k, v) => {
    const s = d2.querySelector('select[data-f="' + k + '"]');
    s.value = v;
    s.dispatchEvent(new w2.Event("change", { bubbles: true }));
    await tick(20);
  };
  const ano0 = String(anosT[0]);
  await setF("ano", ano0);
  ok(
    "filtro de ano",
    d2.querySelectorAll(".qcard").length === uniTop.filter((q) => String(q.ano) === ano0).length &&
      [...d2.querySelectorAll(".qcard .meta")].every((m) => m.textContent.startsWith("ENEM " + ano0))
  );
  ok("filtro preservado após re-render", d2.querySelector('select[data-f="ano"]').value === ano0);
  await setF("ano", "");
  ok("tópico sem filtro de aplicação", !d2.querySelector('select[data-f="apl"]'));
  ok("tópico sem filtro de situação", !d2.querySelector('select[data-f="sit"]'));
  const escala = (n) => [5, 10, 25, 45].filter((x) => x <= n).join();
  const chipsQtd = () => [...d2.querySelectorAll(".qtd .chip")].map((c) => c.textContent).join();
  ok("quantidade na escala até o total do tópico", chipsQtd() === escala(uniTop.length), chipsQtd());
  await setF("ano", ano0);
  const nAno = uniTop.filter((q) => String(q.ano) === ano0).length;
  ok("quantidade acompanha o filtro de ano", chipsQtd() === escala(nAno), nAno + ": " + chipsQtd());
  await setF("ano", "");
  click(w2, [...d2.querySelectorAll(".qtd .chip")].find((c) => c.textContent === "10"));
  await tick(20);
  ok("chip de 10 marcado", d2.querySelector('.qtd .chip[aria-pressed="true"]').textContent === "10");
  click(w2, d2.querySelector(".qtd .btn.primary"));
  await tick(20);
  ok("fazer 10 questões abre simulado de 10", /de 10$/.test(d2.querySelector(".bar-row span").textContent));
  click(w2, d2.querySelector(".btn.sair"));
  await tick(10);
  const dSair = d2.querySelector("dialog.modal[open]");
  ok("sair pede confirmação", !!dSair && /Sair do simulado/.test(dSair.textContent));
  click(w2, [...dSair.querySelectorAll(".btn")].find((b) => b.textContent === "Sair"));
  await tick(20);
  ok("sair volta ao tópico sem salvar bloco", d2.querySelector("h1").textContent === tA.nome && !w2.localStorage.getItem("banco-enem:blocos"));
  {
    // Tópico com menos de 5 questões só deixa escolher pela lista.
    const peq = Object.keys(TOP).find((k) => unicas(banco.filter((q) => q.topico === k)).length < 5);
    await irTopico(w2, peq);
    ok("tópico pequeno não oferece quantidade", !d2.querySelector(".qtd") && d2.querySelectorAll(".qcard").length > 0);
    await irTopico(w2, "LC.en." + "leitura-em-ingles");
    ok("Língua Inglesa abre direto nas questões", d2.querySelector("h1").textContent === "Leitura em Inglês" &&
      d2.querySelector(".btn.back").textContent.includes("Linguagens"));
    await irTopico(w2, alvo);
  }

  console.log("\n== Progresso do estudante no tópico ==");
  click(w2, d2.querySelectorAll(".qcard")[0]);
  await tick(20);
  ok("questão do tópico abre o simulado", !!d2.querySelector(".bar"));
  ok(
    "simulado do tópico tem as questões do tópico",
    /de \d+/.test(d2.querySelector(".bar-row span").textContent) &&
      d2.querySelector(".bar-row span").textContent.endsWith("de " + uniTop.length)
  );
  const q0 = questaoNaTela(d2, uniTop);
  const r0 = [...d2.querySelectorAll('.alt input[type="radio"]')].find((i) => i.value === q0.gab);
  r0.checked = true;
  r0.dispatchEvent(new w2.Event("change", { bubbles: true }));
  await tick(10);
  click(w2, d2.querySelectorAll(".dot")[d2.querySelectorAll(".dot").length - 1]);
  await tick(10);
  click(w2, [...d2.querySelectorAll(".nav .btn")].find((b) => /Finalizar/.test(b.textContent)));
  await tick(20);
  const fim = d2.querySelector("dialog.modal[open]");
  if (fim) {
    click(w2, [...fim.querySelectorAll(".btn")].find((b) => /Finalizar mesmo assim/.test(b.textContent)));
    await tick(30);
  }
  const volta = [...d2.querySelectorAll(".btn")].find((b) => /Voltar ao tópico/.test(b.textContent));
  ok("resultado oferece voltar ao tópico", !!volta);
  click(w2, volta);
  await tick(20);
  const st = [...d2.querySelectorAll(".stats b")].map((b) => b.textContent);
  ok("tópico conta 1 respondida e 1 acertada", st[1] === "1" && st[3] === "1" && st[4] === "0", st.join(","));
  ok("histórico salvo no navegador", Object.keys(JSON.parse(w2.localStorage.getItem("banco-enem:hist"))).length === 1);
  ok("teclado não navega fora do simulado", (() => {
    d2.dispatchEvent(new w2.KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
    return !d2.querySelector(".bar");
  })());
  click(w2, d2.querySelector(".btn.back"));
  await tick(20);
  ok("voltar do tópico leva à matéria", d2.querySelector("h1").textContent === SUB[tA.materia].nome);
  click(w2, d2.querySelector(".btn.back"));
  await tick(20);
  ok("voltar da matéria leva à área", !!d2.querySelector(".tabs"));

  console.log("\n== Suas respostas ==");
  ok("barra lateral com Início e Suas respostas", !!d2.getElementById("nav-inicio") && !!d2.getElementById("nav-resp"));
  click(w2, d2.getElementById("nav-resp"));
  await tick(20);
  ok("aba Suas respostas marcada", d2.getElementById("nav-resp").getAttribute("aria-current") === "page");
  const blocos = d2.querySelectorAll(".bloco");
  ok("simulado do tópico virou 1 bloco", blocos.length === 1, String(blocos.length));
  ok("bloco na cor da área", blocos[0] && blocos[0].getAttribute("data-area") === tA.area);
  ok(
    "título do bloco traz matéria e tema",
    blocos[0] &&
      blocos[0].querySelector(".bloco-mat").textContent === SUB[tA.materia].nome &&
      blocos[0].querySelector(".bloco-tema").textContent === uniTop.length + " questões de " + tA.nome
  );
  ok("bloco mostra acertos", blocos[0] && blocos[0].querySelector(".bloco-placar").textContent === "1/" + uniTop.length);
  ok("bloco salvo no navegador", JSON.parse(w2.localStorage.getItem("banco-enem:blocos")).length === 1);
  const setRF = async (k, v) => {
    const s = d2.querySelector('select[data-rf="' + k + '"]');
    s.value = v;
    s.dispatchEvent(new w2.Event("change", { bubbles: true }));
    await tick(20);
  };
  const outra = Object.keys({ CN: 1, MT: 1, CH: 1, LC: 1 }).find((a) => a !== tA.area);
  await setRF("area", outra);
  ok("filtro de área esconde blocos de outra área", d2.querySelectorAll(".bloco").length === 0);
  await setRF("area", tA.area);
  ok("filtro de matéria lista só as matérias da área", [...d2.querySelectorAll('select[data-rf="sub"] option')].length === tax.areas.find((a) => a.id === tA.area).subjects.length + 1);
  await setRF("sub", tA.materia);
  ok("filtro de matéria mantém o bloco", d2.querySelectorAll(".bloco").length === 1);
  ok(
    "situação em Suas respostas sem 'não respondidas'",
    [...d2.querySelectorAll('select[data-rf="sit"] option')].map((o) => o.textContent).join() === "Todas,Respondidas,Acertadas,Erradas"
  );
  await setRF("sit", "ok");
  ok("situação acertadas lista a questão acertada", d2.querySelectorAll(".qcard").length === 1 && !d2.querySelector(".bloco"));
  await setRF("sit", "bad");
  ok("situação erradas vazia", d2.querySelectorAll(".qcard").length === 0);
  await setRF("sit", "todas");
  ok("situação todas volta aos blocos", d2.querySelectorAll(".bloco").length === 1);
  click(w2, d2.querySelector(".bloco"));
  await tick(20);
  ok("bloco abre as correções", d2.querySelectorAll(".cor").length === uniTop.length);
  click(w2, [...d2.querySelectorAll(".btn")].find((b) => /Voltar ao resultado/.test(b.textContent)));
  await tick(20);
  const vr = [...d2.querySelectorAll(".btn")].find((b) => /Suas respostas/.test(b.textContent));
  ok("resultado do bloco volta para Suas respostas", !!vr);
  click(w2, vr);
  await tick(20);
  ok("voltou para Suas respostas", d2.querySelector("h1").textContent === "Suas respostas");
  click(w2, d2.getElementById("nav-inicio"));
  await tick(20);
  ok("Início volta para a área", !!d2.querySelector(".tabs"));

  console.log("\n== Questões únicas ==");
  ok(
    "contagem da área ignora anuladas e equivalentes",
    (() => {
      click(w2, [...d2.querySelectorAll(".chip.mode")].find((b) => /aleatório/.test(b.textContent)));
      const n = unicas(banco.filter((q) => q.area === tA.area)).length;
      return d2.querySelector(".panel .note.avail").textContent.startsWith(n + " ");
    })()
  );

  console.log(
    "\n== Resultado: " + pass + " passaram, " + fail + " falharam ==\n"
  );
  process.exit(fail ? 1 : 0);
})();
