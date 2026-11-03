# Observabilidade

O site é estático (GitHub Pages e Cloudflare Pages). O que dá para observar nele é o navegador de quem usa: erros de JavaScript e promessas rejeitadas, enviados ao Sentry (plano gratuito). A API de login e Pix (`api/`) existe, mas ainda não está publicada; quando estiver, os eventos de segurança saem nos logs do Cloud Run (`api/app/auditoria.py`, uma linha JSON por evento, sem e-mail nem IP). Datadog, New Relic e OpenTelemetry não foram adotados: repetiriam o Sentry no navegador e os logs do Cloud Run na API. Ligar o Sentry também na API (`sentry-sdk[fastapi]`) fica para quando ela for ao ar, com a mesma regra de não enviar dados pessoais.

## Estado
**Ligado** desde a v35 (2026-10-28), projeto `banco-enem-app` na organização `banco-enem` (região EUA), só com Monitoramento de erros. O código está no fim de `js/resultado.js` e só carrega o SDK quando `SENTRY_DSN` tem valor e a página está em HTTPS; local (`npm start`) e e2e usam HTTP e não enviam nada. Para desligar, deixar `SENTRY_DSN` vazio. A CSP libera só `browser.sentry-cdn.com` (script) e o ingest do projeto (`connect-src`). Desde a v41, os erros das prévias de PR (`pr-<n>.banco-enem.pages.dev`) chegam com o ambiente `previa` e os do site com `producao`; no Sentry, filtre por ambiente.

## O que é enviado
Só a mensagem e a pilha do erro (com os nomes dos arquivos do app). Desligado: URL e navegador (integração `httpContext`), IP e dados pessoais (`sendDefaultPii: false`), usuário, trilha de cliques (breadcrumbs), replay de sessão e medição de desempenho. O SDK vem do CDN do Sentry com versão fixa e hash de integridade (SRI).

## LGPD
O Sentry é operador de dados e há transferência internacional (EUA); a base legal provável é legítimo interesse (Art. 7, IX). "Prevent Storing of IP Addresses" está ligado no projeto (Settings › Projects › banco-enem-app › Security & Privacy) e os eventos ficam até 90 dias. A política de privacidade já cita o Sentry, mas ainda é rascunho, sem publicar (`docs/privacidade.md`).

## Atualizar o SDK
Trocar a versão na URL e recalcular o hash:
`curl -sL https://browser.sentry-cdn.com/<versão>/bundle.min.js | openssl dgst -sha384 -binary | openssl base64 -A`
