# Revisão do Pedro (2026-10-16): análise e plano

> Fonte: `~/Desktop/artigo_2_access_2026-10-16.pdf` (51 anotações, extraídas com PyMuPDF; numeração #1–#51
> pela ordem do PDF). Branch `revisao-access`. Regras de escrita: CLAUDE.md §9.2.

## 0. Estado (atualizado 2026-10-16, ~12h)

**Decisões do Pedro (resposta à análise):**
- **P1**: experiência da instrução aprovada, incluindo modelos que não colapsam, para mostrar que não estraga.
  Tira-se do guia a escada de orçamentos e o "confirmar localmente". **Sem teste extra ao guia**
  (leave-one-out rejeitado): o guia é uma receita boa e simples.
- **P2**: RQ1 sem exclusões (fallback para a nota sem reasoning). No fim, reanalisar o RQ1 inteiro à luz
  dos comentários.
- **P3**:
  - GPT-5.1 no RQ3: sim.
  - GLM: procurar outro fornecedor. Verificado: o GLM-5.1 sem reasoning já não existe (ver abaixo).
  - Sonnet 4.6: validar o custo e propor um subconjunto de cerca de $20.
- **P4**: retirar a RQ6 e **todo o ângulo "deployment/transfer"** do artigo (verificação global).
- **P5**: trabalhamos sempre pergunta a pergunta. "Total" era a soma dos critérios de uma pergunta e deixa
  de aparecer.
- **P6 (trabalho novo, muito importante, no fim)**: secção em que se aplica o guia nos datasets e se
  compara com as outras configurações nas métricas escolhidas ("é barato e bom", idealmente melhor que
  todas).

**Verificações feitas:**
- **GLM-5.1**:
  - a DeepInfra já não o lista; o `zai-org/GLM-5.1` é servido pelo GLM-5.3, que raciocina mesmo com
    `enable_thinking=false` (184–1763 tokens de saída, contra 10 em junho);
  - com `thinking: disabled` gasta 126–876 tokens de raciocínio;
  - OpenRouter: reasoning sempre ligado; Z.ai: modelo descontinuado.
  - O Qwen3.5 e o DeepSeek-V4-Flash reproduzem junho (mesmo modelo, 7 tokens, mesma nota em 5 de 6 itens).
- **Sonnet 4.6**, validado com os tokens reais do GPT-5.1 ($3/$15 por milhão, tokenizer +25%):
  - paridade total $155 ($77 com a Batch API);
  - subconjunto proposto: reasoning off em todos os itens, prompt atual + instrução do guia, $44 ($22 com
    batch);
  - falta a `ANTHROPIC_API_KEY`.
- **OpenAI**: conta sem crédito (`credit_balance_exhausted`). Bloqueia o GPT na experiência, no RQ3 e na
  avaliação final.
  - Antes, cada chamada era repetida durante 15 minutos.
  - Correção no harness: `NoCredits` salta o fornecedor e não grava nada, por isso uma retoma corre essas
    células depois.

**Experiência da instrução** (`instruction.jsonl`, motor `experiments/analysis/instruction.py`):
- **Fase 1, código, modelos abertos (13 320 notas, π=1, ≈€1,5):**
  - **Controlo de deriva OK**: o prompt atual repetido dá QWK a ±0.007 do original e a mesma nota em
    81–94% das repetições.
  - **DeepSeek, crédito parcial vs estrito**: PT-CS +0.070 [0.034, 0.111] e RIAYN +0.062 [0.021, 0.107],
    ambos significativos após Holm, sem custo extra e com SD baixo.
  - **DeepSeek, justificação**: no RIAYN +0.102 contra o estrito (p_holm 0.05); no PT-CS fica 0.068 abaixo
    do crédito parcial (significativo). É instável e aumenta o SD.
  - **Qwen**: crédito parcial +0.028 (PT-CS, não sobrevive ao Holm) e +0.010 no RIAYN (ns). Com
    justificação, PT-CS +0.053 (Holm sig) e zeros de 49% para 25%; RIAYN ns. **A instrução não repara o
    colapso**; o reasoning continua melhor no Qwen (PT-CS 0.612 contra 0.524).
  - **Contra o reasoning** (mesmas amostras):
    - DeepSeek com crédito parcial bate o DeepSeek com reasoning (PT-CS 0.670 contra 0.555; RIAYN 0.732
      contra 0.702);
    - fica ao nível do GLM-5.1 off (0.676 / 0.726) com cerca de 1/10 do custo.
  - **Regra pré-declarada**: como reparação do colapso, nenhuma variante passa (Qwen não melhora de forma
    robusta; GPT pendente). O crédito parcial é um ganho significativo e gratuito no modelo que não colapsa
    e não baixa nada em lado nenhum. **Decisão do Pedro**: adotá-lo no guia com esta leitura honesta?
