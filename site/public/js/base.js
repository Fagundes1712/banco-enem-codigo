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

/* ============================== Helpers ============================== */

function h(t, a, ...k) {
  const e = document.createElement(t);
  for (const [x, v] of Object.entries(a || {})) {
    if (x.startsWith("on")) e.addEventListener(x.slice(2), v);
    else if (x === "class") e.className = v;
    else if (x.startsWith("aria-") && typeof v === "boolean") e.setAttribute(x, String(v));
    else if (v !== false && v != null) e.setAttribute(x, v === true ? "" : v);
  }
  for (const c of k.flat()) if (c != null) e.append(c);
  return e;
}

function mount(...n) {
  $.replaceChildren(...n.flat());
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

// Transição entre áreas e abas: um véu preto sobe cobrindo a tela, a tela
// nova é desenhada por baixo e o véu continua subindo até sair. Só
// transform; com movimento reduzido vira um fade. Sem animate(), troca direto.
let veu = null;
let veuFila = null;
function swap(fn) {
  if (!document.body.animate) return fn();
  if (veuFila) return void (veuFila = fn);
  veuFila = fn;
  veu ||= document.body.appendChild(h("div", { class: "veu", "aria-hidden": "true" }));
  const calmo = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const ease = "cubic-bezier(0.77, 0, 0.175, 1)";
  const ida = calmo
    ? [{ opacity: 0 }, { opacity: 1 }]
    : [{ transform: "translateY(100%)" }, { transform: "translateY(0)" }];
  const volta = calmo
    ? [{ opacity: 1 }, { opacity: 0 }]
    : [{ transform: "translateY(0)" }, { transform: "translateY(-100%)" }];
  const dur = calmo ? 150 : 420;
  veu.animate(ida, { duration: dur, easing: ease, fill: "forwards" });
  // Relógio, não o fim da animação: com a aba parada a troca acontece igual.
  setTimeout(() => {
    const f = veuFila;
    veuFila = null;
    f();
    veu.animate(volta, { duration: calmo ? 150 : 460, easing: ease, fill: "forwards" });
  }, dur);
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
          h("img", { class: "q", src: x, alt: "Imagem do enunciado", loading: "lazy" })
        );
      else
        x.split(/\n{2,}/).forEach((p) => {
          if (p.trim()) w.append(h("p", null, p.trim()));
        });
    });
  return w;
}

const imgs = (q) =>
  (q.imagens || []).map((u) =>
    h("img", { class: "q", src: u, alt: "Imagem da questão", loading: "lazy" })
  );

const altImg = (src) =>
  h("img", {
    class: "q alt-img",
    src,
    alt: "Alternativa em imagem",
    loading: "lazy",
  });

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

function load() {
  const tx = getJSON("taxonomy.json").catch(() => null);
  getJSON("questions.json")
    .then((d) => {
      if (!Array.isArray(d) || !d.length) throw new Error("banco vazio");
      return tx.then((t) => boot(d, t));
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

