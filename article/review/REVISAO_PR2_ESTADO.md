# Revisão do Pedro, ronda 2 (2026-10-18): análise e plano

> Fonte: `~/Desktop/artigo_2_access_revisto3_2026-10-16.pdf`, com 48 anotações, todas destaques com comentário.
> Extraídas com PyMuPDF e numeradas #1–#48 pela ordem do PDF.
> **O PDF anotado não pode ser apagado nem substituído.**
> Branch `revisao-access`. Regras de escrita: CLAUDE.md §9.2. Ronda anterior: `REVISAO_PR_ESTADO.md`.
>
> Legenda:
> - **A**: automático, sem decisão do Pedro;
> - **D**: precisa de decisão do Pedro (ver secção 2);
> - **✅** feito, **⏳** a fazer, **⏸** à espera de decisão.

## ★ ONDE ESTAMOS (2026-10-18, fecho) — ler primeiro

- **Ronda fechada.** As 48 anotações estão tratadas e as decisões D1–D7 implementadas. A secção *Acknowledgment*
  tem a declaração de uso de IA, com a redação final do Pedro. Está commitado no branch `revisao-access`, sem
  push.
- **PDFs finais no Desktop (versão 6):**
  - `artigo_2_access_revisto6_2026-10-18.pdf`: limpa, 16 páginas;
  - `artigo_2_access_revisto6_alteracoes_2026-10-18.pdf`: assinalada contra o PDF anotado (commit `b45cffb`).
  - As versões 4 e 5 também lá estão (pode-se apagá-las se o Pedro quiser).
  - O PDF anotado `artigo_2_access_revisto3_2026-10-16.pdf` ficou intacto.
- **Declaração de IA (redação final do Pedro):** "During the preparation of this work, the authors used Claude
  Opus 5 (Anthropic) to help write the scripts that run the experiments and process the data for the tables and
  figures, and to help revise the text. The research questions, study design, interpretation of the results,
  discussion, and conclusions are the authors' own; the authors checked all results and take full
  responsibility for the content."
- **Pendentes fora do artigo:**
  - a revogação das chaves de API que passaram pelo chat;
  - a questão ética/RGPD (D6/B4);
  - o financiamento a agradecer, se houver (não foi indicado).

- **Versão 5 (2026-10-18, 18h20):**
  - D6 condensado;
  - secção nova *Acknowledgment* com a declaração de uso de IA que a IEEE exige. Redação suave, como o
    Pedro pediu, sem "Claude Code". Diz "help draft and revise the text", porque o assistente também redigiu
    texto; desenho, interpretação, discussão e conclusões são dos autores;
  - Fig. 1 ligeiramente mais baixa, para o texto da pág. 6 não invadir o rodapé.
  - No Desktop: `artigo_2_access_revisto5_2026-10-18.pdf` (limpa) e
    `artigo_2_access_revisto5_alteracoes_2026-10-18.pdf` (assinalada contra o PDF anotado). As versões 4
    também lá estão.
- **PDFs no Desktop (versão 4):**
  - `artigo_2_access_revisto4_2026-10-18.pdf`: versão limpa;
  - `artigo_2_access_revisto4_alteracoes_2026-10-18.pdf`: alterações assinaladas contra o PDF anotado (commit
    `b45cffb`). Azul sublinhado = novo, vermelho riscado = removido; Figs. 1 e 4 redesenhadas, Fig. 8 e Tabela 4
    novas. Como refazer: `article/review/tools/README.md`.
  - O PDF anotado (`artigo_2_access_revisto3_2026-10-16.pdf`) ficou intacto.
- **Motores e figuras mudados nesta ronda:**
  - `make_phase5_tables.write_guide_table`: Tabela 4 = o guia, com os números todos calculados;
  - `phase6.fig_guide_test1`: o Teste 1 em gráfico, Fig. 8;
  - `phase6.fig_rq1`: duas linhas;
  - `phase6.fig_rq4_cost` e `audit_pct_baselines.rq4`/`rq4_winners`: os cinco conjuntos;
  - o `guide_eval.write_table` foi removido.
- **Próximo passo:** a leitura do Pedro do PDF assinalado. Depois, commit, se ele o pedir.

---

## 1. Os 48 comentários

