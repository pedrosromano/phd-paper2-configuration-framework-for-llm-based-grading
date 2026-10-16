# Revisão do Pedro (2026-10-16): análise e plano

> Fonte: `~/Desktop/artigo_2_access_2026-10-16.pdf` (51 anotações, extraídas com PyMuPDF; numeração #1–#51
> pela ordem do PDF). Branch `revisao-access`. Regras de escrita: CLAUDE.md §9.2.

## ★ ONDE ESTAMOS (2026-10-16, noite) — ler primeiro na próxima sessão

- **Feito:**
  - as duas passagens de implementação da revisão do Pedro (commits `9257d38` e `cae86c9`, branch
    `revisao-access`);
  - a **segunda passagem** de revisão ao artigo inteiro (secção 5 abaixo).
  - Todos os 51 comentários estão resolvidos (lista de verificação na secção 5).
- **PDF para leitura:** Google Drive do Pedro, "O meu disco" → `artigo_2_access_revisto3_2026-10-16.pdf`
  (15 páginas, com o guia novo). As versões anteriores (`..._revisto_...` e `..._revisto2_...`) ficam lá
  também. O PDF anotado do Pedro continua em `~/Desktop/artigo_2_access_2026-10-16.pdf` e **não pode ser
  apagado**.
- **Guia refeito (secção 6 abaixo):** independente do modelo, com dois testes de validação.
- **Próximo passo:** a leitura do Pedro sobre o guia novo.
- **Motores novos:**
  - `experiments/analysis/instruction.py` (RQ6);
  - `experiments/analysis/guide_eval.py` (Tabela 5, guia aplicado);
  - `experiments/analysis/make_datasets_table.py` (tabela de datasets);
  - `experiments/run/batch_runner.py` (Batch API OpenAI e Anthropic);
  - `experiments/configs/prompts_instruction.yaml`.
  - Store da experiência: `data/processed/runs/instruction.jsonl`. Contém 60 linhas do GLM no Mohler, de
    uma corrida abortada, que as análises excluem.
- **Regras técnicas a lembrar:**
  - Fallback do RQ1 em `phase5.apply_reasoning_fallback`. SD, zeros e variação a temperatura 0 usam só as
    notas do próprio modelo.
  - O estrito do GPT vem do main store (não foi repetido).
  - O GLM-5.1 do OpenRouter (`glm-5.1-or`) usa o estrito de junho da DeepInfra no PT-CS
    (`instruction.MAIN_MODEL`).
  - Sonnet: saída estruturada; Mohler limitado a 800 para o Sonnet e o GLM.
  - O OpenRouter limita contas novas a cerca de 20 pedidos por minuto.
- **Pendentes fora do artigo:**
  - Pedro deve **revogar as chaves** que passaram pelo chat (Anthropic, OpenAI, OpenRouter);
  - questão ética/RGPD (D6/B4), ainda adiada;
  - os custos a repor à empresa estão na memória do Claude, não no repo (OpenAI + DeepInfra ≈ €160,6 sem
    IVA).
- **Avisos de LaTeX conhecidos:** caixa a mais do template (9,3 pt) e da Fig. 5 (2,9 pt). O resto está
  limpo.

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
- **Fecho (2026-10-16, fim do dia):**
  - **GPT-5.1** (Batch API; RQ3 exame inteiro síncrono):
    - crédito parcial no código: PT-CS +0.076 e RIAYN +0.106, ambos com Holm; zeros 32%→20% e 17%→12%.
      **Reduz o colapso do GPT**, mas não o do Qwen.
    - No PT-CS, o GPT com crédito parcial passa o GPT com reasoning (0.706 contra 0.672, cerca de 1/20 do
      custo).
    - Respostas curtas: Mohler +0.030 (equivalente), resto equivalente ou não significativo.
    - RQ3: exame inteiro −0.138 (Holm); critério RIAYN +0.153 (Holm); critério PT-CS +0.002 (equivalente).
  - **GLM-5.1** (OpenRouter, Z.AI; conta nova limitada a cerca de 20 pedidos por minuto, por isso só no
    código):
    - o prompt estrito reproduz junho no RIAYN (0.726 nos dois; mesma nota em 77% das repetições);
    - crédito parcial: RIAYN +0.033 e PT-CS −0.016 (contra o estrito da DeepInfra), ambos não
      significativos;
    - 6 notas ilegíveis em 2 965, por defeito do servidor.
  - **Guia aplicado** (Tabela 5):
    - a receita (DeepSeek + crédito parcial) é 1.ª de 10 no PT-CS código e 2.ª de 10 no RIAYN, atrás do GLM
      com crédito parcial (0.760, cerca de 15× o custo);
    - no Mohler e no SemEval fica a ≤0.046 da melhor sem reasoning; no PT-CS curtas a 0.123 do Sonnet (43×);
    - face à baseline: +0.19 no RIAYN e +0.21 no PT-CS código.
  - **Custo total de todas as experiências, a preços normais: €158.7** (OpenAI 65.0, DeepInfra 56.6,
    Anthropic 33.7, OpenRouter 3.5).
  - **Texto atualizado:**
    - RQ3 com 3 modelos, RQ6 com 5 modelos, guia, Discussão, Conclusão e abstract (250 palavras);
    - Method: Sonnet, GLM pelo OpenRouter e Tabela 2 compactada.
    - Corrigida uma citação do Qwen que juntava duas justificações.
    - Restam caixas largas só do template e uma de 2,9 pt numa figura.
  - **Falta:** a leitura do Pedro (PDF no Google Drive) e a **revogação das chaves** que passaram pelo chat
    (Anthropic, OpenAI e OpenRouter).

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

