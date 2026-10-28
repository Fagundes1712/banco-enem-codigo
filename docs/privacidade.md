# Privacidade e LGPD

Levantamento técnico de 2026-10-28. Não é parecer jurídico; os pontos marcados como decisão são do responsável pelo projeto.

## Dados tratados
| Dado | Onde fica | Quem acessa | Finalidade |
|---|---|---|---|
| Respostas, simulados terminados e notas (`banco-enem:hist`, `banco-enem:blocos`) | `localStorage` do navegador do estudante | Só o próprio navegador; nada é enviado ao projeto | Mostrar o histórico e o progresso |
| Endereço IP e navegador de quem visita | Registros do GitHub Pages | GitHub (operador da hospedagem, nos EUA) | Entregar o site e segurança da hospedagem |
| Endereço IP e navegador ao baixar as fontes | Google Fonts (`fonts.googleapis.com`, `fonts.gstatic.com`) | Google (EUA) | Baixar as fontes Inter e Source Serif 4 |

O app não tem cadastro, cookies, analytics, anúncios nem formulário, e não coleta nome, e-mail ou documento. As respostas ficam no aparelho e não identificam a pessoa para o projeto.

## Pontos de atenção
- **Transferência para terceiros:** cada visita envia IP e user agent ao Google por causa das fontes. Hospedar as fontes junto com o app (licença OFL permite) elimina esse envio e simplifica a CSP. Mudança pequena e reversível, que altera arquivos do visual.
- **Menores de idade:** parte do público do ENEM tem menos de 18 anos. Como não há conta, perfil, publicidade nem coleta pelo projeto, a exposição à Lei 15.211/2025 (ECA Digital) é baixa, mas vale reavaliar se entrar login, analytics ou monitoramento de erros.
- **Monitoramento de erros (issue #2):** um serviço como o Sentry passaria a receber IP e dados técnicos do navegador. Antes de ligar: decidir a base legal, mascarar dados, citar o serviço numa política de privacidade e liberar o domínio na CSP.
- **Direitos do titular:** o projeto não guarda dados pessoais próprios; apagar os dados do site no navegador remove todo o histórico.

## Decisões pendentes do responsável
1. Publicar um aviso de privacidade curto (o que fica no aparelho, GitHub e Google como terceiros, contato). Texto final depende de revisão jurídica.
2. Hospedar as fontes localmente ou manter o Google Fonts.
3. Se entrarem contas, sincronização ou monitoramento, refazer este levantamento antes (skills `lgpd-*` instaladas no PC).
