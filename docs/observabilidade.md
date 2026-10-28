# Observabilidade

O app é estático no GitHub Pages, sem servidor. O que dá para observar é o navegador de quem usa: erros de JavaScript e promessas rejeitadas. Para isso o projeto usa o Sentry (plano gratuito). Datadog, New Relic e OpenTelemetry não foram adotados: cobrem a mesma coisa no navegador e brilham com servidor, que o projeto não tem.

## Estado
Preparado e **desligado**. O código está no fim de `js/resultado.js` e só carrega o SDK quando `SENTRY_DSN` tem valor e a página está em HTTPS.

## O que é enviado
Só a mensagem e a pilha do erro (com os nomes dos arquivos do app). Desligado: URL e navegador (integração `httpContext`), IP e dados pessoais (`sendDefaultPii: false`), usuário, trilha de cliques (breadcrumbs), replay de sessão e medição de desempenho. O SDK vem do CDN do Sentry com versão fixa e hash de integridade (SRI).

## Para ligar
1. Criar a conta e um projeto "Browser JavaScript" no Sentry (região UE se preferir dados fora dos EUA).
2. Copiar o DSN para `SENTRY_DSN` em `js/resultado.js`, subir `VERSION` em `sw.js`, `npm run mirror`, PR.
3. Antes de publicar, atualizar a política de privacidade (LGPD): o Sentry é operador de dados, há transferência internacional e a base legal provável é legítimo interesse (Art. 7, IX). As skills `lgpd-vendor-audit` e `lgpd-privacy-policy` ajudam.

## Atualizar o SDK
Trocar a versão na URL e recalcular o hash:
`curl -sL https://browser.sentry-cdn.com/<versão>/bundle.min.js | openssl dgst -sha384 -binary | openssl base64 -A`
