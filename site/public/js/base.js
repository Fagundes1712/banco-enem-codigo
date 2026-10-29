"use strict";

/* ============================== Domínio ============================== */

const AREAS = {
  CN: ["Ciências da Natureza", "Física, Química, Biologia"],
  MT: ["Matemática", "e suas Tecnologias"],
  CH: ["Ciências Humanas", "História, Geografia, Filosofia, Sociologia"],
  LC: ["Linguagens", "Português, Literatura, Línguas, Artes"],
};

// Situação só existe em Suas respostas, onde tudo já foi respondido.
const SIT = { todas: "Todas", resp: "Respondidas", ok: "Acertadas", bad: "Erradas" };
const QTDS = [5, 10, 25, 45];
// Faixas do parâmetro b oficial do INEP (tools/microdados.py), do 1 ao 5.
const NIVEIS = ["Leve", "Moderado", "Intenso", "Radical", "Extremo"];
const HKEY = "banco-enem:hist";

const $ = document.getElementById("app");
let Q = [];
let TX = null; // taxonomia: áreas → matérias → tópicos (taxonomy.json)
let IX = { sub: {}, top: {} }; // índices por id
let S = { area: "CN", n: 10, modo: "conteudo", materia: null, topico: null, f: {} };
let T = null;
let tick = null;
let H = readHist();
let PRO = false; // assinatura ativa na conta; só ela mostra as notas

/* ============================== Helpers ============================== */

function h(t, a, ...k) {
  const e = document.createElement(t);
  for (const [x, v] of Object.entries(a || {})) {
    if (x.startsWith("on")) e.addEventListener(x.slice(2), v);
    else if (x === "class") e.className = v;
    else if (x === "style") e.style.cssText = v; // CSSOM: a CSP barra o atributo style, não isto
    else if (x.startsWith("aria-") && typeof v === "boolean") e.setAttribute(x, String(v));
    else if (v !== false && v != null) e.setAttribute(x, v === true ? "" : v);
  }
  for (const c of k.flat()) if (c != null) e.append(c);
  return e;
}

function mount(...n) {
  // replaceChildren escreveria "null" na tela para filhos vazios.
  $.replaceChildren(...n.flat().filter((x) => x != null));
  // Durante a prova a barra lateral some, para não sair sem querer.
  document.documentElement.toggleAttribute("data-exam", !!(T && T.live));
  $.classList.remove("in");
  void $.offsetWidth;
  $.classList.add("in");
  $.focus({ preventScroll: true });
  scrollTo(0, 0);
}

// Redesenha a mesma tela sem pular para o topo (troca de área, filtros).
function keep(fn) {
  const y = scrollY;
  fn();
  scrollTo(0, y);
}

// Transição entre áreas e abas: a tela se desfaz em quadrados pretos que
// acendem em ordem aleatória, a tela nova é desenhada por baixo e os
// quadrados se apagam, também ao acaso. Só opacity, sem deslocamento, então
// roda também com movimento reduzido (o Windows com "Mostrar animações"
// desligado avisa reduce e o efeito sumia no computador, a pedido do usuário
// ele vale em todo aparelho). Sem animate() (testes), troca direto.
let veu = null;
let veuFila = null;
const PIX = { dur: 140, ida: 260, volta: 300 };
function veuGrade() {
  const lado = Math.max(44, Math.ceil(innerWidth / 18));
  const cols = Math.ceil(innerWidth / lado);
  const n = cols * Math.ceil(innerHeight / lado);
  if (veu && veu.dataset.n === String(n)) return veu;
  veu?.remove();
  veu = h("div", { class: "veu", "aria-hidden": "true", "data-n": n, style: "--lado:" + lado + "px;--cols:" + cols });
  for (let i = 0; i < n; i++) veu.append(h("i"));
  return document.body.appendChild(veu);
}
function swap(fn) {
  if (!document.body.animate) return fn();
  if (veuFila) return void (veuFila = fn);
  veuFila = fn;
  const v = veuGrade();
  const pix = [...v.children];
  const anima = (de, ate, max) => {
    for (const p of pix)
      p.animate([{ opacity: de }, { opacity: ate }], {
        duration: PIX.dur,
        delay: Math.random() * max,
        easing: "cubic-bezier(0.23, 1, 0.32, 1)",
        fill: "both",
      });
  };
  anima(0, 1, PIX.ida);
  // Relógio, não o fim da animação: com a aba parada a troca acontece igual.
  setTimeout(() => {
    const f = veuFila;
    veuFila = null;
    f();
    anima(1, 0, PIX.volta);
  }, PIX.ida + PIX.dur + 40);
}