---

## 5. Segunda passagem (2026-10-16, noite)

Leitura do artigo inteiro com os 51 comentários ao lado, verificação das regras do §9.2 e conferência de
todos os números contra os motores (`guide_eval`, `instruction`, `make_phase5_tables`,
`audit_pct_baselines`, `bloco_c`). As tabelas regeneradas ficaram iguais às do commit anterior.

**Erros encontrados e corrigidos:**
- **Temperatura do GPT-5.1 (erro factual).**
  - O Method dizia "All calls use temperature 0", mas o GPT-5.1 não aceita temperatura e o harness nunca a
    envia (`adapter_api._build_payload_msgs`), por isso corre com a amostragem de origem.
  - Correções:
    - o Method passa a dizer que só os modelos abertos e o Sonnet correm a temperatura 0;
    - "9 a 60% dos itens variam a temperatura 0" incluía o GPT; para os modelos abertos é **9 a 56%**
      (`audit_pct_baselines.temp0_variation` separa agora os dois grupos; o GPT dá 29–60%).
- **Guia:** dizia que pontuar critério a critério "nunca melhorou" a concordância. Melhorou no GPT-5.1 no
  RIAYN (+0.153, com Holm). Corrigido.
- **Introdução vs Tabela 5:** a introdução promete comparar o guia em concordância, consistência e custo,
  mas a Tabela 5 não tinha consistência.
  - Acrescentado à "Guide in Use":
    - o SD dentro do item é 0.011–0.029 (o Sonnet, o mais consistente, fica em 0.002–0.006);
    - zeros no código: 7% no RIAYN e 10% no PT-CS, contra 5% e 2% dos professores e até 49% do Qwen.
