# Segurança

Estado verificado em 2026-10-28. O app é estático: não há servidor próprio, banco de dados, contas, formulários nem segredos no navegador. A superfície de ataque é o que o GitHub Pages serve e o que o navegador executa.

## Modelo de ameaça
| Ameaça | Situação | Controle |
|---|---|---|
| XSS | Baixa. Os dados vêm de `questions.json` do próprio repositório; a interface monta o DOM com `createElement`/`setAttribute` (`h()` em `js/base.js`), sem `innerHTML`, `eval` nem `new Function`. | CSP em `index.html` bloqueia script de outra origem e script inline. |
| Script ou arquivo malicioso publicado | Exige escrita no repositório. | `main` protegida (PR + check `verify`, vale para admin), push protection e secret scanning ligados, deploy só por chave SSH de escopo único. |
| Dependência comprometida | Só `jsdom`, e só nos testes; nada vai para o site. | `npm ci` com lockfile; `npm audit` = 0 vulnerabilidades em 2026-10-28; Dependabot (`.github/dependabot.yml`). |
| Segredo vazado | Nenhum encontrado nos arquivos nem no histórico (busca por padrões de chave, token e senha em 2026-10-28). | Único segredo: `DEPLOY_KEY_SITE`, guardado em Actions secrets. |
| CSRF, SQL injection, SSRF, upload | Não aplicável: não há servidor, formulário, banco nem upload. | — |
| Força bruta, enumeração de contas | Não aplicável: não há login. | — |

## HTTPS e cabeçalhos
- Produção: `https://fagundes1712.github.io/banco-enem-app/`. O GitHub Pages emite e renova o certificado TLS; `https_enforced` está ligado (API do Pages) e `http://` responde 301 para `https://`. O cabeçalho `Strict-Transport-Security: max-age=31556952` vem do próprio GitHub.
- O GitHub Pages não deixa configurar cabeçalhos. Por isso a política vai em `<meta http-equiv="Content-Security-Policy">` no `index.html`, e `npm run check` falha se ela sumir.
- Política atual: só a própria origem para script, dados, imagens, manifesto e service worker; estilos da origem e do Google Fonts (`'unsafe-inline'` porque a interface usa atributos `style` para barras e anéis); fontes do `fonts.gstatic.com`; `object-src 'none'`, `base-uri 'self'`, `form-action 'none'`.
- Limites da meta: `frame-ancestors` (proteção contra clickjacking), `X-Content-Type-Options` e `Permissions-Policy` só funcionam como cabeçalho HTTP. Risco baixo aqui, porque a página não tem ação sensível para enganar alguém a clicar. Para tê-los seria preciso um domínio com CDN que injete cabeçalhos (por exemplo Cloudflare grátis), decisão que envolve DNS.
- Ao adicionar um serviço externo (Sentry, analytics, outra fonte), atualize a CSP no mesmo PR e teste o fluxo no navegador: o que não estiver na lista é bloqueado.

## DDoS e abuso
O site é servido pela CDN do GitHub Pages (Fastly). Não há endpoint que consuma recurso próprio, então não há rate limit a implementar. Limites reais: o Pages tem cota de banda (cerca de 100 GB por mês, limite flexível) e pode suspender o site em caso de abuso; não há proteção contratada nem alerta de tráfego. Proteção total contra DDoS não existe neste plano.

## Rede local
`npm start` e `.claude/launch.json` sobem o servidor só em `127.0.0.1`, para não expor a pasta do projeto a outros aparelhos da rede.

## Segredos
- `DEPLOY_KEY_SITE` (Actions secret do `banco-enem-codigo`): chave privada SSH; a pública está como deploy key com escrita só no `banco-enem-app`.
- Rotação: gerar um par novo (`ssh-keygen -t ed25519 -N "" -f deploy_site`), cadastrar a pública em `banco-enem-app` › Settings › Deploy keys (com escrita), trocar o segredo em `banco-enem-codigo` › Settings › Secrets and variables › Actions, rodar Actions › Deploy › Run workflow, conferir que passou e só então apagar a deploy key antiga e os arquivos locais.
- Nunca colar segredo em issue, PR, commit ou conversa.

## Revisão
Mudança com risco de segurança usa `docs/prompts/security-review.md`. Vulnerabilidades: veja `SECURITY.md`.
