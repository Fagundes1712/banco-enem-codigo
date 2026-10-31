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

Para subir o servidor, carregue as variáveis do `.env` no terminal e rode `.venv/Scripts/uvicorn app.main:app --reload`.

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

## Limitações conhecidas

- Tabelas criadas com `create_all`; antes da primeira mudança de schema em produção, adotar Alembic.
- Só Pix. Parcelamento em 12x no cartão depende de confirmar o suporte na API da AbacatePay.
- Assinatura mensal por Pix não renova sozinha: o aluno paga de novo e os dias são somados.
- Sem estorno nem log de auditoria imutável ainda.