function shuffle(a) {
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// Enunciado: linha em branco separa parágrafos; quebra simples é mantida
// (poemas, listas). Figuras entram por ![alt](url).
function rich(t) {
  const w = h("div", { class: "enun" });
  String(t || "")
    .split(/!\[[^\]]*\]\(([^)]+)\)/)
    .forEach((x, i) => {
      if (i % 2)
        w.append(
          foto("q", x, "Imagem do enunciado")
        );
      else
        x.split(/\n{2,}/).forEach((p) => {
          if (p.trim()) w.append(h("p", null, p.trim()));
        });
    });
  return w;
}

// Figura preguiçosa: placeholder (skeleton) até carregar, depois entra com
// fade (styles.css, img.q). Erro também tira o placeholder e mostra o alt.
const foto = (cls, src, alt) =>
  h("img", {
    class: cls,
    src,
    alt,
    loading: "lazy",
    decoding: "async",
    onload: (e) => e.target.setAttribute("data-ok", ""),
    onerror: (e) => e.target.setAttribute("data-ok", ""),
  });

const imgs = (q) => (q.imagens || []).map((u) => foto("q", u, "Imagem da questão"));

const altImg = (src) => foto("q alt-img", src, "Alternativa em imagem");

// Alternativa: texto, "img:<url>" ou texto com ![alt](url) no meio.
const altc = (t) =>
  t.startsWith("img:")
    ? altImg(t.slice(4))
    : /!\[[^\]]*\]\(/.test(t)
      ? h(
          "span",
          { class: "alt-mix" },
          t.split(/!\[[^\]]*\]\(([^)]+)\)/).map((x, i) => (i % 2 ? altImg(x) : x.trim() || null))
        )
      : t;

const fmt = (s) =>
  String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");


/* ============================== Carga ================================ */

const getJSON = (u) =>
  fetch(u, { cache: "no-cache" }).then((r) => {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  });

// Plano do usuário (contaAtual vem de js/conta.js, com o login). Sem login,
// sem rede ou sem API, fica no grátis.
const plano = () =>
  Promise.resolve(typeof contaAtual === "function" ? contaAtual() : null)
    .then((c) => {
      PRO = !!c?.assinatura_ativa;
    })
    .catch(() => {});

function load() {
  const tx = getJSON("taxonomy.json").catch(() => null);
  const pl = plano();
  getJSON("questions.json")
    .then((d) => {
      if (!Array.isArray(d) || !d.length) throw new Error("banco vazio");
      return Promise.all([tx, pl]).then(([t]) => boot(d, t));
    })
    .catch(() => tx.then((t) => pickFile(t)));
}

/* Liga banco e taxonomia. Cada questão aponta para área, matéria e tópico;
   se os três não baterem com a taxonomia, a questão fica fora das telas de
   conteúdo (continua no simulado aleatório da área) e conta como revisão. */
function boot(d, t) {
  Q = d;
  TX = t && Array.isArray(t.areas) ? t : null;
  IX = { sub: {}, top: {} };
  for (const a of TX ? TX.areas : [])
    for (const s of a.subjects) {
      IX.sub[s.id] = { ...s, area: a.id };
      for (const x of s.topics) IX.top[x.id] = { ...x, area: a.id, materia: s.id };
      // Ids de tópicos que foram reunidos: blocos antigos ainda acham o tópico.
      for (const x of s.topics) for (const v of x.antes || []) IX.top[v] ||= IX.top[x.id];
    }
  for (const q of Q) q._ok = !!q.topico && consistent(q);
  home();
}

