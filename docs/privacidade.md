# Privacidade e LGPD

Levantamento técnico de 2026-10-28. Não é parecer jurídico; os pontos marcados como decisão são do responsável pelo projeto.

## Dados tratados
| Dado | Onde fica | Quem acessa | Finalidade |
|---|---|---|---|
| Respostas, simulados terminados e notas (`banco-enem:hist`, `banco-enem:blocos`) | `localStorage` do navegador do estudante | Só o próprio navegador; nada é enviado ao projeto | Mostrar o histórico e o progresso |
| Endereço IP e navegador de quem visita | Registros do GitHub Pages | GitHub (operador da hospedagem, nos EUA) | Entregar o site e segurança da hospedagem |

O app não tem cadastro, cookies, analytics, anúncios nem formulário, e não coleta nome, e-mail ou documento. As respostas ficam no aparelho e não identificam a pessoa para o projeto.

## Pontos de atenção
- **Transferência para terceiros:** as fontes Inter e Source Serif 4 (licença OFL) são servidas pelo próprio site, em `fonts/`; nenhuma visita envia dados ao Google.
- **Menores de idade:** parte do público do ENEM tem menos de 18 anos. Como não há conta, perfil, publicidade nem coleta pelo projeto, a exposição à Lei 15.211/2025 (ECA Digital) é baixa, mas vale reavaliar se entrar login, analytics ou monitoramento de erros.
- **Monitoramento de erros (issue #2):** um serviço como o Sentry passaria a receber IP e dados técnicos do navegador. Antes de ligar: decidir a base legal, mascarar dados, citar o serviço numa política de privacidade e liberar o domínio na CSP.
- **Direitos do titular:** o projeto não guarda dados pessoais próprios; apagar os dados do site no navegador remove todo o histórico.

## Decisões pendentes do responsável
1. Publicar um aviso de privacidade curto (o que fica no aparelho, GitHub como terceiro, contato). Texto final depende de revisão jurídica.
2. Se entrarem contas, sincronização ou monitoramento, refazer este levantamento antes (skills `lgpd-*` instaladas no PC).
