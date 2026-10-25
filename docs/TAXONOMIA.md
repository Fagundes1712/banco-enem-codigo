# Taxonomia de conteúdos — 3 níveis

O app organiza as questões em exatamente três níveis:

1. **Área do conhecimento** (`areas`): Linguagens, Ciências Humanas, Ciências da Natureza e Matemática, cada uma com suas Tecnologias.
2. **Matéria** (`subjects`): componente curricular que pertence a uma única área.
3. **Grande tópico** (`topics`): pertence a uma única matéria e lista as questões direto, sem nenhum nível abaixo.

Não existe subtópico, conteúdo específico, subcategoria ou assunto subordinado ao grande tópico. Exemplos como "Lei de Ohm" ou "juros compostos" servem só para decidir em qual grande tópico a questão entra. Eles aparecem na descrição do tópico e nunca como navegação.

## Arquivos

| Arquivo | Papel |
| --- | --- |
| `tools/taxonomia.py` | Fonte da taxonomia. Edite aqui e rode `python3 tools/taxonomia.py`. |
| `taxonomy.json` | Gerado pelo script e carregado pelo app por `fetch` (nunca embutido no JS). |
| `tools/classificacao.json` | Classificação de cada questão: tópico principal, tags auxiliares e motivo de revisão. |
| `tools/aplicar_classificacao.py` | Grava `materia`, `topico`, `tags` e `revisao` em `questions.json` e valida a integridade. |

IDs seguem o caminho: área `CN`, matéria `CN.fis`, tópico `CN.fis.eletrodinamica`. O ID do tópico sempre começa pelo ID da matéria, e o da matéria pelo da área.

## Campos de classificação em `questions.json`

| Campo | Tipo | Regra |
| --- | --- | --- |
| `area` | `CN`, `MT`, `CH` ou `LC` | Área principal (vem da prova). |
| `materia` | ID de matéria | Precisa ser a matéria-mãe do `topico`. |
| `topico` | ID de tópico | Grande tópico principal. Uma questão tem exatamente um. |
| `tags` | ID[] | Tópicos auxiliares, para questões interdisciplinares. Não criam nível nem mudam a navegação. |
| `revisao` | string | Presente quando a classificação precisa de revisão humana, com o motivo. |

Integridade: o app só mostra uma questão numa tela de conteúdo se `topico` existe em `taxonomy.json` e `area`/`materia` batem com os pais do tópico. Questões inconsistentes continuam no simulado aleatório da área e aparecem na contagem "aguardando classificação". O teste `test/dom.test.cjs` falha se houver qualquer inconsistência no banco.

## Regras de classificação

A questão vai para o tópico do **conhecimento necessário para resolvê-la**, considerando enunciado, alternativas, textos, imagens, gráficos e tabelas. O tema do texto-base não decide sozinho: uma questão de Linguagens sobre um texto que fala de vacinas continua em Linguagens.

### Fronteiras entre tópicos parecidos

