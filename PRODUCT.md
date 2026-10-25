# Produto

## O que é
Um banco de questões do ENEM para estudar sozinho no navegador, no computador ou no celular.

## Público
Estudantes que se preparam para o ENEM.

## Fluxos principais (implementados)
1. **Por conteúdo:** escolher área, depois matéria e tópico, e resolver as questões daquele tópico.
2. **Simulado aleatório:** escolher área e quantidade e resolver questões sorteadas, com cronômetro.
3. **Resultado:** acertos, nota pela TRI do INEP (parâmetros oficiais quando o banco tem; `docs/dificuldade.md`) e correção questão a questão com o gabarito oficial.
4. **Histórico:** respostas ficam salvas só neste navegador (`localStorage`); sem ele o app funciona sem progresso.
5. **Offline:** o service worker guarda o app e o banco depois da primeira visita.

## Dados
- 1.850 questões das provas oficiais (aplicação regular, caderno azul), 8 anuladas.
- Classificação em 3 níveis: Área → Matéria → Tópico (`docs/TAXONOMIA.md`). 37 classificações marcadas para revisão.
- Parâmetros TRI oficiais e nível de dificuldade (Leve a Extremo) nas questões de 2022; os outros anos entram quando houver os microdados.
- 26 questões aparecem como imagem da página oficial, porque o texto do PDF não conferia.

## Fora do escopo hoje
- Resoluções comentadas: o campo existe, mas está vazio. Não inventar conteúdo.
- Prova de 2020, provas PPL e reaplicação.
- Contas, servidor ou sincronização entre aparelhos.
