"use strict";

/* ============================= Resultado ============================= */

function result() {
  mount(
    h("div", { class: "top" }, h("span", { class: "brand" }, "Banco ENEM")),
    h(
      "section",
      { class: "res" },
      h(
        "div",
        { class: "ring", style: "--n:" + T.hits / T.qs.length },
        h("p", { class: "meta" }, "Nota estimada"),
        h("div", { class: "score" }, T.nota)
      ),
      h(
        "div",
        { class: "stats" },
        h("div", null, h("b", null, T.hits + " de " + T.qs.length), h("span", null, "acertos")),
        h("div", null, h("b", null, fmt(T.secs)), h("span", null, "tempo total")),
        T.blank
          ? h("div", null, h("b", null, String(T.blank)), h("span", null, "em branco"))
          : null
      ),
      h("p", { class: "note" }, notaComo()),
      h(
        "div",
        { class: "nav spaced" },
        h("button", { class: "btn primary", onclick: corr }, "Ver correções"),
        h(
          "button",
          { class: "btn", onclick: () => T.back() },
          T.back === home ? "Novo simulado" : T.back === respostas ? "Suas respostas" : "Voltar ao tópico"
        )
      )
    )
  );
}

// Explica de onde veio a nota.
function notaComo() {
  return "Nota que estudantes com a mesma proporção de acertos tiraram no Enem de 2022 a 2025 (mediana oficial do INEP, base da TRI). Toda questão vale o mesmo, de qualquer ano. A nota oficial também pesa quais questões você acertou, então ela pode variar uns 30 pontos para cima ou para baixo.";
}

/* ============================= Correções ============================= */

function corr() {
  mount(
    h(
      "div",
      { class: "top" },
      h("h2", { class: "brand" }, "Correções"),
      h("button", { class: "btn", onclick: result }, "Voltar ao resultado")
    ),
    T.qs.map((q, j) => {
      const u = T.ans[q.id];
      const ok = u === q.gab;
      return h(
        "section",
        { class: "cor" },
        h(
          "p",
          { class: "meta" },
          "Questão " +
            (j + 1) +
            (q._ok ? " · " + IX.top[q.topico].nome : "") +
            (q.lang ? " · " + (q.lang === "ingles" ? "Inglês" : "Espanhol") : "")
        ),
        h(
          "div",
          { class: "cor-head" },
          h(
            "span",
            { class: "tag " + (u ? (ok ? "ok" : "bad") : "nil") },
            u ? (ok ? "Acertou" : "Errou") : "Em branco"
          )
        ),
        rich(q.enunciado),
        imgs(q),
        h(
          "div",
          { class: "alts" },
          Object.entries(q.alts).map(([l, t]) =>
            h(
              "div",
              { class: "alt" + (l === q.gab ? " gab" : l === u ? " err" : "") },
              h("span", { class: "bub" }, l),
              h(
                "span",
                null,
                altc(t),
                l === q.gab
                  ? h("span", { class: "gab-label" }, " · gabarito")
                  : l === u
                    ? h("span", { class: "gab-label" }, " · sua resposta")
                    : null
              )
            )
          )
        ),
        q.resolucao
          ? [h("h3", null, "Resolução"), h("div", { class: "enun" }, q.resolucao)]
          : h("p", { class: "note" }, "Resolução ainda não cadastrada para esta questão.")
      );
    })
  );
}

/* =========================== Navegação =============================== */

document.addEventListener("keydown", (e) => {
  if (!T || !T.live || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.target instanceof Element && e.target.matches("input, select, textarea")) return;
  if (e.key === "ArrowRight" && T.i < T.qs.length - 1) {
    T.i += 1;
    test();
  } else if (e.key === "ArrowLeft" && T.i > 0) {
    T.i -= 1;
    test();
  }
});

load();

/* =========================== Modo offline =========================== */

if (
  "serviceWorker" in navigator &&
  (location.protocol === "https:" ||
    location.hostname === "localhost" ||
    location.hostname === "127.0.0.1")
) {
  // Versão nova do service worker assumiu: recarrega uma vez para não ficar
  // com o shell antigo do cache (só quando já havia um controlando).
  if (navigator.serviceWorker.controller) {
    navigator.serviceWorker.addEventListener("controllerchange", () => location.reload(), { once: true });
  }
  addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js", { updateViaCache: "none" }).catch(() => {
      /* offline é opcional: falha de registro não pode quebrar o app */
    });
  });
}

/* ========================== Observabilidade ========================= */

// Erros do navegador vão para o Sentry (projeto banco-enem-app), só em HTTPS
// (docs/observabilidade.md). Sem IP, cookies nem texto da tela: só a
// mensagem e a pilha do erro. DSN vazio desliga.
const SENTRY_DSN =
  "https://1da0b01364b29b2a5c4cce169c478ee0@o4512336096526336.ingest.us.sentry.io/4512336160292864";
if (SENTRY_DSN && location.protocol === "https:") {
  const s = document.createElement("script");
  s.src = "https://browser.sentry-cdn.com/11.10.0/bundle.min.js";
  s.integrity = "sha384-O/8YQaGGVy/n9jIUzcOiaiJVm4t5+JMNiK/zOa0fWvlSld+FquXemEcwJxQ3x/Lr";
  s.crossOrigin = "anonymous";
  s.onload = () =>
    window.Sentry.init({
      dsn: SENTRY_DSN,
      sendDefaultPii: false,
      tracesSampleRate: 0,
      defaultIntegrations: false,
      integrations: [window.Sentry.globalHandlersIntegration(), window.Sentry.dedupeIntegration()],
      beforeSend: (e) => {
        delete e.user;
        delete e.breadcrumbs;
        return e;
      },
    });
  document.head.append(s);
}
