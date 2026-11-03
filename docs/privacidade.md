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
- **Monitoramento de erros:** o Sentry (EUA) recebe, em HTTPS, a mensagem e a pilha dos erros do navegador, sem usuário, breadcrumbs nem PII (`docs/observabilidade.md`). O IP chega pela conexão, mas o projeto não o guarda ("Prevent Storing of IP Addresses" ligado); retenção de 90 dias.
- **Contas e Pix (API pronta, desligada):** quando `api-url` for preenchido, o projeto passa a guardar e-mail, hash da senha (bcrypt), aceite dos termos (versão e data), sessões e links de e-mail só como hash, e pagamentos (plano, valor, datas). Operadores: Neon (banco), Upstash (Redis), Resend (e-mail), AbacatePay (Pix), Cloudflare (Turnstile e proxy) e Google Cloud Run (`docs/backend-setup.md`). A exclusão de conta apaga tudo, menos o registro de pagamentos feitos, que fica sem e-mail nem senha pelo prazo fiscal (Art. 16, I). Com conta e assinatura, menores de idade passam a ser público direto: reavaliar o ECA Digital antes de ligar.
- **Direitos do titular:** o projeto não guarda dados pessoais próprios; apagar os dados do site no navegador remove todo o histórico.

## Decisões pendentes do responsável
1. Política de privacidade: rascunho v1.0 pronto com o responsável (controlador "Banco Enem", contato banco.enem.saas@gmail.com), cobrindo o site, o Sentry e as contas e o Pix. Falta revisão jurídica e decidir quando publicar; o responsável pediu para esperar o resto do produto.
2. Antes de ligar as contas: publicar a política e os termos de uso (a API já exige o aceite, versão `2026-10`) e revisar este levantamento.
