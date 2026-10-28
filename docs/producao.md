# Prontidão para produção

Auditoria de 2026-10-28 contra a lista de requisitos de um SaaS. O produto real é um PWA estático e gratuito, sem servidor, contas ou cobrança (`PRODUCT.md`), então boa parte da lista não se aplica. Reavaliar esta página se o escopo mudar.

Estados: **validado** (há evidência), **implementado, não validado**, **pendente de configuração**, **bloqueado**, **não aplicável** (com motivo).

| Requisito | Estado | Evidência ou motivo |
|---|---|---|
| Produto original preservado | validado | 169 checks do `npm run verify`; fluxo home, simulado e resultado no navegador sem erro |
| Build e inicialização | validado | Não há build; `npm start` serve a pasta; clone limpo sobe e passa nos testes (`docs/operacao.md`) |
| Persistência no servidor | não aplicável | Progresso fica no `localStorage` por decisão de produto ("Fora do escopo: contas, servidor ou sincronização") |
| Migrações, transações, concorrência | não aplicável | Sem banco de dados nem operação concorrente |
| Autenticação, sessões, rate limit de login, hash de senha | não aplicável | Sem login |
| Isolamento entre clientes | não aplicável | Sem dados no servidor; cada navegador só vê o próprio `localStorage` |
| Segredos e histórico do Git | validado | Nenhuma credencial nos arquivos nem no histórico; secret scanning e push protection ligados (`docs/security.md`) |
| HTTPS e TLS | validado | Certificado do GitHub Pages, `https_enforced`, 301 de http para https, HSTS |
| Cabeçalhos de segurança | implementado, validado em parte | CSP por meta testada no navegador; `frame-ancestors` e outros cabeçalhos dependem de CDN própria |
| Firewall e portas | não aplicável | Sem servidor próprio; servidor local só em `127.0.0.1` |
| DDoS e abuso | não aplicável além da hospedagem | Coberto pela CDN do GitHub; sem endpoint próprio; limites em `docs/security.md` |
| Dependências vulneráveis | validado | `npm audit`: 0; Dependabot configurado (`.github/dependabot.yml`) |
| APIs e integrações | não aplicável | Só Google Fonts (arquivos estáticos) |
| Pagamentos, webhooks, estornos | não aplicável | App gratuito, sem cobrança |
| E-mail, SPF, DKIM, DMARC | não aplicável | O app não envia e-mail e não tem domínio próprio |
| Nota fiscal | não aplicável | Sem receita |
| LGPD | avaliado, decisões pendentes | `docs/privacidade.md` |
| Testes | validado | jsdom com o banco real, hook e checagem; ampliação em andamento na issue #2 |
| CI, issues, PRs, proteção da `main` | validado | PR #1; proteção exige `verify` atualizado, também para admin |
| Deploy e rollback | validado | `deploy.yml` com conferência pós-deploy; rollback por `workflow_dispatch` (`docs/fluxo.md`) |
| Homologação e preview por PR | não aplicável hoje | Custo de manutenção maior que o ganho; PR validado no CI e localmente |
| Backup e restauração | validado | Clone limpo restaurado e testado em 2026-10-28 |
| Monitoramento e alertas | implementado, limitado | Falha de CI e deploy avisa por e-mail; sem monitor de disponibilidade nem captura de erros (issue #2) |
| Custos | validado | Zero: GitHub Free com repositórios públicos, Pages e Actions gratuitos |

## Se o produto ganhar contas ou sincronização
Isso muda a arquitetura e abre os itens marcados como não aplicáveis (auth, isolamento, banco, backups de dados, LGPD completa). Opções gratuitas para avaliar na época: Supabase (Postgres com RLS, plano grátis com pausa por inatividade), Firebase (Firestore com regras, plano Spark) ou Cloudflare Workers + D1. Decisão do responsável antes de qualquer código.
