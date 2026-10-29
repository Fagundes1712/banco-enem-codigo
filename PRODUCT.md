# Produto

## O que é
Um banco de questões do ENEM para estudar sozinho no navegador, no computador ou no celular.

## Público
Estudantes que se preparam para o ENEM.

## Fluxos principais (implementados)
1. **Por conteúdo:** escolher área, depois matéria e tópico, e resolver as questões daquele tópico.
2. **Simulado aleatório:** escolher área e quantidade e resolver questões sorteadas, com cronômetro.
3. **Resultado:** acertos e nota pela mediana oficial do INEP para o mesmo número de acertos, 2022 a 2025 (`docs/dificuldade.md`) e correção questão a questão com o gabarito oficial.
4. **Histórico:** respostas ficam salvas só neste navegador (`localStorage`); sem ele o app funciona sem progresso.
5. **Planos:** no grátis o estudante vê só se acertou ou errou; as notas (simulado, área, matéria, tópico e blocos) são do plano Pro. Tocar onde ficaria a nota abre o convite com "Seja PRO" e "Continuar estudando". O plano vem da conta (`contaAtual`, API em `api/`); sem login, é o grátis.
6. **Offline:** o service worker guarda o app e o banco depois da primeira visita.

## Dados
- 1.850 questões das provas oficiais (aplicação regular, caderno azul), 8 anuladas.
- Classificação em 3 níveis: Área → Matéria → Tópico (`docs/TAXONOMIA.md`). 37 classificações marcadas para revisão.
- Parâmetros TRI oficiais e nível de dificuldade (Leve a Extremo) nas questões de 2022 a 2025; os anos anteriores entram quando houver os microdados.
- 26 questões aparecem como imagem da página oficial, porque o texto do PDF não conferia.

## Fora do escopo hoje
- Resoluções comentadas: o campo existe, mas está vazio. Não inventar conteúdo.
- Prova de 2020, provas PPL e reaplicação.
- Sincronização do histórico entre aparelhos (o login e a assinatura estão em construção em `api/`).
