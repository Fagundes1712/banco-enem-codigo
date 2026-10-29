# Segurança

Estado verificado em 2026-10-28. O app é estático: não há servidor próprio, banco de dados, contas, formulários nem segredos no navegador. A superfície de ataque é o que o GitHub Pages serve e o que o navegador executa.

## Modelo de ameaça
| Ameaça | Situação | Controle |
|---|---|---|
| XSS | Baixa. Os dados vêm de `questions.json` do próprio repositório; a interface monta o DOM com `createElement`/`setAttribute` (`h()` em `js/base.js`), sem `innerHTML`, `eval` nem `new Function`. | CSP em `index.html` bloqueia script de outra origem e script inline. |
| Script ou arquivo malicioso publicado | Exige escrita no repositório. | `main` protegida (PR + check `verify`, vale para admin), push protection e secret scanning ligados, deploy só por chave SSH de escopo único. |
| Dependência comprometida | Só `jsdom`, e só nos testes; nada vai para o site. | `npm ci` com lockfile; `npm audit` = 0 vulnerabilidades em 2026-10-28; Dependabot (`.github/dependabot.yml`). |
| Action do GitHub comprometida | Uma tag movida executaria código novo com acesso ao segredo de deploy. | Actions fixadas por hash de commit, com a versão em comentário; o Dependabot atualiza hash e comentário. |
| Segredo vazado | Nenhum encontrado nos arquivos nem no histórico (busca por padrões de chave, token e senha em 2026-10-28). | Único segredo: `DEPLOY_KEY_SITE`, guardado em Actions secrets. |
| CSRF, SQL injection, SSRF, upload | Não aplicável: não há servidor, formulário, banco nem upload. | — |
| Força bruta, enumeração de contas | Não aplicável: não há login. | — |

## HTTPS e cabeçalhos
- Produção: `https://fagundes1712.github.io/banco-enem-app/`. O GitHub Pages emite e renova o certificado TLS; `https_enforced` está ligado (API do Pages) e `http://` responde 301 para `https://`. O cabeçalho `Strict-Transport-Security: max-age=31556952` vem do próprio GitHub.
- O GitHub Pages não deixa configurar cabeçalhos. Por isso a política vai em `<meta http-equiv="Content-Security-Policy">` no `index.html`, e `npm run check` falha se ela sumir.
- Política atual: só a própria origem para script (mais o bundle do Sentry em `browser.sentry-cdn.com`, com SRI), envio de erros só para o ingest do projeto no Sentry, dados, imagens, manifesto e service worker; estilos e fontes só da própria origem, sem `'unsafe-inline'`; `object-src 'none'`, `base-uri 'self'`, `form-action 'none'`.
- Estilo dinâmico (barras, anel, véu) passa por CSSOM: `h()` em `js/base.js` grava `style` com `e.style.cssText`, que a CSP permite, em vez do atributo `style`, que ela bloqueia. Nunca usar `setAttribute("style", ...)`, `<style>` nem `style="..."` no HTML.
- `frame-ancestors` (clickjacking), `X-Content-Type-Options`, `X-Frame-Options`, `Permissions-Policy` e `Cross-Origin-Opener-Policy` só funcionam como cabeçalho HTTP, que o GitHub Pages não deixa configurar. Eles estão em `_headers`, aplicado pela cópia no Cloudflare Pages (abaixo). `npm run check` exige que a CSP do `_headers` seja a do `<meta>` mais `frame-ancestors 'none'`.

## Cópia com cabeçalhos (Cloudflare Pages)
- O `deploy.yml` publica `site/public/` também no Cloudflare Pages quando a variável de repositório `CLOUDFLARE_PAGES_PROJETO` existe, usando os segredos `CLOUDFLARE_API_TOKEN` (permissão Account › Cloudflare Pages › Edit, só isso) e `CLOUDFLARE_ACCOUNT_ID`. Sem a variável, o passo é pulado.
- Endereço: `https://<projeto>.pages.dev/`, com TLS e HSTS do domínio `.dev` (pré-carregado nos navegadores). Plano grátis, sem domínio próprio.
- O passo confere que a `VERSION` no ar bate e que a resposta traz `frame-ancestors 'none'`.
- O wrangler roda por `npx` em versão exata (`4.155.0`); o Dependabot não o atualiza, então suba à mão quando precisar.
- Enquanto o endereço principal divulgado for o do GitHub Pages, os cabeçalhos só valem para quem entra pelo `pages.dev`. Trocar o endereço principal é decisão do responsável; o progresso salvo no navegador é por endereço e não passa de um para o outro.
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