- **Fase 2, respostas curtas** (crédito parcial + estrito no mesmo lote, Qwen e DeepSeek; 63 140 notas,
  π=1, ≈€1,65), **concluída**. Crédito parcial contra estrito, em todos os itens:
  - Mohler: DeepSeek −0.001 (equivalente, TOST) e Qwen +0.013 (equivalente).
  - SemEval: DeepSeek −0.009 e Qwen −0.015, ambos equivalentes.
  - PT-CS curtas: −0.001 e −0.021, não significativos (N=84, IC largo).
  - Conclusão: **o crédito parcial não muda as respostas curtas e melhora o código do modelo que não
    colapsa**, por isso serve como instrução única do guia.
  - Controlo de deriva OK em todos os conjuntos (QWK a ±0.01, exceto DeepSeek PT-CS curtas +0.028 com
    N=84; mesma nota em 81–94% das repetições).
- **DeepSeek com crédito parcial frente ao GLM-5.1 off (todos os itens):**
  - PT-CS código 0.674 contra 0.672; RIAYN 0.732 contra 0.726; Mohler 0.618 contra 0.617; SemEval
    0.588 contra 0.621.
  - Custo: cerca de 1/10. **Candidato à receita do guia**, a confirmar depois do GPT com crédito parcial.
- **Pendente (OpenAI sem crédito)**: o GPT nas fases 1 e 2, o GPT no RQ3 (decomposição + exame inteiro) e
  a avaliação final do guia.
- **Respostas do Pedro (2026-10-16, tarde):**
  - "prompt engineering simples para melhorar a qualidade" (adotar o crédito parcial);
  - o GLM "tem de existir nalgum sítio" → existe no OpenRouter (13 fornecedores, reasoning não obrigatório);
    falta uma chave do OpenRouter;
  - "não podemos gastar tanto" → GPT por Batch API, sem repetir o prompt estrito (≈ €8);
  - deu uma string "M4GbrU2KdzRnHtW" sem explicar → **não usada, perguntado o que é**;
  - chave da Anthropic dada → no `.env`; **recomendar revogação depois**;
  - PT-CS → uma frase só sobre a seleção.
- **Claude Sonnet 4.6** (Batch API, saída estruturada que impõe o JSON só com a nota, Mohler limitado a
  800; 21 280 notas, 0 falhas, €16,87 ao preço do lote):
  - não colapsa (zeros no código 6–10%) e é o mais consistente (SD 0.002–0.006);
  - estrito: Mohler 0.583, SemEval 0.634 (o melhor), RIAYN 0.676, PT-CS código 0.620, PT-CS curtas 0.791
    (o melhor);
  - crédito parcial: +0.031 no PT-CS código (sig. a 95%, não com Holm), equivalente no Mohler, SemEval e
    RIAYN, −0.043 no PT-CS curtas (N=84, não com Holm).
- **Avaliação do guia** (`guide_eval.py`, base B = itens comuns a todas as configurações sem reasoning):
  - receita = DeepSeek + crédito parcial;
  - **1.ª de 8 no RIAYN (0.732) e no PT-CS código (0.674)**, a mais barata;
  - Mohler: 4.ª, a 0.013 do melhor (Qwen + crédito parcial);
  - SemEval: 7.ª, a 0.046 do Sonnet, que custa 53×;
  - PT-CS curtas: 5.ª, a 0.123 do Sonnet, que custa 43×.
  - Na base A (amostras com reasoning) a receita fica a 0.024–0.071 da melhor no código. Essa melhor custa
    41–68× mais.
  - Decisão pendente: modelo da receita (DeepSeek, ou esperar pelo GPT e pelo GLM com crédito parcial).

