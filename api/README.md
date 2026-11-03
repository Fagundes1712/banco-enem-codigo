# API do Banco ENEM

Backend em Python (FastAPI) para contas e assinatura por Pix. O site continua estático; só login e pagamento passam por aqui. Desenho completo no guia [Login e pagamentos do Banco ENEM](https://claude.ai/artifact/Sx3ZSqkseP3ycuCaSKCDsU).

## Rodar na sua máquina

```bash
cd api
py -3.12 -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt   # Linux/macOS: .venv/bin/pip
cp .env.example .env                                 # preencha; precisa de um PostgreSQL
.venv/Scripts/python -m pytest                       # testes (SQLite e serviços simulados)
```

Para subir o servidor, carregue as variáveis do `.env` no terminal, crie os papéis e as tabelas (ver "Banco de dados") e rode `.venv/Scripts/uvicorn app.main:app --reload`.

## Rotas

| Rota | O que faz |
| --- | --- |
| `POST /auth/cadastro` | Cria a conta (e-mail, senha, Turnstile, aceite dos termos) e manda o link de confirmação (24 h) |
| `POST /auth/confirmar` | Ativa a conta com o token do link e a senha do cadastro (quem cadastrou o e-mail de outra pessoa não fica com a conta) |
| `POST /auth/login` | Confere a senha e grava os cookies `acesso` (JWT, 15 min) e `renovacao` (30 dias) |
| `POST /auth/refresh` | Troca o token de renovação; reuso de token velho derruba todas as sessões |
| `POST /auth/logout` | Revoga a sessão e apaga os cookies |
| `POST /auth/esqueci`, `POST /auth/nova-senha` | Recuperação de senha por link de 30 min |
| `GET /me` | E-mail e situação da assinatura |
| `GET /planos` | Planos e preços (do servidor) |
| `POST /pagamentos` | Cria o checkout Pix do plano `mensal` ou `anual` e devolve a URL de pagamento |
| `POST /pagamentos/sincronizar` | Confere na AbacatePay os pagamentos pendentes do usuário |
| `POST /webhooks/abacatepay?webhookSecret=...` | Aviso de pagamento da AbacatePay |
| `GET /conta/dados` | Baixa em JSON tudo o que guardamos da pessoa |
| `POST /conta/excluir` | Exclui a conta (pede a senha) |

## Regras de segurança

- Senha com bcrypt custo 12; acima de 72 bytes é recusada. Login de e-mail inexistente roda o bcrypt contra um hash falso.
- JWT HS256 com `exp`, `iss` e `aud` conferidos e algoritmo fixo. Tokens só em cookie `HttpOnly; SameSite=Strict` (e `Secure` em produção).
- Trocar a senha ou excluir a conta invalida na hora os tokens de acesso já emitidos (`senha_trocada_em`).
- Turnstile: em produção a API confere também o domínio e o formulário (`action`) do token.
- POST sem `Content-Length` é recusado (411) e o corpo tem limite de 64 KB.
- Toda rota que muda algo exige o cabeçalho `Origin` igual a `SITE_URL` (CSRF), menos o webhook.
- Limite de tentativas por IP e por e-mail no Redis; Turnstile no cadastro, login e recuperação.
- Preço e dias vêm de `PLANOS` em `app/pagamentos.py`. O pagamento só libera quando a AbacatePay confirma o valor, e uma vez só.
- Pagamento do Modo Teste nunca libera produção (`ABACATEPAY_DEV_MODE`).
- Em produção todo pedido precisa do cabeçalho `X-Origem` que a Cloudflare acrescenta (`ORIGEM_SECRET`); o endereço do Cloud Run sozinho não responde.
- E-mails saem depois da resposta, e o cadastro roda o bcrypt mesmo para e-mail já cadastrado: o tempo não revela quem tem conta.
- `GET /conta/dados` (baixar meus dados) e `POST /conta/excluir` (com senha) atendem a LGPD; pagamento feito fica pelo prazo fiscal, sem e-mail nem senha.

Passo a passo para publicar: `docs/backend-setup.md`.

## Banco de dados

Papéis criados por `migracoes/papeis.sql`:

| Papel | Para quê | Limite |
| --- | --- | --- |
| `api_app` | A API, em `DATABASE_URL` | Sujeito ao RLS; não cria nem altera tabela |
| `api_migracao` | O Alembic no deploy, em `MIGRACAO_DATABASE_URL` | A API nunca recebe esta variável |
| `api_busca` | Dono das funções de busca | Sem login; só lê as colunas de id e de busca |
| `painel_leitura` | O painel, em `PAINEL_DATABASE_URL` | Não lê tabela; só executa as funções de totais |
| `api_totais` | Dono das funções de totais e de `soma_uso` | Sem login; sem acesso a e-mail e senha |

- RLS forçado em todas as tabelas (`migracoes/versions/0002_rls.py`). `define_usuario` fixa `app.usuario_id` na transação e `_reaplica_usuario` repete isso depois de cada commit. Sem usuário definido, as consultas voltam vazias.
- Antes de haver usuário logado (login, links do e-mail, renovação, webhook), `assume_dono` chama uma função do banco que devolve só o id do dono de um e-mail, token ou checkout, e o resto da rota segue sob o RLS. Tabela nova precisa de RLS na migração: `test_toda_tabela_tem_rls_forcado` quebra se faltar.
- `movimentos` é a trilha de pagamentos: o `api_app` só tem `SELECT` e `INSERT` nela.
- O RLS é a segunda linha de defesa contra um bug de consulta. Não segura quem tomar controle da API, que pode escolher o `app.usuario_id`; para isso servem as outras camadas.

Mudou um modelo em `app/db.py`? Gere a migração (`alembic revision --autogenerate -m "..."`), revise e rode `alembic upgrade head` com `MIGRACAO_DATABASE_URL`. O CI roda subida, descida e `alembic check`, e toda a suíte como `api_app` num PostgreSQL migrado. O SQLite dos testes locais não tem RLS, então `test_rls.py` só roda no CI.

## Painel do desenvolvedor

`/painel` mostra só totais: contas, assinantes, faturamento, questões, minutos e conversão. Desligado sem `PAINEL_EMAIL`. Quatro trancas, em ordem:

1. Cloudflare Access na frente de `painel.<domínio>`, só para o seu e-mail.
2. A API confere o token do Access (assinatura, emissor, aplicativo e e-mail). Sem ele, toda rota responde 404.
3. Código do autenticador (TOTP), de uso único, com 5 tentativas a cada 15 minutos.
4. Sessão de 1 hora em cookie só de `/painel`; cada entrada vai para a auditoria e gera e-mail.

`POST /uso` recebe do site, no fim do simulado, só quantidade de questões e minutos. A API soma por dia e plano e não lê a tabela de volta.

## Limitações conhecidas

- Só Pix. Parcelamento em 12x no cartão depende de confirmar o suporte na API da AbacatePay.
- Assinatura mensal por Pix não renova sozinha: o aluno paga de novo e os dias são somados.
- Sem estorno ainda.