- **RQ6:**
  - o custo da instrução no código é de 53–60 tokens de entrada e 5–8% do custo (o texto dizia "60
    tokens, 5–12%");
  - a justificação só correu no Qwen3.5 e no DeepSeek (texto e nota da Tabela 1 corrigidos);
  - "only reasoning repaired" passa a "reasoning remained the most effective remedy", porque a
    justificação também reduziu para metade os zeros do Qwen.
- **RQ3:** a explicação "porque a resposta conjunta tem mais tokens de saída" não vale para o GPT (o custo
  extra é de entrada). Retirada.
- **Referência mal descrita:** Poličar et al. é a correção de trabalhos numa cadeira de bioinformática, não
  "course evaluations" (introdução e estado da arte).
- **Introdução:** retirado "each run under one prompt configuration" (afirmação não verificada sobre outros
  trabalhos, no tom crítico que o Pedro pediu para tirar, #10).

**Melhorias de coerência:**
- **Claude Sonnet 4.6** passa a aparecer:
  - na introdução e no início do Method ("five LLMs"), com o motivo no Method (testar a instrução num
    segundo modelo fechado);
  - no RQ4: sem reasoning, é o melhor no SemEval (0.634) e no PT-CS curtas (0.791), mas no código fica abaixo
    do GLM-5.1 a cerca de 4× o custo;
  - no fecho do RQ4.
  - Assim, a frase da Discussão sobre o Sonnet tem apoio nos Resultados.
- **Ligação que faltava, RQ4 → RQ6 → guia:** com crédito parcial, o DeepSeek-V4-Flash iguala o GLM-5.1 (o
  melhor sem reasoning no estrito) no código, com cerca de 1/10 do custo (PT-CS 0.674 vs 0.672; RIAYN 0.732
  vs 0.726). Está na RQ6, na Discussão, no guia e na Conclusão, e justifica o modelo da receita.
- **O guia nomeia o modelo:** "DeepSeek-V4-Flash" no fim do guia e da Conclusão, em vez de "an inexpensive
  model that grades soundly" (#48: o utilizador não deve ter de investigar).
- **"Guide in Use":** as comparações nos itens amostrados ficaram exatas:
  - no código, o melhor fica +0.04 e +0.07 acima, a 14× e 68× o custo;
  - nas respostas curtas, o melhor fica 0.06–0.12 acima, a 19–53× o custo.
- **Ameaças:**
  - a frase de contenção passou a ser exata: todas as escolhas do guia, exceto âmbito e conversa, têm
    apoio num dataset público;
  - **frase nova:** o guia foi avaliado nos mesmos datasets de onde saiu, por isso as posições na Tabela 5
    descrevem uma receita fixa nestes dados e podem mudar em dados novos. Um revisor ia levantar isto.
- **Resumo:**
  - âncora do QWK ("where 1 is perfect");
  - "ranked first and second of ten ... on code";
  - continua com 250 palavras.
- **Method:**
  - regras de aplicabilidade com a conversa;
  - frase do Sonnet (800 Mohler) e do GLM pelo OpenRouter (só código) na secção do harness;
  - escala do RIAYN (4 a 12);
  - custos ignoram também o desconto do batch.
- **Seleção do PT-CS (#25):** "whose grade the teachers changed from the platform's first suggestion" (sem
  "score"/total).
- **Estado da arte (#11, #12):** a subsecção "Rubrics and Reference Answers" ganhou a frase sobre respostas
  de referência (Mohler 2011 e SemEval-2013, verificada no PDF do Mohler).
- **Outros:**
  - RQ2/RQ3 remetem para o Method a explicação da ausência do GLM (#36, #37);
  - "collapse to zero" passa a "show the zero-collapse" (#46);
  - o SemEval fica só com a accuracy, sem a sensibilidade do corte (#39);
  - "not only … but" no RQ5 reescrito.

**Lista de verificação dos 51 comentários (estado depois da segunda passagem):**

| # | Onde | Estado |
|---|---|---|
| 1 | "extended reasoning" | ✅ não aparece em lado nenhum; "reasoning" definido na Intro, no Related Work e no RQ1 |
| 2 | escolha dos modelos; 2.º fechado | ✅ três critérios no §III-C; Claude Sonnet 4.6 na RQ6, no RQ4 e no guia |
| 3–4 | plataforma que propõe notas | ✅ fora da Intro |
| 5 | "rather than by model identity" | ✅ fora |
| 6 | PT-CS nosso e necessário | ✅ Intro e contribuição: novo, nosso, único com exames completos (âmbito e conversa) |
| 7 | secções em dois sítios | ✅ um só parágrafo |
| 8 | "overthinking" | ✅ explicado |
| 9–10 | crítica a outros trabalhos | ✅ neutro; retirado também "each run under one prompt configuration" |
| 11–12 | rubricas em geral | ✅ "Rubrics and Reference Answers", com respostas de referência |
| 13 | "usually QWK" | ✅ fora (a subsecção dos datasets saiu) |
| 14 | PT-CS no estado da arte | ✅ fora |
| 15–17 | tratamento de dados / taxa de parse | ✅ fora do estado da arte |
| 18 | abertura do Method | ✅ descrição simples do estudo |
| 19 | "stem" | ✅ fora |
| 20 | Tabela I | ✅ tabela compacta de datasets (Tabela 2), referida no texto |
| 21 | modelos por dimensão | ✅ coluna na Tabela 1 com notas |
| 22 | "affordable" | ✅ fora |
| 23 | prova de conceito da plataforma | ✅ |
| 24 | "two teachers set the final grade jointly" | ✅ |
| 25 | "AI-proposed total" | ✅ "changed from the platform's first suggestion" |
| 26 | comentários da plataforma | ✅ fora |
| 27 | cache / custo por chamada | ✅ fora |
| 28–29 | tamanhos complicados | ✅ "every model grades every answer five times"; tamanhos na Tabela 2 |
| 30 | IC incompreensível | ✅ linguagem simples |
| 31 | overflow no Method | ✅ passou para o RQ1 |
| 32 | abertura dos Resultados | ✅ sem disclaimer |
| 33 | exclusão tendenciosa | ✅ sem exclusões (fallback) |
| 34 | "adds little" pouco claro | ✅ abertura "left agreement almost where it was" + painel custo-benefício |
| 35 | escala 0–1 | ✅ Figs. 1–3 e 6 |
| 36–37 | GPT/GLM ausentes | ✅ GPT no RQ2/RQ3; ausência do GLM explicada no Method e referida no RQ2/RQ3 |
| 38 | Fig. 4 → RQ1 | ✅ Fig. 1(a) |
| 39 | SemEval confuso | ✅ só accuracy, em linguagem simples |
| 40 | custos "historieta" | ✅ uma frase (€158.7) |
| 41 | "deployment provides" | ✅ "only PT-CS provides" |
| 42–43 | RQ6 transfer / Fig. 7 | ✅ fora; RQ6 é a instrução |
| 44 | "significantly" vs "rarely" | ✅ "only six of twenty" |
| 45 | consistência no RQ1 | ✅ SD sem/com reasoning, painel (c) |
| 46 | "collapsed" | ✅ "show(ed) the zero-collapse" |
| 47 | experiência para resolver o colapso | ✅ RQ6 (crédito parcial; justificação) |
| 48–49 | "modelo mais forte que não colapsa" / "verificar o colapso" | ✅ fora; a receita nomeia o modelo |
| 50 | guia condicional demais | ✅ uma receita + "The Guide in Use" (Tabela 5) |
| 51 | demasiadas configurações | ✅ sem escada de orçamentos |

**Pendentes (fora desta passagem):**
- a frase de disponibilidade dos dados do PT-CS, ligada à questão ética/RGPD (D6/B4, adiada pelo Pedro);
- a revogação das chaves que passaram pelo chat (Anthropic, OpenAI, OpenRouter).

---

## 6. O guia refeito: independente do modelo, com validação (2026-10-16, noite)

**Pedido do Pedro:**
- o guia é a parte mais importante: limpo e claro, sem disclaimers nem historietas;
- testes claros e validados;
- independente do modelo, sem aconselhar logo o DeepSeek;
- comparação completa, simples para humanos;
- rever várias vezes até ter qualidade de revista Q1.

**O guia (Tabela 4 e Fig. 7):**
- dar a rubrica ou a resposta de referência;
- pedir crédito parcial;
- reasoning desligado;
- uma pergunta por chamada;
- uma nota holística;
- conversa limpa por resposta.

Não indica modelo, não tem condições e não tem pré-testes.

**Validação** (motor `experiments/analysis/guide_eval.py`, sobre TODAS as configurações corridas, incluindo
sem guia, exame inteiro, critério a critério, justificação e conversa partilhada):
- **Teste 1, dentro de cada modelo (Tabela 4).**
  - Como funciona: o guia é comparado com cada outra configuração do mesmo modelo, nas mesmas respostas, por
    bootstrap emparelhado a 95% e sem correção (o que favorece a alternativa).
  - Sem reasoning, em 56 alternativas: 1 melhor (o Sonnet com a instrução estrita no PT-CS curtas, +0.043),
    22 sem diferença e 33 piores.
  - Sem guia, exame inteiro, critério a critério e conversa partilhada: nunca melhores.
  - Reasoning ligado: melhor em 7 de 17 (5 delas no Qwen) e nunca pior, mas menos consistente em 14 de 17 e
    a 2,6–179 vezes o custo.
- **Teste 2, entre modelos (Fig. 8).** Mostra custo contra concordância por dataset, com todas as
  configurações sem reasoning.
  - Com o modelo mais adequado a cada dataset, o guia:
    - é a melhor configuração do estudo no Mohler (GPT-5.1, 0.653) e no PT-CS código (DeepSeek, 0.674);
    - fica a 0.002 no SemEval, a 0.014 no RIAYN e a 0.043 no PT-CS curtas;
    - nas amostras com reasoning, fica a 0.053 no máximo.
  - Com quatro dos cinco modelos dá 0.65–0.76 no código; com o Qwen, 0.50 e 0.55 (o colapso persiste).
  - Com o modelo mais barato custa €0,02–0,09 por 1000 notas, e nenhuma configuração mais barata concorda
    melhor (só um empate de 0.001 no SemEval).

**Mudanças:**
- A antiga Tabela 5 (`tab_guide_use`) saiu.
- A Tabela 4 passou a ser gerada pelo `guide_eval`.
- Figura nova: `phase6.fig_guide_validation`.
- Atualizados o resumo, a Introdução, a Discussão, as Ameaças e a Conclusão.
- A palavra "recipe" saiu do artigo.

**Revisões da secção (4 passagens):**
- números verificados contra o motor;
- "significantly" nas afirmações;
- abertura do Teste 2 condicionada ao modelo adequado;
- o reasoning com o compromisso completo (melhor às vezes, menos consistente, mais caro);
- legenda da figura sem sobreposições.