**Já feito no texto e no código (por commitar):**
- Introdução reescrita.
- Related Work reescrito (subsecção de rubricas geral, sem crítica, "overthinking" explicado, sem
  datasets).
- Method reescrito, com a tabela de datasets nova `tab_datasets` (gerada) no lugar da Tabela I.
- Regra de fallback em `phase5.apply_reasoning_fallback`:
  - aplicada em `load_main`;
  - os SD, os zeros e a variação a temperatura 0 excluem as notas de fallback.
- Figuras novas em escala 0–1: `fig_rq1` (níveis, ganho contra custo, consistência), `fig_rq2_guidance`,
  `fig_rq3_scope_decomp`.
- Legendas do RQ2/RQ3, "deployment" no RQ2/RQ5.
- **RQ1 na base nova**: 6 de 20 significativos, 3 após Holm (Qwen Mohler, Qwen RIAYN, GPT RIAYN). O
  SemEval do Qwen fica no limite (+0.061 [0.000, 0.123]).

---

## 1. Temas estruturais (precisam de decisão)

### E1. O guia e a experiência do zero-collapse (#47, #48, #49, #50, #51)

Pedro: o guia é condicional demais ("o modelo mais forte que não colapsa" obriga o utilizador a uma
pré-investigação; "verificar o colapso primeiro" rejeitado; escada de orçamentos com demasiadas opções).
Proposta dele: tentar resolver o zero-collapse com engenharia de prompt, para o guia dizer "usa esta
instrução/configuração".

**O que os dados já mostram (análise local, sem custo de API):**
- O prompt atual de código com rubrica diz "Grade strictly according to the following question-specific
  rubric. Award and deduct marks exactly as the rubric specifies" e pede só `{"score": n}`.
- Os zeros reagem à instrução e ao formato:
  - no RIAYN, acrescentar a rubrica "estrita" subiu os zeros do Qwen3.5 de 7% para 16% e os do GPT-5.1
    de 6% para 17% (professores 5%); no GPT a rubrica deixou de ajudar (−0.005);
  - no PT-CS código, pontuar critério a critério baixou os zeros do Qwen3.5 de 49% para 36%;
  - o reasoning baixou-os de 47% para 24% (nos 67 itens com as duas versões).
- Nos 148 itens em que o Qwen3.5 dá zero em pelo menos 3 de 5 repetições, os professores deram em média 38%
  da cotação, e 32% desses itens tiveram metade ou mais.
- Exemplo (`ptcs:sub_0157:96`): código Java que não compila, mas com a assinatura certa, `new Date()` e o
  ciclo pelos movimentos. Professores 2,75/4; Qwen3.5 sem reasoning 0 nas 5 repetições; com reasoning 1,5.
- Os modelos são mais severos do que os professores em todo o código: nota média 0.28–0.49 contra 0.55 no
  PT-CS, e 0.62–0.78 contra 0.81 no RIAYN.
- Nas respostas curtas do Mohler os modelos dão 9–15% de zeros, contra 1% dos professores. No SemEval dão
  menos zeros do que os professores (30–45% contra 59%), por isso uma instrução de crédito parcial pode
  piorar o SemEval e tem de ser testada lá antes de entrar no guia.

**Experiência proposta: "instrução de avaliação"** (pré-declarada; variantes e regra fixadas antes de correr):
- **V0**: o prompt atual, repetido no mesmo lote para controlar a deriva do servidor. Não há verificação de
  reprodução registada para o Qwen/DeepSeek entre junho e outubro.
- **V1, crédito parcial**: substitui a frase "strictly … exactly" por uma instrução para dar crédito a cada
  item da rubrica cumprido, mesmo que o código esteja incompleto, tenha erros ou não compile, e dar 0 só se
  nada for creditável. Saída igual, custo igual.
- **V2, V1 + justificação curta**: saída `{"justification": "<até duas frases>", "score": n}`. Cerca de 60
  tokens de saída, um "reasoning mínimo" a 5–10× os tokens, contra 100–900× do reasoning.