function consistent(q) {
  const t = IX.top[q.topico];
  return !!t && t.area === q.area && (!q.materia || q.materia === t.materia);
}

function pickFile(t) {
  mount(
    h("div", { class: "top" }, h("span", { class: "brand" }, "Banco ENEM")),
    h("h1", null, "Banco ENEM"),
    h(
      "p",
      { class: "lead" },
      "Não consegui carregar questions.json ao lado desta página. Sirva o site por um servidor (por exemplo o GitHub Pages) ou escolha o arquivo manualmente."
    ),
    h(
      "label",
      { class: "f" },
      "Arquivo de questões",
      h("input", {
        type: "file",
        accept: ".json,application/json",
        onchange: (e) => {
          const f = e.target.files[0];
          if (!f) return;
          f.text()
            .then((x) => {
              const d = JSON.parse(x);
              if (!Array.isArray(d) || !d.length) throw new Error("vazio");
              boot(d, t);
            })
            .catch(() => alert("Não consegui ler esse arquivo."));
        },
      })
    )
  );
}

/* ====================== Histórico do estudante ====================== */

// Fica só neste navegador. Sem localStorage o app funciona igual, sem progresso.
function readHist() {
  try {
    return JSON.parse(localStorage.getItem(HKEY)) || {};
  } catch {
    return {};
  }
}

function saveHist() {
  try {
    localStorage.setItem(HKEY, JSON.stringify(H));
  } catch {
    /* armazenamento indisponível: progresso só nesta sessão */
  }
}

/* ========================= Questões únicas ========================== */

// Questões equivalentes em outro caderno apontam para a original em
// `equivale`; anuladas não entram em simulado nem em contagem de únicas.
const canon = (q) => q.equivale || q.id;
const usable = (q) => !q.anulada;

function uniq(list) {
  const seen = new Set();
  return list.filter((q) => {
    if (!usable(q) || seen.has(canon(q))) return false;
    seen.add(canon(q));
    return true;
  });
}

const inArea = (a) => uniq(Q.filter((q) => q.area === a));
const inSub = (s) => uniq(Q.filter((q) => q._ok && IX.top[q.topico].materia === s));
const inTop = (t) => uniq(Q.filter((q) => q._ok && q.topico === t));
const subsOf = (a) => (TX ? (TX.areas.find((x) => x.id === a) || {}).subjects || [] : []);

function sit(q) {
  const r = H[canon(q)];
  return r ? (r.ok ? "ok" : "bad") : "nao";
}

// Nota de um tópico, matéria ou área: o mesmo cálculo do simulado, feito
// direto com as questões respondidas do conjunto (última resposta de cada).
function notaDe(qs) {
  const r = qs.filter((q) => H[canon(q)]);
  return r.length ? nota(r.map((q) => [q, H[canon(q)].ok])) : null;
}

// Selo de nota dos cartões; sem resposta mostra traço.
const notaTag = (n) =>
  h(
    "span",
    travada({ class: "nota-tag", "aria-label": n == null ? "Sem nota ainda" : "Nota " + n }),
    h("small", { "aria-hidden": "true" }, "nota"),
    h("b", { "aria-hidden": "true" }, valorNota(n))
  );

const num = (n) => n.toLocaleString("pt-BR");

// Selo do nível de dificuldade; sem parâmetro oficial, nada aparece.
const nivel = (q) =>
  q.nivel
    ? h(
        "span",
        { class: "q-nivel", "data-nivel": q.nivel, "aria-label": "Dificuldade: " + NIVEIS[q.nivel - 1] },
        h("i", { "aria-hidden": "true" }, NIVEIS.map(() => h("b"))),
        NIVEIS[q.nivel - 1]
      )
    : null;
const plural = (n, um, varios) => num(n) + " " + (n === 1 ? um : varios);

