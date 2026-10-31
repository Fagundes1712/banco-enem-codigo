"use strict";

/* =============================== Conta =============================== */

// Entrar, cadastrar, recuperar a senha, assinar e cuidar dos próprios dados.
// Aqui só há formulários: senha, tokens, preço e liberação ficam na API, e os
// tokens vivem em cookie HttpOnly que este código nem consegue ler.
const SITEKEY = document.querySelector('meta[name="turnstile-sitekey"]')?.content || "";
const TS_URL = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
let EU = null; // promessa de /me: { email, assinatura_ativa, assinatura_ate } ou null
let tsPronto = null;

// Usada também pelo bloqueio do plano Pro. forca = pergunta de novo à API.
// Toda troca (entrar, sair, pagar, excluir) avisa com o evento "conta" na window.
function contaAtual(forca) {
  if (!API) return Promise.resolve(null);
  if (!EU || forca) {
    EU = api("/me").then((r) => (r.ok ? r.d : null)).catch(() => null);
    if (forca) EU.then(() => dispatchEvent(new Event("conta")));
  }
  return EU;
}

function semConta() {
  EU = Promise.resolve(null);
  dispatchEvent(new Event("conta"));
}

function abrirAssinatura() {
  if (API) swap(telaConta);
}

// Mensagem de erro da API; validação do FastAPI vem como lista, essa não serve para gente.
const msg = (x) => (typeof x.d.detail === "string" ? x.d.detail : "");
const reais = (c) => (c / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const dia = (iso) => new Date(iso + "Z").toLocaleDateString("pt-BR");
const voltar = () => h("button", { class: "btn back", type: "button", onclick: () => swap(home) }, "Voltar");

function telaDeConta(titulo, ...corpo) {
  mount(h("div", { class: "top" }, h("span", { class: "brand" }, "Banco ENEM"), voltar()), h("h1", null, titulo), ...corpo);
  for (const id of ["nav-inicio", "nav-resp"]) document.getElementById(id)?.removeAttribute("aria-current");
  document.getElementById("nav-conta")?.setAttribute("aria-current", "page");
}

// Caixa do Turnstile (anti-robô do Cloudflare). Devolve o token da vez.
// acao = qual formulário; a API confere que o token veio dele.
function robo(acao) {
  const caixa = h("div", { class: "robo" });
  let token = "";
  let id = null;
  tsPronto ||= new Promise((ok, falha) =>
    document.head.append(h("script", { src: TS_URL, async: true, onload: ok, onerror: falha }))
  );
  tsPronto
    .then(() => {
      id = window.turnstile.render(caixa, {
        sitekey: SITEKEY,
        action: acao,
        callback: (t) => (token = t),
        "expired-callback": () => (token = ""),
      });
    })
    .catch(() => caixa.append(h("p", { class: "note" }, "Não consegui carregar a verificação anti-robô. Recarregue a página.")));
  return { caixa, token: () => token, reset: () => ((token = ""), id != null && window.turnstile?.reset(id)) };
}

const campo = (rotulo, attrs) => h("label", { class: "f" }, rotulo, h("input", { required: true, ...attrs }));

// Formulário padrão: desliga o botão enquanto envia e mostra a resposta da API.
function formulario(campos, botao, enviar, extra) {
  const aviso = h("p", { class: "note", role: "status", "aria-live": "polite" });
  const btn = h("button", { class: "btn primary", type: "submit" }, botao);
  const form = h("form", {
    class: "conta-form",
    onsubmit: (e) => {
      e.preventDefault();
      const dados = Object.fromEntries(new FormData(form));
      btn.disabled = true;
      aviso.textContent = "";
      enviar(dados, aviso)
        .catch(() => (aviso.textContent = "Sem conexão com o servidor. Tente de novo."))
        .finally(() => (btn.disabled = false));
    },
  });
  form.append(...campos, ...(extra ? [extra.caixa] : []), btn, aviso);
  return form;
}

const link = (texto, fn) => h("button", { class: "btn", type: "button", onclick: () => swap(fn) }, texto);

function telaEntrar(msg) {
  const r = robo("login");
  telaDeConta(
    "Entrar",
    msg ? h("p", { class: "lead", role: "status" }, msg) : null,
    formulario(
      [
        campo("E-mail", { name: "email", type: "email", autocomplete: "email" }),
        campo("Senha", { name: "senha", type: "password", autocomplete: "current-password" }),
      ],
      "Entrar",
      (d, aviso) =>
        api("/auth/login", { ...d, turnstile: r.token() }).then((x) => {
          r.reset();
          if (!x.ok) return void (aviso.textContent = msg(x) || "Não deu para entrar.");
          return contaAtual(true).then(telaConta);
        }),
      r
    ),
    h("div", { class: "acoes" }, link("Criar conta", telaCadastro), link("Esqueci a senha", telaEsqueci))
  );
}

function telaCadastro() {
  const r = robo("cadastro");
  telaDeConta(
    "Criar conta",
    h("p", { class: "lead" }, "Com a conta você pode assinar o Banco ENEM Pro."),
    formulario(
      [
        campo("E-mail", { name: "email", type: "email", autocomplete: "email" }),
        campo("Senha (de 8 a 72 caracteres)", { name: "senha", type: "password", autocomplete: "new-password", minlength: 8 }),
        h(
          "label",
          { class: "f aceite" },
          h("input", { type: "checkbox", name: "aceite_termos", required: true }),
          "Li e aceito os termos de uso e a política de privacidade."
        ),
      ],
      "Criar conta",
      (d, aviso) =>
        api("/auth/cadastro", { ...d, aceite_termos: !!d.aceite_termos, turnstile: r.token() }).then((x) => {
          r.reset();
          aviso.textContent = x.ok
            ? "Pronto. Abra o link que enviamos para o seu e-mail (vale por 24 horas) e depois entre."
            : msg(x) || "Não deu para criar a conta.";
        }),
      r
    ),
    h("div", { class: "acoes" }, link("Já tenho conta", telaEntrar))
  );
}

function telaEsqueci() {
  const r = robo("esqueci");
  telaDeConta(
    "Esqueci a senha",
    formulario(
      [campo("E-mail da conta", { name: "email", type: "email", autocomplete: "email" })],
      "Enviar link",
      (d, aviso) =>
        api("/auth/esqueci", { ...d, turnstile: r.token() }).then((x) => {
          r.reset();
          aviso.textContent = x.ok ? x.d.mensagem : msg(x) || "Não deu para enviar.";
        }),
      r
    )
  );
}

function telaNovaSenha(token) {
  telaDeConta(
    "Nova senha",
    formulario(
      [campo("Senha nova (de 8 a 72 caracteres)", { name: "senha", type: "password", autocomplete: "new-password", minlength: 8 })],
      "Trocar senha",
      (d, aviso) =>
        api("/auth/nova-senha", { token, senha: d.senha }).then((x) =>
          x.ok ? telaEntrar(x.d.mensagem) : void (aviso.textContent = msg(x) || "Não deu para trocar.")
        )
    )
  );
}

function telaConta() {
  return contaAtual().then((eu) => (eu ? minhaConta(eu) : telaEntrar()));
}

function minhaConta(eu) {
  const planos = h("div", { class: "acoes" });
  const aviso = h("p", { class: "note", role: "status", "aria-live": "polite" });
  api("/planos")
    .then((x) =>
      planos.append(
        ...(x.ok ? x.d : []).map((p) =>
          h(
            "button",
            { class: "btn primary", type: "button", onclick: (e) => assinarPlano(p.id, e.currentTarget, aviso) },
            (p.id === "anual" ? "Anual, " : "Mensal, ") + reais(p.centavos) + " no Pix"
          )
        )
      )
    )
    .catch(() => (aviso.textContent = "Sem conexão com o servidor."));
  telaDeConta(
    "Sua conta",
    h("p", { class: "lead" }, eu.email),
    h(
      "p",
      null,
      eu.assinatura_ativa ? "Pro ativo até " + dia(eu.assinatura_ate) + "." : "Você está no plano gratuito."
    ),
    h("h2", { class: "secao" }, eu.assinatura_ativa ? "Renovar" : "Assinar o Pro"),
    h("p", { class: "note" }, "O pagamento é pelo Pix na página da AbacatePay. Renovar antes de vencer soma os dias."),
    planos,
    aviso,
    h("h2", { class: "secao" }, "Seus dados"),
    h(
      "div",
      { class: "nav" },
      h("a", { class: "btn", href: API + "/conta/dados", download: "meus-dados-banco-enem.json" }, "Baixar meus dados"),
      h("button", { class: "btn", type: "button", onclick: () => swap(() => telaExcluir(eu)) }, "Excluir conta"),
      h("button", { class: "btn", type: "button", onclick: sairDaConta }, "Sair")
    )
  );
}

function assinarPlano(plano, btn, aviso) {
  btn.disabled = true;
  api("/pagamentos", { plano })
    .then((x) => {
      // Só segue para a página de pagamento se a API devolveu um endereço https.
      if (x.ok && /^https:\/\//.test(x.d.url)) return location.assign(x.d.url);
      aviso.textContent = msg(x) || "Não deu para iniciar o pagamento.";
    })
    .catch(() => (aviso.textContent = "Sem conexão com o servidor."))
    .finally(() => (btn.disabled = false));
}

function sairDaConta() {
  api("/auth/logout", {})
    .catch(() => null)
    .then(() => {
      semConta();
      swap(home);
    });
}

function telaExcluir(eu) {
  telaDeConta(
    "Excluir conta",
    h(
      "p",
      { class: "lead" },
      "Isso apaga a conta " + eu.email + " e não tem volta. Pagamentos já feitos ficam guardados pelo prazo fiscal, sem seu e-mail."
    ),
    formulario(
      [campo("Digite sua senha para confirmar", { name: "senha", type: "password", autocomplete: "current-password" })],
      "Excluir para sempre",
      (d, aviso) =>
        api("/conta/excluir", d).then((x) => {
          if (!x.ok) return void (aviso.textContent = msg(x) || "Não deu para excluir.");
          semConta();
          home();
        })
    )
  );
}

// A senha do cadastro prova que quem clicou no link é quem criou a conta.
function telaConfirmar(token) {
  telaDeConta(
    "Confirmar e-mail",
    h("p", { class: "lead" }, "Digite a senha que você escolheu no cadastro para ativar a conta."),
    formulario(
      [campo("Senha", { name: "senha", type: "password", autocomplete: "current-password" })],
      "Ativar conta",
      (d, aviso) =>
        api("/auth/confirmar", { token, senha: d.senha }).then((x) =>
          x.ok ? telaEntrar(x.d.mensagem) : void (aviso.textContent = msg(x) || "Não deu para confirmar.")
        )
    )
  );
}

// Chamada por boot() (js/base.js): links do e-mail e volta da página de pagamento.
function contaInicio() {
  if (!API) return;
  const q = new URLSearchParams(location.search);
  const [confirmar, novaSenha, pagou] = [q.get("confirmar"), q.get("nova-senha"), q.has("pagamento")];
  if (!confirmar && !novaSenha && !pagou) return;
  // Tira o token do endereço antes de tudo: não fica no histórico nem vaza no Referer.
  history.replaceState(null, "", location.pathname);
  if (novaSenha) return telaNovaSenha(novaSenha);
  if (confirmar) return telaConfirmar(confirmar);
  api("/pagamentos/sincronizar", {})
    .catch(() => null)
    .then(() => contaAtual(true))
    .then(telaConta);
}

const navConta = document.getElementById("nav-conta");
if (navConta && API) {
  navConta.hidden = false;
  navConta.addEventListener("click", () => Q.length && swap(telaConta));
  for (const id of ["nav-inicio", "nav-resp"])
    document.getElementById(id)?.addEventListener("click", () => navConta.removeAttribute("aria-current"));
}