- **Modelos**:
  - Qwen3.5 e GPT-5.1, os dois que colapsam;
  - DeepSeek-V4-Flash como controlo, porque não colapsa;
  - o GLM-5.1 não pode correr sem reasoning (D10).
- **Fase 1, código**: PT-CS código (295) e RIAYN (149), k=5, reasoning off, uma pergunta por chamada,
  holístico, conversa limpa. Custo ≈ €10 (GPT ≈ €7, abertos < €1,5).
- **Regra de decisão**: uma variante entra no guia se subir significativamente o QWK nos modelos que colapsam
  (IC 95%, Holm dentro da família) sem baixar significativamente o do DeepSeek.
- **Fase 2, só se uma variante passar**: Mohler, SemEval e PT-CS respostas curtas, para o guia poder
  recomendar uma única instrução. Custo ≈ €12 com V1 ou ≈ €22 com V2, incluindo o V0 de controlo.
- **Medidas**: QWK contra os professores, taxa de zeros, nota média contra a dos professores, SD_k e custo.
- **Leitura de cada desfecho**:
  - Se resultar, o guia passa a ser uma receita única e o reasoning perde o único papel que tinha (reparar o
    colapso).
  - Se não resultar, também é um resultado: o colapso é do modelo e não da redação, e o guia nomeia os
    modelos a evitar no código.

**Reescrita do guia (independente da experiência):**
- Uma configuração recomendada, como receita, sem "verificar o colapso primeiro", sem escada de orçamentos e
  sem "confirmar localmente".
- A Tabela 5 (default contra a melhor configuração a posteriori) fica como prova.
- Opcional e grátis: validação deixando um dataset de fora. Escolhida a configuração sem reasoning com o
  melhor QWK médio nos outros quatro datasets, sai o GLM-5.1 sem reasoning em todas as cinco partições.
- A Fig. 8 perde o losango "model collapses to 0?".

### E2. RQ1: exclusão de itens, figuras e clareza (#33, #34, #35, #38, #44, #45)

- **#33, a exclusão dos itens com overflow é enviesável.** Tirámos os itens em que o reasoning do Qwen3.5
  passou os 32 768 tokens: 37% dos itens no Mohler e 52% no SemEval, e são os mais difíceis.
  - **Alternativa testada, sem exclusões**: quando o reasoning não devolve nota, a corrida usa a nota do
    mesmo modelo sem reasoning, que é o que um sistema real faria.
  - **Resultado**: 5 de 20 combinações significativas, 3 após Holm (antes eram 2).
  - Ganhos do Qwen3.5: Mohler +0.056 [+0.022, +0.090], PT-CS código +0.173 [+0.047, +0.305],
    PT-CS curtas +0.129 [+0.014, +0.269], RIAYN +0.218 [+0.109, +0.325]. O SemEval (+0.061 [0.000, +0.123])
    fica no limite. O GPT-5.1 no RIAYN não muda (+0.228). Sobrevivem ao Holm: Qwen Mohler, Qwen RIAYN e GPT
    RIAYN.
  - **Vantagens**:
    - acaba o conceito de "tractable items";
    - o RQ1 e o RQ4 passam a usar exatamente os mesmos itens (as amostras de reasoning);
    - o overflow torna-se um resultado sobre o custo do reasoning: o Qwen3.5 não devolveu nota em 13% das
      corridas do Mohler e em 17% das do SemEval.
  - Muda números no abstract, no RQ1, no RQ4 e na Tabela 5 (o melhor a posteriori no Mohler passa de 0.659
    para 0.642).
- **#34, #35 e #38, figuras.**
  - O problema: o eixo de cada figura de ΔQWK ajusta-se aos dados, por isso +0.07 no RQ1 parece tão grande
    como +0.30 no RQ2.
  - Proposta: uma linguagem visual única para RQ1–RQ3, com o QWK absoluto em escala 0–1 e uma seta de
    "sem → com" (sem reasoning → com reasoning; sem guia → com guia; baseline → alternativa).
  - A Fig. 4 passa para o RQ1, como o Pedro sugere.
  - Custo-benefício: um painel com o ganho de QWK contra o multiplicador de custo (eixo log), com a faixa
    ±0.05 sombreada.
