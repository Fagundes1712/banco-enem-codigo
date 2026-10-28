"use strict";

/* =============================== Home ================================ */

function home() {
  clearInterval(tick);
  if (T) T.live = false;
  S = { ...S, materia: null, topico: null };

  const pool = inArea(S.area);
  const avail = pool.length;
  const pend = Q.filter((q) => q.area === S.area && usable(q) && !q._ok).length;

  const modos = h(
    "div",
    { class: "chips", role: "group", "aria-label": "Tipo de simulado" },
    [
      ["conteudo", "Por conteúdo"],
      ["aleatorio", "Simulado aleatório"],
    ].map(([k, n]) =>
      h(
        "button",
        {
          class: "chip mode",
          type: "button",
          "aria-pressed": S.modo === k,
          onclick: () => keep(() => {
            S.modo = k;
            home();
          }),
        },
        n
      )
    )
  );

  const aleatorio = [
    h(
      "div",
      null,
      h("div", { id: "nl" }, "Quantidade de questões"),
      h(
        "div",
        { class: "chips", role: "group", "aria-labelledby": "nl" },
        QTDS.filter((n) => n <= avail).map((n) =>
          h(
            "button",
            {
              class: "chip",
              type: "button",
              "aria-pressed": S.n === n,
              onclick: () => keep(() => {
                S.n = n;
                home();
              }),
            },
            n
          )
        )
      )
    ),
    h(
      "p",
      { class: "note avail" },
      avail ? avail + " questões disponíveis neste filtro." : "Nenhuma questão neste filtro."
    ),
    h(
      "div",
      null,
      h(
        "button",
        {
          class: "btn primary",
          disabled: !avail,
          onclick: () => start(shuffle(pool.slice()).slice(0, S.n), home),
        },
        "Fazer simulado"
      )
    ),
  ];

  const subs = subsOf(S.area);
  const conteudo = [
    h("h3", { id: "ml" }, "Matérias"),
    subs.length
      ? h(
          "ul",
          { class: "list", "aria-labelledby": "ml" },
          subs.map((s) => {
            const n = inSub(s.id).length;
            return h(
              "li",
              null,
              h(
                "button",
                { class: "item sub", type: "button", onclick: () => materia(s.id) },
                h("span", { class: "item-name" }, s.nome),
                notaTag(notaDe(inSub(s.id))),
                h(
                  "span",
                  { class: "item-meta" },
                  (s.topics.length > 1 ? plural(s.topics.length, "tópico", "tópicos") + " · " : "") +
                    plural(n, "questão", "questões")
                )
              )
            );
          })
        )
      : h("p", { class: "note" }, "Lista de conteúdos indisponível. Use o simulado aleatório."),
    pend
      ? h(
          "p",
          { class: "note pend" },
          plural(pend, "questão desta área ainda aguarda", "questões desta área ainda aguardam") +
            " classificação por tópico e por enquanto só aparece no simulado aleatório."
        )
      : null,
  ];

  document.documentElement.dataset.area = S.area;
  nav("inicio");
  mount(
    h("div", { class: "top" }, h("span", { class: "brand" }, "Banco ENEM")),
    h(
      "div",
      { class: "hero" },
      h("span", { class: "kicker" }, "Provas oficiais do INEP"),
      h("h1", null, "Treine com as provas do ENEM."),
      h(
        "p",
        { class: "lead" },
        num(uniq(Q).length) +
          " questões do ENEM, separadas por área e conteúdo. Bons estudos."
      )
    ),
    h(
      "div",
      {
        class: "tabs",
        role: "tablist",
        "aria-label": "Área do conhecimento",
        onkeydown: (e) => {
          const tabs = [...$.querySelectorAll(".tab")];
          const idx = tabs.findIndex((t) => t.getAttribute("aria-selected") === "true");
          let next = -1;
          if (e.key === "ArrowRight") next = (idx + 1) % tabs.length;
          else if (e.key === "ArrowLeft") next = (idx - 1 + tabs.length) % tabs.length;
          else if (e.key === "Home") next = 0;
          else if (e.key === "End") next = tabs.length - 1;
          if (next < 0) return;
          e.preventDefault();
          tabs[next].click();
        },
      },
      Object.entries(AREAS).map(([k, [n]]) =>
        h(
          "button",
          {
            id: "tab-" + k,
            class: "tab",
            role: "tab",
            type: "button",
            "aria-selected": k === S.area,
            "aria-controls": "setup",
            "data-area": k,
            "data-sigla": k,
            "data-n": plural(inArea(k).length, "questão", "questões"),
            tabindex: k === S.area ? 0 : -1,
            onclick: () => k !== S.area && swap(() => keep(() => {
              S = { ...S, area: k };
              home();
              document.getElementById("tab-" + k)?.focus({ preventScroll: true });
            })),
          },
          n,
          notaTag(notaDe(inArea(k)))
        )
      )
    ),
    h(
      "section",
      {
        class: "panel",
        id: "setup",
        role: "tabpanel",
        "aria-labelledby": "tab-" + S.area,
      },
      h("h2", null, AREAS[S.area][0]),
      h("p", { class: "note" }, AREAS[S.area][1]),
      modos,
      S.modo === "aleatorio" ? aleatorio : conteudo
    ),
    h(
      "footer",
      null,
      "A nota é uma estimativa simplificada, não a nota oficial do INEP."
    )
  );
}

/* ============================= Matéria =============================== */

const back = (txt, fn) =>
  h("button", { class: "btn back", type: "button", onclick: fn }, "‹ " + txt);

function materia(id) {
  clearInterval(tick);
  if (T) T.live = false;
  const s = IX.sub[id];
  // Matéria de um tópico só (Inglês, Espanhol) vai direto para as questões.
  if (s.topics.length === 1) return topico(s.topics[0].id);
  S = { ...S, materia: id, topico: null };
  document.documentElement.dataset.area = s.area;
  nav("inicio");

  mount(
    h("div", { class: "top" }, back(AREAS[s.area][0], home)),
    h("p", { class: "eyebrow" }, AREAS[s.area][0]),
    h("h1", null, s.nome),
    h(
      "p",
      { class: "lead" },
      plural(s.topics.length, "grande tópico", "grandes tópicos") +
        " · " +
        plural(inSub(id).length, "questão classificada", "questões classificadas")
    ),
    h(
      "ul",
      { class: "list topics", "aria-label": "Grandes tópicos de " + s.nome },
      s.topics.map((t) => {
        const qs = inTop(t.id);
        const done = qs.filter((q) => H[canon(q)]).length;
        return h(
          "li",
          null,
          h(
            "button",
            { class: "item top-item", type: "button", onclick: () => topico(t.id) },
            h("span", { class: "item-name" }, t.nome),
            notaTag(notaDe(qs)),
            h(
              "span",
              { class: "item-meta" },
              qs.length
                ? plural(qs.length, "questão", "questões") + (done ? " · " + done + " respondidas" : "")
                : "Sem questões ainda"
            )
          )
        );
      })
    )
  );
}

