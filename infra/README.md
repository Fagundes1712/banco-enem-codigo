# Servidor da Fase 1

Uma máquina grátis da Oracle (Arm, Ubuntu 24.04) com API, PostgreSQL e Redis em contêineres. Nada escuta para fora: o tráfego entra pelo Cloudflare Tunnel, que só faz conexões de dentro para fora. A Fase 2 usa `docs/backend-setup.md`.

| Peça | Exposição |
| --- | --- |
| `postgres`, `redis` | Rede interna sem saída para a internet, sem porta publicada |
| `api` | `127.0.0.1:8080`; recusa pedido sem o `X-Origem` da Cloudflare |
| `papeis`, `migracao` | Rodam e terminam antes da API a cada subida |
| `tunel` (fora do Compose) | Conexão de saída; leva `api.<domínio>` e `ssh.<domínio>` para localhost |

## Montar

1. No Cloudflare Zero Trust, crie um Tunnel e copie o token. Rotas: `api.<domínio>` para `http://localhost:8080` e `ssh.<domínio>` para `ssh://localhost:22`. Proteja `ssh.<domínio>` com uma regra do Access só para o seu e-mail.
2. Crie a regra de transformação que acrescenta `X-Origem` em todo pedido da API.
3. Na Oracle, crie a máquina Ubuntu 24.04 Arm numa rede **sem nenhuma regra de entrada**. Em "user data", cole `infra/cloud-init.yaml` com `__CHAVE_SSH__` e `__TUNNEL_TOKEN__` trocados.
4. Entre pelo Tunnel: `ssh -o ProxyCommand="cloudflared access ssh --hostname %h" deploy@ssh.<domínio>`.
5. Em `/opt/banco-enem/infra`: `cp .env.example .env`, `chmod 600 .env`, preencha e rode `docker compose up -d --build`.

Com token ou chave errados não há como entrar. Recrie a máquina: ela ainda não tem dados.

## Conferir

```bash
ss -tln                          # só endereços 127.x ou [::1], nada em 0.0.0.0
docker compose ps                # api e postgres healthy
docker run --rm alpine wget -T3 -qO- http://169.254.169.254/ ; echo $?   # diferente de 0: metadata bloqueado
curl -i https://api.<domínio>/saude                                      # 200, passando pelo Cloudflare
```

## O que roda sozinho

| Tarefa | Quando | Como |
| --- | --- | --- |
| Publicar | Até 5 minutos depois do CI verde na `main` | `api-producao.yml` move o branch `api-producao`; `atualiza.sh` busca e sobe |
| Voltar versão | Quando pedir | Actions > API em produção > Run workflow, com o commit anterior. Migração não volta sozinha |
| Backup | Todo dia, 03:30 UTC | `backup.sh`: `pg_dump` criptografado com `age` para o R2, guarda 30 dias |
| Teste de restauração | Toda semana | `restauracao.yml` restaura o último backup numa cópia descartável |
| Alertas | A cada 5 minutos | `alerta.sh`: e-mail com eventos graves da API; backup e atualização avisam se falharem |
| Sistema | Todo dia | `unattended-upgrades`, com reinício às 04:30 UTC se preciso |

Painel: crie no Cloudflare a rota `painel.<domínio>` para `http://localhost:8080` e um aplicativo do Access só para o seu e-mail, preencha `PAINEL_*` no `.env` e abra `https://painel.<domínio>/painel`.

Monitor de queda: cadastre `https://api.<domínio>/saude` num serviço externo gratuito (UptimeRobot, por exemplo), a cada 5 minutos.

Chave do backup: rode `age-keygen -o chave.txt` no seu PC. A linha pública vai em `BACKUP_CHAVE_PUBLICA`. Guarde `chave.txt` fora do servidor: sem ela, nenhum backup abre. Para o teste semanal, crie no GitHub os segredos `BACKUP_CHAVE_PRIVADA`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` e `R2_ENDPOINT`, e a variável `BACKUP_ATIVO=true`.

## Limitações

- O CI sobe a pilha e valida o formato do `cloud-init.yaml`, mas a instalação em si só roda na máquina real, sem teste automático.
- Imagens seguem as tags `postgres:17`, `redis:7-alpine` e `cloudflared:latest`, sem hash. Elas só mudam num `pull` feito de propósito.
- Máquina única e banco no mesmo disco: se o backup parar, perder a máquina é perder dados. Não receba pagamento real sem um teste de restauração verde.
- Alertas e backup avisam por e-mail, via Resend: se o Resend cair, o aviso fica só no `journalctl`.
- `atualiza.sh` não volta sozinho se a versão nova falhar: ele avisa, e a volta é manual.
