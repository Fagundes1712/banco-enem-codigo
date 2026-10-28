# Operação

Ambientes, backup, restauração, monitoramento e incidentes. Deploy e rollback passo a passo ficam em `docs/fluxo.md`.

## Ambientes
| Ambiente | Onde | Dados |
|---|---|---|
| Local | `npm start` em `http://127.0.0.1:8765` | Os mesmos JSON do repositório; progresso no `localStorage` do navegador local. |
| Testes | `npm run verify` (local, hook e CI) | Banco real; `BANCO=<arquivo>` usa outro. |
| Homologação | Não existe. O PR é validado pelo CI e localmente. Um preview por PR exigiria outro repositório de Pages ou um serviço externo; não vale o custo de manutenção hoje. | — |
| Produção | `https://fagundes1712.github.io/banco-enem-app/` | Conteúdo de `site/public/` publicado pelo `deploy.yml`. |

Não há dados de clientes em servidor, então não há separação de dados de teste e produção a fazer.

## O que precisa de backup
| Dado | Onde vive | Cópias |
|---|---|---|
| Código, `questions.json`, `taxonomy.json`, `img/`, ferramentas | `Fagundes1712/banco-enem-codigo` | GitHub + a pasta de trabalho no PC; cada clone é um backup completo com histórico. |
| Site publicado | `Fagundes1712/banco-enem-app` | Reconstruível a partir de qualquer commit da `main` do código (Actions › Deploy). |
| Microdados do INEP e PDFs das provas | Só no PC (fora do Git, grandes demais) | Baixáveis de novo no portal do INEP. |
| `DEPLOY_KEY_SITE` | Actions secrets | Não precisa de backup: gera-se um par novo (`docs/security.md`). |
| Progresso dos estudantes | `localStorage` de cada navegador | Nenhuma. Limpar os dados do site apaga o histórico; não há exportação. |

RPO do código: o último push (o que só está na pasta local se perde junto com o PC). RTO do site: o tempo de um deploy manual, uns 5 minutos.

## Teste de restauração
Feito em 2026-10-28: `git clone https://github.com/Fagundes1712/banco-enem-codigo.git` numa pasta temporária vazia (28 s), `npm ci`, `npm run verify` com 169 checks passando, e o app servido dessa cópia completou home, simulado de 5 questões e resultado no navegador. Repetir quando mudar a estrutura do projeto:

```bash
git clone https://github.com/Fagundes1712/banco-enem-codigo.git /tmp/restore && cd /tmp/restore
npm ci && npm run verify && npm start
```

## Monitoramento
| O que | Como | Alerta |
|---|---|---|
| Testes e integridade do banco | CI em todo PR e push na `main` | E-mail do GitHub quando um workflow falha (padrão da conta). |
| Site no ar depois do deploy | `scripts/pos-deploy.cjs`: mesma `VERSION`, `index.html`, `questions.json` e `taxonomy.json` respondendo | Falha do workflow Deploy, pelo mesmo e-mail. |
| Disponibilidade contínua | Não monitorada. Status do GitHub Pages em https://www.githubstatus.com | — |
| Erros no navegador dos estudantes | Não coletados. Captura opcional está sendo preparada na issue #2, desligada até haver decisão de LGPD. | — |

## Incidente
1. Site fora ou quebrado: conferir https://www.githubstatus.com; se o problema for do último deploy, rollback pelo `docs/fluxo.md`.
2. Dado errado numa questão: corrigir no repositório por PR; o service worker troca o cache na próxima visita.
3. Segredo vazado: rotacionar `DEPLOY_KEY_SITE` (`docs/security.md`) antes de qualquer outra coisa.
4. Registrar o que houve e a correção na issue ou no PR.