| # | Pág. | Onde | Comentário do Pedro (resumo) | Tipo | Ação | Estado |
|---|---|---|---|---|---|---|
| 1 | 1 | Abstract, "names no model" | forma mais académica? | A | "model-agnostic" (abstract, Intro, guia, Conclusão) | ✅ (também no guia) |
| 2 | 1 | Abstract, "outperformed by one of 56" | valorizar o guia ("melhor em 99% dos casos, X% mais barato"); o mesmo no resto do artigo | D5 | ✅ D5: 33 melhor / 22 sem diferença / 1 pior; abstract, Intro, Conclusão |
| 3 | 1 | Intro, "(Section II)" | utilidade? remover | A | remover | ✅ |
| 4 | 1 | Intro, "practical synthesis" | parece uma revisão da literatura | A | "What is missing is an empirical answer to the practitioner's question" | ✅ |
| 5 | 2 | Intro, "one closed (GPT-5.1) ... A second closed model, Claude Sonnet 4.6, joins" | não é *one closed*; o Sonnet junto do GPT | A | "three open-weight ... and two closed (GPT-5.1, Claude Sonnet 4.6)"; diz que o Sonnet corre sem reasoning | ✅ |
| 6 | 2 | Intro, "which names no model" | "model agnostic"? também no abstract | A | = #1 | ✅ |
| 7 | 3 | Related Work, rubricas mais claras → mais consistência [21] | já foi estudado? como nos distinguimos? | A | frase final curta com a diferença, depois de verificar o que [12] e [21] fizeram (pesquisa em curso) | ✅ fontes verificadas; frases corrigidas e 3 refs novas (ver D6/§3) |
| 8 | 3 | Related Work, κ 0.41 → 0.60–0.65 com rubrica [12] | afinal já foi estudado | A | = #7 | ✅ |
| 9 | 3 | Related Work, "These results motivate our comparison..." | a diferenciação não é clara; curta e clara | A | = #7 | ✅ |
| 10 | 3 | Tabela 1 | pôr no fundo da página | A | `[b]` | ✅ fundo da pág. 3 |
| 11 | 3 | Method, "five LLMs" | foram mesmo 5? | A | sim (Qwen3.5, DeepSeek-V4-Flash, GLM-5.1, GPT-5.1, Claude Sonnet 4.6); nomeá-los na primeira frase | ✅ |
| 12 | 3 | Method, "graded five times" | não é o k=5? definir uma variável | A | definir *k* (repetições, k = 5) na abertura e usá-lo; tirar o "K=5" dos níveis do QWK (legendas dizem só "QWK") para não confundir k com K | ✅ |
| 13 | 4 | Method, PT-CS "changed from the platform's first suggestion" | tirar; fica "PT-CS consists of 379 answers: 295 code ... from 97 exams"; confirmar que não há mais referências à plataforma sugerir notas | A + D2 | Method: frase do Pedro. **Há mais referências:** duas frases nas Ameaças e "teacher-validated" na Intro e no Method (2×). Ver D2 | ✅ D2: retirado de todo o artigo (Method e Ameaças) |
| 14 | 4 | Method, "strongest open models when the study began" | apoio científico para a escolha? | A (pesquisa) | pesquisa em curso: uso destas famílias na literatura de *grading* e rankings independentes de junho de 2026; mostrar a frase ao Pedro | ✅ D6: texto mostrado ao Pedro na resposta |
| 15 | 4 | Method, GLM pelo OpenRouter + reprodução 0.726 | não quero esta diferenciação; diz que foi tudo DeepInfra | D3 | **"tudo DeepInfra" não é verdade** (o crédito parcial do GLM correu no OpenRouter). Ver D3 | ✅ D3: texto 'DeepInfra' + nota de rodapé com a exceção |
| 16 | 4 | Method, "DeepInfra no longer offers GLM-5.1 with reasoning off" | irrelevante | A | remover | ✅ |
| 17 | 4 | Method, "The closed model is GPT-5.1" | também é o Sonnet | A | "The closed models are GPT-5.1 and Claude Sonnet 4.6" | ✅ |
| 18 | 4 | Method, "To test the instruction on a second closed model..." | devia estar com o de cima | A | = #17 | ✅ |
| 19 | 4 | Method, saída estruturada do Sonnet | relevância? | A | encurtar para uma oração. Fica porque é o que garante que o Sonnet corre mesmo "sem reasoning" (sem ela escreve uma análise antes da nota) | ✅ |
| 20 | 5 | Method, "Sonnet 800 of Mohler; GLM only the code sets" | porquê esta diferença? | A | dizer porquê: o Sonnet é o modelo mais caro e o Mohler o maior conjunto (2273); o GLM só no código, o domínio a que a instrução se dirige | ✅ Sonnet: o mais caro sem reasoning; GLM sem razão no Method (ver D1) |
| 21 | 5 | Method, "that contain a teacher-validated code answer" | não quero referência a isto | A | "that contain at least one of the 295 PT-CS code answers" | ✅ |
| 22 | 5 | Method, conversa "first 20 ... three times with GLM-5.1" | foi para poupar? não se percebe o que é completo e o que é subamostra | A | reescrever o parágrafo: o que é completo e o que é amostra, e porquê. Explicação ao Pedro na secção 3 | ✅ |
| 23 | 5 | Method, *clamp* e normalização | difícil de ler; "Mohler 5, SemEval 1..." o que é? | A | reescrever: cada nota é dividida pela cotação máxima da pergunta (5 pontos no Mohler, 1 no SemEval, ...) | ✅ |
| 24 | 5 | Method, estatística (Holm, TOST, Wilcoxon) | secção muito complexa | A | reescrever em frases curtas, uma ideia por frase | ✅ |
| 25 | 5 | RQ1, "those runs take its reasoning-off grade (Section III-E)" | o que significa? | A | explicar por extenso e tirar a referência | ✅ (e a legenda da Tabela 3, no gerador) |
| 26 | 6 | Fig. 1 | muito comprimida; duas linhas se houver espaço | A | (a) numa linha, (b) e (c) na segunda | ✅ |
| 27 | 7 | RQ2, "Section III-C explains why GLM-5.1 is not among them" | não faz sentido, explica logo | D3 | nomear os três modelos sem remeter para outra secção (ver D3) | ✅ três modelos, sem remissão |
| 28 | 8 | RQ4, "on the public datasets" | porque não em todos os datasets? | D7 | contas feitas (secção 2) | ✅ D7: RQ4 com os cinco conjuntos |
| 29 | 9 | RQ4, "(Section IV-A)" | confunde; é necessário? | A | remover | ✅ |
| 30 | 9 | RQ4, "(Section IV-A)" | novamente | A | remover | ✅ |
| 31 | 9 | RQ4, "All the experiments together cost €158.7" | parece o custo da subsecção | A | passar para o Method, junto da definição de custo | ✅ |
| 32 | 9 | RQ5, "80 complete code exams" | é uma subamostra? | A | sim: amostra aleatória das 181 provas do PT-CS com código. Dizê-lo no Method e no RQ5 | ✅ |
| 33 | 9 | RQ5, "(Wilcoxon p = .03)" | nunca usámos isto; relevante? | A | "a paired test of the per-answer differences, p = .03"; o Method explica numa frase | ✅ |
| 34 | 9 | "F. RQ6: Grading Instruction" | não devia ser uma RQ: surgiu como tentativa de reparar o zero-collapse | D1 | ✅ D1: 'Follow-Up: Asking for Partial Credit', 5 RQ |
| 35 | 10 | RQ6, exemplo da justificação do Qwen | parece que demos nota máxima a uma tontice | A | trocar por `ptcs:sub_0148:85` (secção 3) | ✅ |
| 36 | 10 | Discussão, "six questions" | ver se são sempre seis | A (depois de D1) | com D1 recomendado passam a "five questions and the follow-up" | ✅ 'five research questions and the follow-up experiment' |
| 37 | 11 | Discussão, "(Section IV-A)" | necessidade? | A | remover | ✅ |
| 38 | 11 | Discussão, "(Sections IV-A and IV-F)" | acabou de ser lido | A | remover | ✅ |
| 39 | 11 | Guia, primeiro parágrafo | não explica a necessidade do guia nem enquadra as métricas | D4 | ✅ D4 |
| 40 | 11 | Guia, "Two settings carry the gain" | qual ganho? isto é o guia, não discussão | D4 | ✅ D4 |
| 41 | 11 | Guia, parágrafo de resultados com referências | *dump* de resultados sem propósito; não gosto das referências a secções | D4 | ✅ D4 |
| 42 | 11 | "A. Validating the Guide" | aparece antes de o guia ser explicado; "introduz-se e valida-se só" | D4 | ✅ D4 |
| 43 | 11 | "two tests that use every configuration graded in the study" | o que significa? | D4 | dizer em palavras simples (secção 2) | ✅ D4 |
| 44 | 11 | "compares with the best configuration of any model, and at what cost" | ótima frase; meter no abstract? | D5 | sim (recomendado) | ✅ D5: no abstract e na Intro |
| 45 | 11 | "Test 1: the same model, configured otherwise" | confuso; primeiro os testes, depois os resultados, de preferência em duas subsecções | D4 | ✅ D4: B (testes) e C (resultados) |
| 46 | 11 | "33 ... significantly worse" | *worse* que quê? | D4 | "worse than the guide" na reescrita | ✅ D4: 'agreed significantly better ... than the alternative' |
| 47 | 11 | "Turning reasoning on was the only change..." | porque voltamos ao reasoning? o guia não tem reasoning | D4 | explicação na secção 2 (D4) | ✅ D4: parágrafo próprio sobre o reasoning |
| 48 | 12 | Tabela 4 | não é clara; não podia ser um gráfico? | D4 | ✅ D4: Teste 1 em gráfico (Fig. 8); Tabela 4 = o guia |