- **#44**: na Discussão, "it raised agreement in only five of twenty …", para não parecer contraditório com
  "rarely paid".
- **#45**: a consistência no RQ1 passa a valores diretos (SD sem e com reasoning) e frases simples, em vez
  de "off minus on".

### E3. Cobertura de modelos (#2, #36, #37)

- **GPT-5.1 no RQ3** (exame inteiro em 88 exames; critério a critério no RIAYN e no PT-CS), ≈ €8–10. Com
  isto, o RQ2, o RQ3 e a experiência nova usam os mesmos três modelos.
- **GLM-5.1 ausente do RQ2, do RQ3 e da experiência nova.** A única razão verdadeira é o fornecedor ter
  deixado de servir o modo sem reasoning.
  - Proposta: uma frase neutra no Method. Não tira conclusões, mas toca na D10/D12, por isso precisa do ok
    do Pedro.
  - Alternativa não recomendada: API da Z.ai (conta nova, ≈ €25, outro backend).
- **Segundo modelo fechado (#2).**
  - O candidato seria o Claude Sonnet 4.6; o Gemini 3 Pro não desliga o reasoning. Cobertura completa
    ≈ €100 ou mais.
  - Não recomendado. Em vez disso, explicar a escolha no Method e limitar a afirmação ao GPT-5.1. Critérios
    da escolha:
    - um interruptor de reasoning limpo no mesmo modelo;
    - os principais modelos abertos de três fabricantes, com duas ordens de grandeza de preço;
    - um modelo fechado de referência, o mais barato com reasoning verdadeiramente desligável.

### E4. RQ6 (#42, #43) e o papel do PT-CS (#6)

- A RQ6 acrescenta pouco:
  - o PT-CS já entra em todas as RQ;
  - a correlação entre rankings de 8 configurações é fraca (ρ 0.64 e 0.21, nenhuma significativa);
  - a única consequência prática era "confirmar localmente", que o Pedro rejeitou no guia.
- Proposta: retirar a RQ6 e a Fig. 7. Um parágrafo na Discussão diz que cada efeito reapareceu no PT-CS: o
  guia ajudou tanto como nos dados públicos, os mesmos dois modelos colapsaram no código e o GLM-5.1 sem
  reasoning voltou a ser o melhor no código.
- O PT-CS ganha o papel pedido no #6: é nosso, novo, em português e o único com exames completos, o que
  permite estudar o âmbito, a conversa e a pontuação por critério com rubricas reais.
- A experiência E1 pode ocupar o lugar da RQ6: "How does the grading instruction affect agreement and cost?".
  Fica neutra, sem antecipar o colapso na Intro.
- Atenção: apresentar o PT-CS como contributo leva a perguntar se está disponível. É precisa uma frase de
  disponibilidade dos dados, ligada à questão ética (D6/B4, adiada).

### E5. Descrição do PT-CS (#23, #24, #25, #26)

- Aplicar as alterações pedidas: protótipo da plataforma deste projeto (#23), "two teachers set the final
  grade jointly" (#24), tirar a frase sobre os comentários da plataforma (#26).
- **#25 ("não há AI proposed total")**: se se tirar toda a menção às sugestões da plataforma, a regra de
  seleção (a nota final difere da soma das pontuações por critério) fica sem explicação, e a ameaça
  ratificada em D4 desaparece.
- Proposta mínima: "for each answer, an AI model in the platform suggests a score per rubric criterion, and
  two teachers set the final grade jointly; PT-CS keeps the 379 answers whose final grade differs from the
  sum of the suggested scores".
- Falta o Pedro confirmar o que a plataforma faz: sugere por critério, sem total?

---

## 2. Comentários locais (ação proposta; não precisam de decisão)

**Introdução**
- #1 "extended reasoning" → "reasoning" em todo o artigo; definir uma vez na Intro ("a mode in which the
  model writes out its thinking before giving the grade"). Atualizar também as RQ e o Related Work.
- #2 razão dos modelos → parágrafo no Method §III-C (ver E3).
- #3 e #4: tirar "on which an AI model proposes grades for teachers to review".
- #5: tirar "keyed by observable task and model behaviour rather than by model identity".
- #6: PT-CS como dataset nosso e novo, e o único que permite os estudos com exames completos (ver E4).
- #7: juntar num só sítio os dois parágrafos que falam das secções.

**Related Work**
- #8: explicar "overthinking" (modelos de reasoning que produzem raciocínios muito mais longos do que a
  tarefa precisa).
- #9 e #10: tirar o tom crítico ("only indirectly", "cannot separate reasoning from vendor"); descrever o
  trabalho do Cong de forma neutra e manter só a lacuna ("to our knowledge, no study …").
- #11 e #12: subsecção "Code Grading with Rubrics" → "Rubrics and Reference Answers", geral para os dois
  domínios. Junta a lição sobre o guia da subsecção A com Pathak, Havare e Garcia-Huertes.
- #13 "usually QWK" está errado (a Tabela I mostra várias métricas); corrigir.
- #14: tirar a frase do PT-CS; a subsecção D desaparece, os datasets passam para o Method.
- #15 e #16: o parágrafo do "data handling" sai (ver #17).
- #17: a frase sobre notas não interpretáveis já está no Method; sai do Related Work.
- #20: a Tabela I passa a uma tabela compacta de datasets no Method §III-B, com as colunas dataset, domínio
  e língua, respostas, nota humana, material de guia e melhor resultado publicado. Saem as linhas "other
  LLM-grading studies" e a legenda longa.

**Method**
- #18: abrir com uma descrição simples do estudo (o que fizemos) e depois o "como".
- #19 "question stem" → "question".
- #21: os modelos usados em cada dimensão passam para uma coluna da Tabela 2; a prosa fica numa frase.
- #22: tirar "keeps the number of runs affordable".
- #27: tirar a cache e a contagem de custo por chamada.
- #28 e #29: simplificar ("with reasoning off, every model grades every answer five times"); os tamanhos
  ficam na tabela de datasets.
- #30: reescrever a frase dos IC em linguagem simples.
- #31: os números do overflow passam para os Resultados (RQ1), ver E2.

**Results**
- #32: abrir com uma introdução curta, sem disclaimer.
- #39: SemEval com accuracy e AUROC passa a uma frase simples (só accuracy) ou vai para o Method; sai a
  sensibilidade do corte.
- #40: cortar a "lição operacional" de custos; fica uma frase com o custo total.
- #41: "which only the deployment provides" → "which only PT-CS provides".
- #43: a Fig. 7 sai com a RQ6 (E4).

**Discussion**
- #44: ver E2.
- #45: ver E2.
- #46 "collapsed" → "showed the zero-collapse".

---

## 3. Decisões pendentes (Pedro)

1. Experiência E1 (V0, V1 e V2; fase 1 ≈ €10, fase 2 ≈ €12–22)?
2. RQ1 sem exclusões (fallback para a nota sem reasoning) como base única do RQ1, do RQ4 e do guia?
3. GPT-5.1 no RQ3 (≈ €8–10)? Frase neutra sobre o GLM-5.1? Sem segundo modelo fechado?
4. Retirar a RQ6 e pôr a E1 no lugar dela?
5. Frase mínima sobre as sugestões da plataforma (E5) e frase de disponibilidade dos dados.

Custo novo total ≈ €30–40, quase todo OpenAI. Já gasto: €103,9; tetos de €150 por fornecedor.

## 4. Ordem de trabalho proposta

1. Implementar no harness as variantes de instrução (config, hash e matriz) e fazer o dry-run de custos.
2. Correr a fase 1 de forma sequencial, com o watchdog de custos. Em paralelo, fazer as correções locais
   (secção 2).
3. Ler a fase 1, aplicar a regra de decisão e correr a fase 2 se se justificar. Correr também o GPT-5.1 no
   RQ3.
4. Recalcular tudo na base sem exclusões: tabelas, figuras novas com escala 0–1 e auditorias.
5. Reescrever o RQ1, a secção nova, o guia, a Discussão, as Ameaças, o abstract e a Conclusão.
6. Atualizar o CLAUDE.md §1.2 e §11, compilar e pôr o PDF no Desktop.