- **Física, Eletrostática e Eletrodinâmica × Circuitos Elétricos:** associação de resistores, série/paralelo, geradores, medidores e análise de circuito vão para Circuitos Elétricos. Carga, corrente, Lei de Ohm num elemento, potência e consumo de aparelhos vão para Eletrostática e Eletrodinâmica.
- **Física, Ondas e Fenômenos Ondulatórios × Acústica:** grandezas da onda, espectro, reflexão, refração, difração, interferência, ressonância e Doppler vão para Ondas; qualidades do som e instrumentos, Acústica.
- **Física, Termologia e Calorimetria × Termodinâmica e Transmissão de Calor:** temperatura, dilatação, quantidade de calor e mudança de fase ficam no primeiro; máquinas, leis, condução, convecção e irradiação, no segundo.
- **Física, Eletromagnetismo e Geração de Energia:** ímãs, indução, motores, usinas, transmissão e eficiência energética de sistemas. Contas de consumo de um aparelho ficam em Eletrostática e Eletrodinâmica.
- **Química, Química Orgânica e Isomeria × Reações Orgânicas, Polímeros e Biomoléculas:** reconhecer cadeia, função, nomenclatura ou isômero vai para o primeiro; transformações, polímeros e biomoléculas, para o segundo.
- **Química, Funções e Reações Inorgânicas × Equilíbrio Químico e Iônico:** pH, Kps, hidrólise e tampão vão para Equilíbrio; teorias ácido-base, neutralização, nomenclatura e tipos de reação, Funções e Reações Inorgânicas.
- **Química, Química Ambiental e Cotidiana:** só quando nenhum tópico conceitual domina. Se a questão exige cálculo estequiométrico sobre poluição, vai para Estequiometria e Gases com tag Química Ambiental e Cotidiana.
- **Biologia, Ecologia e Relações Ecológicas × Ciclos × Impactos Ambientais e Conservação × Ecotoxicologia:** conceitos, cadeias, relações, sucessão e populações, Ecologia; ciclos de elementos, Ciclos Biogeoquímicos; poluição, desmatamento, proteção e manejo, Impactos Ambientais e Conservação; acúmulo de tóxicos nos organismos, Ecotoxicologia.
- **Biologia, Microbiologia, Parasitologia e Saúde Pública × Imunologia:** o organismo, o ciclo do parasita e a prevenção coletiva ficam no primeiro; resposta imune, vacinas e soros, Imunologia.
- **Matemática, Grandezas e Medidas × Aritmética:** conversões, escalas e proporcionalidade entre grandezas vão para Grandezas e Medidas; operações e frações sem grandeza física, Aritmética.
- **Matemática, Estatística × Funções:** ler gráfico de dados (barras, setores, linhas de séries) é Estatística; gráfico de uma lei de formação é Funções.
- **Geografia × Sociologia, Globalização:** fluxos, redes, blocos e território, Globalização (Geografia); cultura, consumo e identidade, Cultura (Sociologia).
- **Filosofia, períodos × temas:** se a questão pede o pensamento de um autor ou período, vai para o período (Antiga, Medieval, Moderna, Contemporânea). Se pede um conceito ético, político ou do conhecimento independente do autor, vai para o tema.
- **História:** os grandes tópicos são nomeados como `História Geral — …` e `História do Brasil — …`; História da América é um tópico só. O prefixo é parte do nome do tópico, não um nível.
- **Língua Portuguesa:** Interpretação e Compreensão de Textos é o tópico de leitura global. Quando a pergunta mira gênero, coesão, gramática, sentido de palavras, variação ou função da linguagem, vai para esse tópico específico. Charges e tirinhas cuja pergunta é o efeito de humor ou crítica ficam em Interpretação.
- **Literatura:** período literário quando a pergunta exige reconhecê-lo; Texto Literário e Gêneros Literários quando o foco é recurso expressivo ou gênero.
- **Línguas estrangeiras:** as cinco questões de inglês e as cinco de espanhol de cada prova ficam em Leitura em Inglês e Leitura em Espanhol. Cada matéria tem um tópico só, então o app abre as questões direto, sem escolha de tema.

## Reagrupamento de 2026-10-25

A primeira versão tinha 190 tópicos, muitos com 0, 1 ou 2 questões, o que deixava o filtro sem peso. Os tópicos vazios saíram e os pequenos foram reunidos com vizinhos de conteúdo, ficando 117, todos com pelo menos 4 questões únicas. Nenhuma questão mudou de assunto: a classificação antiga foi traduzida para o tópico que a reuniu. Cada tópico novo guarda em `antes` os ids antigos que absorveu; o app usa isso para os blocos de "Suas respostas" salvos antes da mudança. O teste falha se algum tópico ficar vazio ou com menos de 4 questões.

### Casos de revisão

Uma questão recebe `revisao` quando:

- a classificação depende de figura, gráfico ou fórmula que não foi possível conferir pelo texto;
- dois tópicos são igualmente centrais (a questão recebe o principal e o outro como tag);
- a extração do texto da prova tem trechos ilegíveis.

## Tópicos acrescentados à lista do pedido

Além dos tópicos listados no pedido, a taxonomia traz alguns grandes tópicos para não deixar questões frequentes do ENEM sem lugar adequado. Todos estão em `tools/taxonomia.py` e podem ser removidos sem afetar o restante:

- Língua Portuguesa: Variação Linguística, Funções da Linguagem.
- Literatura, Línguas Estrangeiras, Artes, Educação Física e TIC: o pedido nomeia as matérias, mas não os tópicos; os tópicos dessas matérias foram propostos aqui.
- História: períodos dentro de História Geral, do Brasil e da América.
- Geografia: Meio Ambiente e Sustentabilidade.
- Filosofia: os tópicos por período e por tema.
- Sociologia: Teorias Sociológicas Clássicas, Indústria Cultural e Meios de Comunicação, Violência.
