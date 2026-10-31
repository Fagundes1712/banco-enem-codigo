# Ligar login e assinatura em produção

Passo a passo do que só o responsável pode fazer (contas, chaves, pagamento). O código já está pronto em `api/` (API) e `js/conta.js` (telas); enquanto `<meta name="api-url">` estiver vazio no `index.html`, o site segue sem conta.

Regras durante todo o processo:
- Nunca cole chave, senha ou token em issue, PR, commit ou conversa com o Claude. Elas vão só nos painéis indicados.
- Use o mesmo e-mail com verificação em duas etapas em todos os serviços.
- Faça tudo primeiro no **modo de teste** da AbacatePay. Produção só no passo 10.

Nos exemplos o domínio é `seudominio.com.br`: troque pelo seu.

## 1. Domínio (Registro.br, pago)
1. Em https://registro.br, pesquise o nome e registre o `.com.br` (cerca de R$ 40 por ano; precisa de CPF).
2. Guarde a senha do Registro.br no seu gerenciador de senhas.

Por que é obrigatório: os cookies de login só passam entre o site e a API se os dois estiverem no mesmo domínio (`seudominio.com.br` e `api.seudominio.com.br`). Com `pages.dev` e `run.app` o navegador bloqueia.

## 2. Cloudflare (grátis)
1. Crie a conta em https://dash.cloudflare.com/sign-up e clique em **Add a domain** com o seu domínio, plano **Free**.
2. A Cloudflare mostra dois *nameservers*. No Registro.br, em **DNS > Alterar servidores DNS**, troque pelos dois. Pode levar algumas horas.
3. Em **SSL/TLS > Overview**, escolha **Full (strict)**.
4. Site: o `deploy.yml` já publica no Cloudflare Pages (ver `docs/security.md`, variável `CLOUDFLARE_PAGES_PROJETO`). No projeto do Pages, em **Custom domains**, adicione `seudominio.com.br`.
5. Turnstile: em **Turnstile > Add widget**, nome "Banco ENEM", domínio `seudominio.com.br`, modo **Managed**. Guarde a **Site key** (pública) e a **Secret key** (secreta).

## 3. Banco de dados (Neon, grátis)
1. Crie a conta em https://neon.com e um projeto "banco-enem" na região mais próxima de São Paulo que aparecer.
2. Em **Connect**, ligue **Connection pooling** e copie o endereço (tem `-pooler` no nome).
3. Troque o começo `postgresql://` por `postgresql+psycopg://`. Esse é o `DATABASE_URL`.

## 4. Redis (Upstash, grátis)
1. Crie a conta em https://upstash.com e um banco **Redis** na região mais próxima.
2. Copie o endereço que começa com `rediss://` (com a senha embutida). Esse é o `REDIS_URL`.

## 5. E-mail (Resend, grátis)
1. Crie a conta em https://resend.com e em **Domains** adicione `seudominio.com.br`.
2. O Resend mostra registros DNS (SPF, DKIM). Cadastre cada um na Cloudflare em **DNS > Records** e espere ficar **Verified**.
3. Em **API Keys**, crie uma chave com permissão **Sending access** só para esse domínio. Esse é o `RESEND_API_KEY`.

## 6. AbacatePay (sem mensalidade, R$ 0,80 por Pix)
1. Crie a conta em https://www.abacatepay.com e ligue o **Modo Teste (Sandbox)**.
2. Em **Integração > API**, crie uma chave **API v2**, escopo **Personalizado**, só com `CHECKOUT:CREATE`, `CHECKOUT:READ`, `PRODUCT:CREATE` e `PRODUCT:READ`.
3. Gere o segredo do webhook no seu computador: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
4. Pergunte ao suporte se a API v2 aceita cartão parcelado em 12x; com isso dá para oferecer o anual em 12x de R$ 19,99.

