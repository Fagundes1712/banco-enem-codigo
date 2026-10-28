# Observabilidade

O app é estático no GitHub Pages, sem servidor. O que dá para observar é o navegador de quem usa: erros de JavaScript e promessas rejeitadas. Para isso o projeto usa o Sentry (plano gratuito). Datadog, New Relic e OpenTelemetry não foram adotados: cobrem a mesma coisa no navegador e brilham com servidor, que o projeto não tem.

## Estado
**Ligado** desde a v35 (2026-10-28), projeto `banco-enem-app` na organização `banco-enem` (região EUA), só com Monitoramento de erros. O código está no fim de `js/resultado.js` e só carrega o SDK quando `SENTRY_DSN` tem valor e a página está em HTTPS; local (`npm start`) e e2e usam HTTP e não enviam nada. Para desligar, deixar `SENTRY_DSN` vazio.

## O que é enviado
Só a mensagem e a pilha do erro (com os nomes dos arquivos do app). Desligado: URL e navegador (integração `httpContext`), IP e dados pessoais (`sendDefaultPii: false`), usuário, trilha de cliques (breadcrumbs), replay de sessão e medição de desempenho. O SDK vem do CDN do Sentry com versão fixa e hash de integridade (SRI).

## LGPD
O Sentry é operador de dados e há transferência internacional (EUA); a base legal provável é legítimo interesse (Art. 7, IX). O app ainda não tem política de privacidade: pendência registrada na issue #2. As skills `lgpd-vendor-audit` e `lgpd-privacy-policy` ajudam. No painel do Sentry, deixar ligado "Prevent Storing of IP Addresses" (Settings › Projects › banco-enem-app › Security & Privacy).

## Atualizar o SDK
Trocar a versão na URL e recalcular o hash:
`curl -sL https://browser.sentry-cdn.com/<versão>/bundle.min.js | openssl dgst -sha384 -binary | openssl base64 -A`