**Resumo:** 31 automáticos (#36 depende de D1) e 17 que dependem de 7 decisões (D1–D7).

---

## 2. Decisões (com recomendação e o que o Pedro decidiu)

### Decisões do Pedro (2026-10-18, noite) e o que foi feito

- **D1 ok.** A RQ6 passa a experiência de seguimento.
  - Intro: cinco RQ, mais uma frase sobre o seguimento.
  - Method: a Tabela 1 tem a nota "follow-up experiment".
  - Resultados: "F. Follow-Up: Asking for Partial Credit", que abre com o zero-collapse como motivação.
  - Discussão e Ameaças com a mesma designação.
- **D2: "retirar totalmente".** Saíram as duas frases das Ameaças (seleção e sugestão da IA). O Method fica com a
  frase do Pedro.
  - **Decisão do autor; contraria a regra B2 do CLAUDE.md §2.2**, que fica registada como substituída.
  - As 80 provas da conversa continuam descritas como sorteadas das 181 provas da coleção com código, porque
    é o facto.
- **D3: "quero a nota de foi tudo DeepInfra, decidiu a equipa".**
  - No texto principal os modelos abertos correm "via the DeepInfra inference API".
  - A nota de rodapé diz a única exceção (o GLM-5.1 com crédito parcial, servido pela Z.ai via OpenRouter) e
    que, como as corridas estritas deram a mesma concordância nos dois (0.726 no RIAYN), tratamos os dois
    fornecedores como um só backend.
  - Não se podia escrever que nada correu fora da DeepInfra: os registos das corridas dizem OpenRouter.
- **D4 ok.** A secção do guia foi reescrita:
  - introdução: porquê um guia, as três medidas e a regra;
  - A. o guia, com a Tabela 4 nova (o guia e a evidência de cada definição) e a Fig. 7;
  - B. os dois testes, explicados antes dos resultados;
  - C. os resultados: a Fig. 8 (Teste 1, gráfico novo) com um parágrafo próprio sobre o reasoning, e a Fig. 9
    (Teste 2).
- **D5: "muito confuso".**
  - Passou a contagem simples: "Against 56 alternatives without reasoning, the guide agreed significantly
    better with teachers in 33, showed no significant difference in 22, and agreed worse in only one".
  - A frase do #44 entrou no abstract ("validated twice: against every other configuration of the same model,
    and against the best configuration of any model, at what cost") e na Intro.
  - O abstract tem 250 palavras.
- **D6.** Primeiro o Pedro pediu "mostra o texto". Depois clarificou: a escolha deve apoiar-se nos estudos de
  correção de respostas de alunos, e não em benchmarks gerais, com os autores nomeados.
  - O parágrafo do Method foi reescrito assim. Quatro das cinco famílias têm registo na literatura de
    correção:
    - Jukiewicz: 18 modelos de Anthropic, DeepSeek, Google e OpenAI;
    - Cipriano et al.: o Claude 3.5 Sonnet foi o mais próximo dos humanos;
    - Moazzez et al.: o Claude foi o mais consistente;
    - Li et al.: o GPT-4o ficou em 1.º e o DeepSeek-V3 em 2.º;
    - Aminah et al.: o DeepSeek teve o menor erro no Mohler;
    - Jiang e Fowler: o Qwen 2.5 72B ficou ao nível do GPT-4o;
    - Havare et al.: um Qwen de 7B igualou um modelo três vezes maior;
    - Cisneros-González et al.: um dataset classificado por DeepSeek e Qwen;
    - Jayarao: o interruptor de raciocínio do Qwen.
  - **O GLM-5.1 não tem registo na correção.** Fica justificado só como o melhor modelo aberto em código (o
    Arena), porque o estudo corrige código.
  - Quatro referências novas: Cipriano, Li, Jiang e Fowler, Cisneros-González.
  - Todas as afirmações foram verificadas nos resumos.
  - **Depois o Pedro disse que estava longo demais ("quase uma revisão da literatura").** Ficou condensado em
    três frases:
    - "The model families follow prior studies of LLM grading of student answers, which evaluated Claude
      [Cipriano, Moazzez], GPT [Li, Jukiewicz], DeepSeek [Aminah, Li] and Qwen [Jiang, Havare] models as
      graders";
    - o GLM-5.1 entra como o modelo aberto mais forte em código [Arena];
    - o GPT-5.1 entra pelo preço e pelo reasoning que se desliga.
- **D7 ok.** O RQ4 usa os cinco conjuntos (auditoria `audit_pct_baselines.rq4`, Fig. 4 redesenhada).
  - Mudou: nas curtas sem reasoning, o GPT-5.1 (0.660) e o GLM-5.1 (0.656) empatam; no código, o melhor é o
    GPT-5.1 com reasoning (0.732, €27/mil), só 0.031 acima do GLM-5.1 sem reasoning a 34× o custo.
  - "The closed models did not repay their price on code" passou a "bought little for their price"
    (Discussão e Conclusão).
- **Correções que os motores obrigaram a fazer:**
  - **"0.10 to 0.34"** era um duplo arredondamento (0.0949–0.3350). Passa a "0.095 to 0.335" (abstract, RQ2,
    Discussão, Conclusão, Tabela 4).
  - **Custo do crédito parcial no código:** "5 to 8%" passa a "5 to 9%" (calculado agora no motor, um preço por
    modelo).
  - **Custo da guidance:** "1.2 to 1.8×" não tinha motor por trás. Agora é calculado em `write_guide_table` (dá
    1.23–1.84).

### D1. A instrução de crédito parcial: RQ própria ou experiência de seguimento? (#34, #36)

**Facto:** a experiência foi desenhada depois de encontrarmos o zero-collapse, para o tentar reparar. As
Ameaças já o dizem.

- **Opção A (recomendada).** Cinco RQ e uma experiência de seguimento.
  - **Intro:** a lista fica com cinco RQ, mais uma frase sem antecipar resultados: "A follow-up experiment,
    designed after the first results, varies how the model is told to apply the guidance."
  - **Resultados:** a subsecção passa a ser a última, com o título "Follow-Up: Asking for Partial Credit". Abre
    com o zero-collapse como motivação: "the reasoning and model comparisons revealed..." e a pergunta de
    seguimento.
  - **Method:** a Tabela 1 mantém a linha da instrução, com a nota "follow-up".
  - **Discussão:** "the five questions and the follow-up".
- **Opção B.** Manter a RQ6 como está.

**Porque recomendo A:** é mais honesto quanto à origem da experiência, liga-a ao zero-collapse (que é o
achado central) e deixa de parecer que estava planeada desde o início.

### D2. A seleção do PT-CS e as sugestões da plataforma (#13, #21)

**O que o Pedro pediu:** tirar toda a referência à plataforma sugerir notas.

**Factos verificados:**
- O PT-CS tem **181 provas com código e 1174 respostas**. As 379 respostas usadas para a concordância (de 97
  provas) são as que têm a nota final diferente da sugestão da plataforma.
- A sugestão da plataforma veio de um modelo de IA, por isso a nota de referência partiu de uma sugestão de
  IA que os professores alteraram.
- A subexperiência de conversa usa **80 provas sorteadas das 181**, e só 34 estão entre as 97. Se o artigo
  disser apenas "379 answers from 97 exams", a descrição das 80 provas fica errada.

**Opções:**
- **A (recomendada).**
  - O Method fica com a frase do Pedro, sem a plataforma.
  - As 80 provas da conversa são descritas como "drawn at random from all 181 PT-CS exams with code answers,
    since this sub-study needs no teacher grade".
  - As Ameaças guardam **uma** frase, num só sítio, que junta a seleção e a sugestão da IA. Exemplo: "The
    PT-CS answers are those whose grade the teachers changed from a suggestion made by the platform's AI
    model; they may differ from typical answers, and agreement could be inflated if that model resembled one
    we test."
- **B (o pedido literal).** Nenhuma referência em lado nenhum.
  - **Não recomendo.** Esconderia que a nota de referência partiu de uma sugestão de IA. Um revisor que o
    descobrisse leria isso como um problema de integridade (é uma regra não negociável do CLAUDE.md §2.2).
  - Além disso, deixaria incoerente a descrição das 80 provas.

### D3. O GLM-5.1 e os fornecedores (#15, #16, #27)

**Facto:** as corridas do GLM-5.1 com crédito parcial correram na Z.ai pelo OpenRouter. As restantes correram
na DeepInfra. **Escrever "tudo DeepInfra" seria falso**, e o Method tem de indicar o fornecedor (CLAUDE.md
§6.4).

**Opções:**
- **A (recomendada).**
  - Sai a história: "DeepInfra no longer offers..." e a frase de reprodução no corpo do texto.
  - Fica uma oração factual na lista de modelos: "GLM-5.1 ... served by DeepInfra and, in the
    grading-instruction comparison, by its developer through OpenRouter".
  - A verificação de reprodução (0.726 QWK no RIAYN nos dois fornecedores) passa para uma nota de rodapé,
    porque é o que permite comparar as duas corridas.
  - No RQ2/RQ3 nomeiam-se os três modelos, sem razão e sem referência a outra secção.
- **B.** Igual a A, sem a nota de rodapé.

### D4. A secção do guia (#39–#48)

**Estrutura proposta:**
- **Introdução (#39–#41):**
  - porque é precisa uma configuração: sete escolhas e três medidas (concordância com os professores,
    consistência entre repetições, custo por nota);
  - a regra usada para escolher cada definição: fica a que sobe a concordância; quando nenhuma alternativa a
    sobe de forma fiável, fica a mais barata e mais consistente;
  - sem *dump* de resultados e sem referências a secções.
- **A. The Guide (#42):**
  - a Tabela 4 passa a ser o próprio guia, com seis linhas: definição, o que fazer, porquê (uma linha de
    evidência, sem números em excesso) e custo;
  - mais a Fig. 7 (o diagrama).
- **B. How We Validated It (#43, #45):** os dois testes explicados em palavras simples.
  - Teste 1: o guia contra todas as outras maneiras de configurar o mesmo modelo, nas mesmas respostas.
  - Teste 2: o guia, com cada modelo, contra a melhor configuração de qualquer modelo, e a que custo.
  - Para cada teste: o que se compara e o que conta como melhor ou pior.
- **C. Validation Results (#46–#48):**
  - **Teste 1:** a Tabela 4 de validação sai e entra um **gráfico**. Para cada alternativa, uma barra
    horizontal divergente com quantas comparações foram piores que o guia (à esquerda), sem diferença e
    melhores (à direita), e o custo relativo ao lado.
  - **Teste 2:** a Fig. 8 atual.
- **#47, explicação do reasoning:** o reasoning ligado entra na validação porque "reasoning off" é uma das
  seis definições do guia e tem de ser justificada como as outras.
  - O resultado mostra o preço dessa escolha: foi a única alternativa que às vezes concordou melhor (7 de 17
    comparações, 5 delas no Qwen, que colapsa).
  - Custou 2,6 a 179 vezes mais por nota e foi menos consistente em 14 de 17.
  - Por isso o guia deixa-o desligado. O texto vai dizê-lo assim: como o compromisso que o guia aceita, e não
    como uma reabertura da decisão.

### D5. Como apresentar a validação (abstract, Intro, guia, Conclusão) (#2, #44)

**Correção ao pedido.** "Melhor que todas as outras em 99% dos casos, com custo X% inferior" não é exato.

Os números reais (motor `guide_eval`):
- **Sem reasoning, 56 alternativas:**
  - **o guia foi pelo menos tão bom em 55 (98%)**;
  - foi significativamente melhor em 33 (59%);
  - sem diferença em 22;
  - pior em 1 (o Sonnet estrito no PT-CS curtas, +0.043).
- **Custo:** o guia não é sempre o mais barato.
  - "Sem guia" custa 0,5–0,75× e o estrito 0,86–0,96×, mas concordam pior ou igual.
  - As alternativas que o bateram usaram quase todas reasoning (7 de 8), a 2,6–179× o custo por nota.

**Proposta para o fim do abstract (com a frase do #44):**
> "We condense the comparisons into a model-agnostic configuration guide and validate it twice: against
> every other configuration of the same model, and against the best configuration of any model, and at what
> cost. Without reasoning, the guide agreed with the teachers at least as well as 55 of the 56 alternatives,
> and significantly better than 33; the configurations that beat it mostly used reasoning, at 2.6 to 179
> times the cost per grade. With the best-suited model it came within 0.05 QWK of the best configuration on
> every dataset."

**Para manter as 250 palavras do abstract:** encurtar a parte dos resultados.

### D6. A escolha dos modelos (#14). Implementado; falta confirmar

**A frase antiga estava parcialmente errada.** "Among the strongest open models" é verdade para o GLM-5.1 e o
DeepSeek-V4-Flash, mas **não para o Qwen3.5-35B-A3B**, que fica a meio da tabela. Só o irmão maior
(397B) estava perto do topo.

**Rankings independentes** (verificados por mim nos arquivos do Wayback):
- **Artificial Analysis Intelligence Index v4.0**, 6 jun 2026. A página diz: "Kimi K2.6 and MiMo-V2.5-Pro are
  the highest intelligence open source models, followed by DeepSeek V4 Pro (Max) & GLM-5.1".
  - GLM-5.1: 51, 4.º entre os modelos abertos.
  - DeepSeek-V4-Flash: 47, cerca do 10.º.
  - Qwen3.5-35B-A3B: 37, muito abaixo.
- **Arena** (o antigo LMArena: votos humanos entre pares de respostas):
  - texto, 9 jun 2026: GLM-5.1 é o 1.º modelo aberto (14.º de 365 no total), o DeepSeek-V4-Flash o 13.º aberto
    e o Qwen3.5-35B-A3B o 44.º aberto;
  - código, 31 mai 2026: GLM-5.1 é o 1.º aberto (6.º de 81) e o Qwen3.5-35B-A3B o 28.º de 32 abertos.

**Literatura de *grading*** (rastreio do nosso `refs_merged.csv`, 49 estudos de 2025–26 com um modelo
aberto nomeado):
- Llama aparece em 26, DeepSeek em 16, Qwen em 12, Mistral em 12 e GLM em 2.
- Em 2026, Qwen, Llama e DeepSeek estão ao mesmo nível.
- Ou seja, há precedente de *grading* para o DeepSeek e o Qwen, mas não para o GLM.

**Texto implementado no Method (§III-C)**, sem afirmar o que as fontes não dizem:
- o GLM-5.1 era o 1.º modelo aberto no Arena (texto e código) e o 4.º no Artificial Analysis;
- o DeepSeek-V4-Flash estava entre os 15 primeiros nos dois;
- o Qwen3.5-35B-A3B é um MoE pequeno (3B ativos) da família cujo interruptor de raciocínio o Jayarao usou;
- os modelos DeepSeek e Qwen já foram avaliados como corretores em estudos recentes [Jukiewicz, Aminah,
  Chen, Havare].

Entraram duas entradas novas na bibliografia (Artificial Analysis e Arena, com os URLs do arquivo).

**#7–#9, Related Work (corrigido e implementado):**
- **[Pathak]:** dizíamos "κ ≈0.41 → 0.60–0.65 com rubrica específica" e "superam a rubrica genérica". O
  artigo dá:
  - sem rubrica, 0.43 (OOP) e 0.41 (DSA);
  - a melhor técnica específica, 0.60 e 0.65;
  - contra a rubrica genérica, só ganha no DSA.
  - Corrigido para "0.41–0.43 → 0.60–0.65 with the best question-specific rubric", sem a comparação com a
    genérica.
- **[Garcia-Huertes]:** dizíamos "rubricas mais explícitas aumentam a consistência". O estudo é um modelo
  (GPT-3.5), 18 relatórios e 10 corridas, com duas versões de rubrica e sem condição "sem rubrica". Corrigido
  para dizer exatamente isso.
- **[Seßler]:** dizíamos "given a rubric". O estudo usa "ten predefined criteria" para todos os modelos, sem
  contraste de rubrica. Corrigido. O resto confirma-se no PDF: os GPT fechados são mais consistentes e
  concordam melhor, e os professores são mais severos.
- **[Havare]:** "award partial credit … pooled over criteria" não se pode verificar. O resumo diz
  "micro-accuracy of 85%". Corrigido.
- **Resposta à pergunta do Pedro:** sim, o efeito da rubrica já foi estudado. Há três estudos que não
  citávamos:
  - Nugroho 2025: 10 LLMs, ensaios, com e sem rubrica;
  - Yoshida 2025: 4 LLMs, rubrica completa, simplificada ou nenhuma;
  - Venkatraman 2026: prompt "lenient" contra "strict" com 2 LLMs, em fichas de geografia. É o mais próximo da
    nossa experiência de crédito parcial.
  - Os três estão agora citados.
- **A diferença** é dita como a combinação, numa frase: guia e instrução num só protocolo, com cinco modelos
  abertos e fechados, quatro datasets de código e respostas curtas, cinco repetições por nota e custo
  registado. Não afirmamos ser os primeiros nem na rubrica nem na instrução.

### D7. RQ4 só com os datasets públicos? (#28)

**Porquê só públicos:** a razão era histórica. O PT-CS estava guardado para a análise de transferência, que
saiu na ronda anterior. Hoje não há razão de fundo para o deixar de fora.

**Contas** (os oito pares modelo × reasoning, nos itens que todos avaliaram; script
`scratchpad/rq4_all.py`, a passar para `audit_pct_baselines` se for adotado):

| | Só públicos (atual) | Com o PT-CS |
|---|---|---|
| Respostas curtas: amplitude | 0.071 | 0.112 |
| Melhor curtas sem reasoning | GLM-5.1 0.585 | GPT-5.1 0.660 ≈ GLM-5.1 0.656 |
| Código: amplitude | 0.259 | 0.239 |
| Melhor código | GLM-5.1 on 0.803 (€6.4) | GPT-5.1 on 0.732 (€27) > GLM-5.1 on 0.718 (€5.9) |
| Melhor código sem reasoning | GLM-5.1 0.726 | GLM-5.1 0.701 |

**Afirmações que mudariam:**
- "GLM-5.1 é o melhor sem reasoning nas duas tarefas" passa a "no código; nas curtas empata com o GPT-5.1";
- "no código o GPT-5.1 com reasoning fica abaixo do GLM-5.1 com reasoning" deixa de ser verdade;
- "neither closed model repaid its cost on code" mantém-se discutível: o GPT-5.1 com reasoning ganha 0.014 ao
  GLM-5.1 com reasoning a 4,7× o custo.

**Opções:**
- **A (recomendada).** Os cinco conjuntos, como na Fig. 1a e no Teste 2 do guia, com o texto do RQ4
  atualizado.
- **B.** Manter os públicos e dizer porquê numa oração. As amostras com reasoning do PT-CS são pequenas (67
  e 32), o que torna as médias por tarefa instáveis.

---

## 3. Verificações feitas (respostas a perguntas do Pedro)

- **#11, cinco modelos:** sim. Qwen3.5, DeepSeek-V4-Flash, GLM-5.1, GPT-5.1 e Claude Sonnet 4.6.
- **#13, outras referências à plataforma sugerir notas:**
  - `threats.tex`: duas frases (a seleção e a sugestão vinda de um modelo de IA);
  - "teacher-validated": `introduction.tex` (contribuição) e `method.tex` (dois sítios);
  - o resto do artigo não as tem.
- **#22 e #32, o que é completo e o que é amostra:**
  - **Completo, sem reasoning, 5 repetições:** todos os modelos em todos os conjuntos (Mohler 2273, SemEval
    800, RIAYN 149, PT-CS 295 + 84).
    - Exceções na experiência da instrução: o Sonnet só tem 800 do Mohler (custo) e o GLM só o código.
    - O SemEval já é uma amostra fixa de 800, porque o corpus original tem 16 003 respostas.
  - **Amostra:** o reasoning ligado (175 Mohler, 175 SemEval, todas as 149 do RIAYN, 67 PT-CS código e 32
    curtas), porque os raciocínios são longos e caros.
  - **Exame inteiro:** as 88 provas que contêm pelo menos uma das 295 respostas de código. É completo nesse
    universo.
  - **Conversa:** 80 provas sorteadas (semente fixa) das 181 provas do PT-CS com código, 5 vezes, com o Qwen e
    o DeepSeek. O GLM fez as primeiras 20 dessas provas, 3 vezes.
    - **Porquê:** era o desenho original (20 provas, k=3).
    - Quando a conversa foi alargada a 80 provas com k=5, o GLM já não estava disponível sem reasoning.
    - Não foi para poupar. No artigo fica sem a história (regra D12: sem distinção de períodos).
- **#35, exemplo novo:** `ptcs:sub_0148:85` (método `canMoveTo`).
  - O aluno escreve um método auxiliar que percorre os objetos do jogo e verifica se são atravessáveis; é uma
    solução razoável.
  - Professores: 1,2 em 2 (60%).
  - O Qwen dá 0 nas 5 repetições com sempre a mesma justificação: "The student correctly iterates through
    objects to check passability but fails to explicitly iterate through 'rogueObjects' and 'enemies' as
    required by the rubric...".
  - Mostra o colapso sem expor uma nota discutível dos professores.
- **#36, "six questions":** são as seis RQ. Passam a cinco se D1 = A.
- **#12, k e K:** o *k* das repetições e o *K* dos níveis do QWK coexistiam. O K sai das legendas e do
  Method; a sensibilidade passa a ser dita como "five or seven levels".

## 4. Ordem de trabalho

1. ✅ Extração e análise; este documento.
2. ✅ Passagem automática (itens A) e compilação. A D3 ficou implementada como opção A, à espera de
   confirmação.
3. ✅ Decisões D1–D7 implementadas (2026-10-18, noite).
4. ✅ Números verificados contra os motores; compilado (16 págs.); PDF limpo e PDF com alterações
   assinaladas no Desktop. Falta: o ok do Pedro ao texto do D6 e a leitura dele; commit quando pedir.