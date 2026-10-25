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

- **Física, Eletrodinâmica × Circuitos Elétricos:** associação de resistores, série/paralelo, geradores, medidores e análise de circuito vão para Circuitos Elétricos. Corrente, Lei de Ohm num elemento, potência e consumo de aparelhos vão para Eletrodinâmica.
- **Física, Ondulatória × Fenômenos Ondulatórios × Acústica:** grandezas da onda e espectro vão para Ondulatória. Reflexão, refração, difração, interferência, ressonância e Doppler vão para Fenômenos Ondulatórios. Qualidades do som e instrumentos vão para Acústica.
- **Física, Termologia × Calorimetria × Transmissão de Calor × Termodinâmica:** temperatura e dilatação vão para Termologia; quantidade de calor e mudança de fase, Calorimetria; condução, convecção e irradiação, Transmissão de Calor; máquinas e leis, Termodinâmica.
- **Física, Dinâmica × Forças e Equilíbrio × Estática:** com aceleração, Dinâmica. Ponto material em repouso, Forças e Equilíbrio. Torque e alavancas, Estática.
- **Física, Tecnologia e Energia:** usinas, transmissão e eficiência energética de sistemas. Contas de consumo de um aparelho ficam em Eletrodinâmica.
- **Química, Química Orgânica × Funções Orgânicas × Reações Orgânicas:** reconhecer função ou nomenclatura vai para Funções Orgânicas; transformações, para Reações Orgânicas; cadeia, hibridização e propriedades gerais, para Química Orgânica.
- **Química, Ácidos e Bases × Equilíbrio Iônico × Funções Inorgânicas:** pH, Kps, hidrólise e tampão vão para Equilíbrio Iônico; teorias e neutralização, Ácidos e Bases; nomenclatura e propriedades de ácidos, bases, sais e óxidos, Funções Inorgânicas.
- **Química, Química Ambiental × Química Cotidiana × Química Industrial:** só quando nenhum tópico conceitual domina. Se a questão exige cálculo estequiométrico sobre poluição, vai para Estequiometria com tag Química Ambiental.
- **Biologia, Ecologia × Dinâmica Ecológica × Ciclos × Impactos × Conservação × Ecotoxicologia:** conceitos e cadeias alimentares, Ecologia; relações, sucessão e populações, Dinâmica Ecológica; ciclos de elementos, Ciclos Biogeoquímicos; poluição e desmatamento, Impactos Ambientais; proteção e manejo, Conservação Ambiental; acúmulo de tóxicos nos organismos, Ecotoxicologia.
- **Biologia, Fisiologia Humana × Homeostase:** funcionamento de sistemas, Fisiologia; regulação e feedback, Homeostase.
- **Biologia, Microbiologia × Parasitologia × Saúde Pública × Imunologia:** o organismo em si, Microbiologia; ciclo de parasitas e vetores, Parasitologia; prevenção coletiva e saneamento, Saúde Pública; resposta imune, vacinas e soros, Imunologia.
- **Matemática, Grandezas e Medidas × Aritmética:** conversões, escalas e proporcionalidade entre grandezas vão para Grandezas e Medidas; operações e frações sem grandeza física, Aritmética. Matemática Aplicada só quando nenhum tópico domina.
- **Matemática, Estatística × Funções:** ler gráfico de dados (barras, setores, linhas de séries) é Estatística; gráfico de uma lei de formação é Funções.
- **Geografia, Geografia do Brasil:** só quando nenhum tópico temático (clima, urbanização, agrária…) domina.
- **Geografia × Sociologia, Globalização:** fluxos, redes, blocos e território, Geografia; cultura, consumo e identidade, Sociologia.
- **Filosofia, períodos × temas:** se a questão pede o pensamento de um autor ou período, vai para o período (Antiga, Medieval, Moderna, Contemporânea). Se pede um conceito ético, político ou do conhecimento independente do autor, vai para o tema.
- **História:** os grandes tópicos são nomeados como `História Geral — …`, `História do Brasil — …` e `História da América — …`. O prefixo é parte do nome do tópico, não um nível.
- **Língua Portuguesa:** Interpretação e Compreensão de Textos é o tópico de leitura global. Quando a pergunta mira gênero, coesão, sentido de palavras, gramática, variação ou função da linguagem, vai para esse tópico específico. Charges e tirinhas cuja pergunta é o efeito de humor ou crítica ficam em Interpretação.
- **Literatura:** escola literária quando a pergunta exige reconhecê-la; Texto Literário e Gêneros Literários quando o foco é recurso expressivo ou gênero.
- **Línguas estrangeiras:** as cinco questões de inglês e as cinco de espanhol ficam nas matérias Língua Inglesa e Língua Espanhola, mesmo que o tema seja interpretação.

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