## 7. Google Cloud Run (grátis até a cota, pede cartão)
1. Crie a conta em https://console.cloud.google.com, um projeto "banco-enem" e ligue a cobrança.
2. Em **Billing > Budgets & alerts**, crie um orçamento de R$ 5 com alerta por e-mail. Isso avisa antes de qualquer gasto.
3. Instale o Google Cloud CLI (https://cloud.google.com/sdk/docs/install) e rode `gcloud init`.
4. Gere a chave do JWT e o segredo de origem, cada um com `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
5. Crie os segredos no Secret Manager, um por vez (o valor é digitado, não fica no histórico do terminal):
   ```bash
   for s in DATABASE_URL REDIS_URL JWT_SECRET TURNSTILE_SECRET RESEND_API_KEY ABACATEPAY_API_KEY ABACATEPAY_WEBHOOK_SECRET ORIGEM_SECRET; do
     read -rsp "$s: " v; echo; printf %s "$v" | gcloud secrets create "$s" --data-file=-
   done
   ```
6. Publique a API a partir da pasta `api/`:
   ```bash
   cd api
   gcloud run deploy banco-enem-api --source . --region southamerica-east1 \
     --allow-unauthenticated --max-instances 10 \
     --set-env-vars AMBIENTE=producao,SITE_URL=https://seudominio.com.br,COOKIE_DOMAIN=.seudominio.com.br,EMAIL_REMETENTE="Banco ENEM <nao-responda@seudominio.com.br>",ABACATEPAY_DEV_MODE=true \
     --set-secrets DATABASE_URL=DATABASE_URL:latest,REDIS_URL=REDIS_URL:latest,JWT_SECRET=JWT_SECRET:latest,TURNSTILE_SECRET=TURNSTILE_SECRET:latest,RESEND_API_KEY=RESEND_API_KEY:latest,ABACATEPAY_API_KEY=ABACATEPAY_API_KEY:latest,ABACATEPAY_WEBHOOK_SECRET=ABACATEPAY_WEBHOOK_SECRET:latest,ORIGEM_SECRET=ORIGEM_SECRET:latest
   ```
   Enquanto testa com `ABACATEPAY_DEV_MODE=true`, a API recusa subir com `AMBIENTE=producao`; use `AMBIENTE=dev` nesse período e troque os dois no passo 10.
7. Em **Cloud Run > banco-enem-api > Manage custom domains**, mapeie `api.seudominio.com.br` e cadastre na Cloudflare o registro que o Google pedir, com a nuvem **laranja** (proxy ligado).

## 8. Proteção na Cloudflare
0. **Rules > Transform Rules > Modify Request Header**: regra "origem" para `http.host eq "api.seudominio.com.br"`, **Set static** `X-Origem` = o mesmo valor do `ORIGEM_SECRET`. Sem isso a API responde 403 a tudo; com isso, quem chama o endereço `run.app` direto, pulando a Cloudflare, é barrado.
1. **Security > WAF > Rate limiting rules**: crie a regra "login", expressão `(http.host eq "api.seudominio.com.br" and starts_with(http.request.uri.path, "/auth/"))`, contar por IP, 10 pedidos em 10 segundos, ação **Block** por 10 segundos.
2. **Security > Bots**: ligue **Bot Fight Mode**.
3. **Security > WAF > Managed rules**: deixe ligadas as regras gratuitas.
4. Se o Bot Fight Mode bloquear o webhook, crie em **WAF > Custom rules** uma regra **Skip** para o caminho `/webhooks/abacatepay`.

## 9. Ligar o site na API
Peça ao Claude (ou faça você) num PR:
1. No `index.html`: `<meta name="api-url" content="https://api.seudominio.com.br">` e `<meta name="turnstile-sitekey" content="SUA_SITE_KEY">` (a site key é pública).
2. Na CSP do `index.html` e do `_headers`, acrescente `https://api.seudominio.com.br` em `connect-src`. O `npm run check` acusa se faltar.
3. Na AbacatePay, cadastre o webhook `https://api.seudominio.com.br/webhooks/abacatepay?webhookSecret=<ABACATEPAY_WEBHOOK_SECRET>` com o evento `checkout.completed`.
4. Teste no site: criar conta, abrir o e-mail, entrar, assinar o mensal, simular o pagamento na página da AbacatePay e ver "Pro ativo até".

## 10. Produção
Só depois do passo 9 funcionar no modo de teste:
1. Na AbacatePay, desligue o Modo Teste e crie uma chave de produção com os mesmos escopos; troque o segredo `ABACATEPAY_API_KEY` (`printf %s "$v" | gcloud secrets versions add ABACATEPAY_API_KEY --data-file=-`).
2. Refaça o deploy com `AMBIENTE=producao,ABACATEPAY_DEV_MODE=false`.
3. Cadastre o webhook de novo no modo de produção.
4. Faça uma compra real de R$ 24,99 e confira o acesso.
5. Antes de divulgar: publicar política de privacidade e termos de uso revisados por advogado (`docs/privacidade.md`; skill `lgpd-privacy-policy`) e o e-mail do encarregado.

## Custos esperados
Zero nos planos grátis até o primeiro limite (100 e-mails por dia no Resend, 100 horas de computação no Neon, 500 mil comandos no Upstash, 2 milhões de pedidos no Cloud Run). Fixo: o domínio. Variável: R$ 0,80 por Pix recebido.
