# Revisão do orientador (Daniel Fernandes) e passagem para IEEE Access: estado e plano

> Documento de passagem (2026-10-15), para continuar depois da compactação de contexto. Branch `revisao-access`.
> Fonte da revisão: `~/Desktop/artigo_2_vDF.pdf` (79 anotações, 1 jul. 2026; extraídas com PyMuPDF, ver histórico).
> Regras de escrita: CLAUDE.md §9.2. Números: nunca escritos à mão; todos regeneram dos scripts listados no fim.

---

## 1. Decisões tomadas (todas ratificadas pelo Pedro em 2026-10-15)

| # | Decisão |
|---|---|
| D1 | Revista: **IEEE Access** (template `ieeeaccess` em `article/access-template/`, `article/latexmkrc`, fotos em `article/bios/`). Quartil aceite pelo Pedro. Sem financiamento. |
| D2 | **Não citar o Artigo 1** (não estará publicado). Removida a frase da SLR no Related Work. |
| D3 (B1) | Sem a palavra "framework" para o nosso entregável. Título: *Configuring LLM-Based Grading in Computer Science: An Empirical Study of Reasoning, Guidance, Scope, and Cost*. Entregável = **configuration guide**; secção "The Configuration Guide"; keyword "configuration guidelines". |
| D4 (B2) | **PT-CS = 379 respostas validadas por professores** (295 código, 84 respostas curtas, 97 exames), definidas uma vez pelo critério (a nota final difere do total proposto pela IA). Fora do artigo: export de 1184, estratos, tabela de estratos, "uneven reliability", "requalification", "PT-CS-verified", "university". Ameaças: começar pela contenção; manter só efeito de seleção, sem teto entre avaliadores, proposta inicial de IA. |
| D5 (B3) | **Uma pergunta por chamada** por defeito (exame inteiro nunca melhora e, a preços reais, custa 7% mais por pergunta). Fig. 9 e tabela do guia já atualizadas. |
| D6 (B4) | Ética/RGPD: adiado (Pedro: dados não identificativos). Lembrete: pseudonimizados continuam a ser dados pessoais no RGPD; o Access pode pedir declaração. |
| D7 | Bloco C aprovado (C1–C5, C7–C10); **C6 (modelo novo) não se justifica** (reavaliado no fim, Pedro concordou implicitamente; o estudo é "do seu tempo"). |
| D8 | Margem de equivalência **±0.05 QWK** fixada antes das corridas novas (TOST). |
| D9 | **Holm no RQ1**: os intervalos por combinação continuam a ser o resultado principal; tabela do RQ1 com coluna "Holm"; abstract: "in at most five of twenty combinations, two after correcting for multiple comparisons". |
| D10 | **GLM-5.1 fora das corridas novas** (a DeepInfra passou a servir GLM-5.3 com o reasoning impossível de desligar). As linhas do GLM de outubro foram **apagadas**. **Nenhuma conclusão do artigo sobre isto** (é coisa do fornecedor). Os dados do GLM de junho ficam (válidos). |
| D11 | **Conversa do GLM de junho fica no RQ5** (20 primeiros exames dos mesmos 80, k=3). Nunca deitar fora experiências completas. |
| D12 | **Nenhuma distinção no artigo entre corridas de junho e de outubro** (sem datas, sem "extensions", sem verificação de reprodução). Custos: total de todas as experiências; a história da estimativa usa "core experiment matrix". |
| D13 | **Regra do guia muda**: nas duas tarefas, *reasoning off com o modelo mais forte que não colapsa em zeros* (aqui GLM-5.1), em vez de "o mais barato" nas respostas curtas. Base: C10 (GLM off fica 0.02–0.08 abaixo do melhor; DeepSeek off 0.07–0.13). |
| D14 | Custos re-preçados aos preços reais faturados (pricing.yaml corrigido; `phase5.prepare` recalcula `cost_eur` a partir dos tokens; o valor antigo fica em `cost_eur_logged`). |
| D15 | Resultado novo aceite (Pedro "ok"): o GPT-5.1 sem reasoning também dá zeros a mais no código (32% PT-CS, 17% RIAYN vs 2% e 5% dos professores) e é o outro modelo em que o reasoning ajuda no código; reforça a regra "reasoning on se o modelo colapsa". |

---

## 2. Comentários do Daniel: estado

Todos tratados, exceto os marcados **PENDENTE**.

- p1: "Framework" (título) → D3 ✔ · abstract com "?" ✔ · "cell"→"combination" ✔ · "you use"→"should be used" ✔ · "space" ✔ · frase PT-CS na Intro → D4 ✔
- p2: framework ✔ · "large language models"→LLMs ✔ · "tríade" do Art. 1 → frase removida (D2) ✔ · itálicos (evaluation/assist) ✔ · "summative" ✔ · "above" → cita [7]–[9] ✔
- p3: falta o 3.º dataset (RIAYN) ✔ · ASAP definido ✔ · itálicos not/as graders ✔ · "We set out the configuration design space" ✔ · ordem natural/inversa explicada ✔ · **"só PT-CS limita a generalização"**: decomposição agora também no RIAYN ✔; âmbito continua só PT-CS (não há exames multi-pergunta públicos; Mohler original não tem ID de aluno) → **PENDENTE dizer nas Ameaças** · números sem vírgula ✔ · "gold" definido ✔
- p4: "1 a 12" explicado ✔ · números ✔ · "§" ✔ · notas de rodapé da Tabela de dimensões ✔ · MAE/BERT definidos (legenda da Tabela I) ✔ · "Qwen3-8B … roster" removido ✔ · κ_B → "κ (binned)" ✔ · referências dos modelos ✔ (bib: qwen_qwen35_2026, deepseek_v4_2026, glm5_2026, openai_gpt51_2025)
- p5: números ✔ · temperatura 0 justificada ✔ · "cells" ✔ · QWK sem re-expansão ✔ · corte 0.5 "otimista" → C8 no RQ4 ✔ · ROC definido ✔
- p6: p-values em itálico ✔ · legenda Fig. 1 no canto ✔ · valores verificáveis → `tab_rq1_values` ✔ (e figuras agora usam a mesma base que o texto) · "the plane omits" ✔ · painéis (a)(b)(c) ✔ · zero-collapse claro ✔ · títulos fora dos gráficos ✔
- p7: escala log justificada ✔ · "only" (Qwen) → agora 3 modelos ✔
- p8: N definido ✔ · "matrix" definido ✔ · GPT em amostras pequenas → agora cobertura total ✔ · como foi feita a estimativa ✔ · números ✔
- p9: eixo X da Fig. custo ✔ · painéis ✔ · "framework→system" → D3 ✔ · "across the exam" ✔ · natural/reversed ✔ · k=3 → k=5, 80 exames ✔ · legendas sem conclusões ✔ · "20 submissões indicador" → 80 exames ✔
- p10: Fig. 8 (a)(b) ✔ · "on/off" na legenda ✔ · "configuration" ✔
- p11: "the size of these exams" ✔ · FRAMEWORK ✔ · "model that discriminates" definido ✔ · parágrafo "Two design decisions" removido ✔
- p12: "(SECTION VI)" ✔ · "uma pergunta por call" → D5 ✔ · Ameaças PT-CS → D4 ✔
- p13: framework→system ✔

**PENDENTE (opcional)**: documento de resposta ao Daniel (como cada comentário foi tratado). Pode ser gerado a partir desta secção.

---

## 3. Experiências do bloco C (todas concluídas; 0 erros, 0 respostas por ler)

| | O quê | Resultado final |
|---|---|---|
| C1 | Guidance em Qwen + DeepSeek + GPT-5.1, 4 datasets | ajuda em **11/12** (todas sobrevivem a Holm), +0.095 a +0.256; exceção GPT RIAYN −0.005 |
| C2 | Decomposição (critério vs holística), Qwen + DeepSeek, RIAYN + PT-CS | nunca melhora: −0.072 (DeepSeek PT-CS, sig., sobrevive Holm) a +0.029; ~2× custo |
| C3 | Exame inteiro, 88 exames (295 perguntas PT-CS), Qwen + DeepSeek | Qwen **−0.091** [−0.13,−0.05] sig.; DeepSeek −0.024 n.s.; exame inteiro **7% mais caro**/pergunta |
| C4 | Conversa, 80 exames k=5 Qwen + DeepSeek (+GLM junho 20 exames k=3) | partilhada baixa nota 0.012 (Qwen p=.03), 0.010 (DeepSeek n.s.), 0.027 (GLM p=.003); ordem muda notas ~0.08–0.10; desvio médio em sentidos opostos (DeepSeek +0.013 p<.001, Qwen −0.015 p=.004) |
| C5 | GPT-5.1 cobertura total (off todos os itens, on amostras dos abertos, k=5) | off fica 2.º–3.º de 4 (1.º PT-CS curtas); reasoning só ajuda RIAYN +0.228 (sobrevive Holm); Mohler +0.006 equivalente a zero |
| C7 | Teto humano Mohler | professores entre si QWK 0.491; modelos vs média 0.61–0.66; vs prof. A 0.73–0.80; vs prof. B 0.33–0.41 |
| C8 | Corte SemEval | 0.5 fica no máx. 0.024 abaixo do melhor corte; acc 0.76–0.79, AUROC 0.83–0.85 |
| C9 | Holm + TOST | RQ1: 5/20 sig., **2/20** após Holm (Qwen RIAYN, GPT RIAYN); equivalência: GLM e GPT no Mohler (reasoning); RQ3 nenhum equivalente |
| C10 | Regret do guia (itens comuns = amostras de reasoning) | GLM off: Mohler 0.057, SemEval 0.021, PT-CS curtas 0.028, RIAYN 0.077, PT-CS código 0.000; DeepSeek off: 0.076/0.073/0.088/0.131/0.077 |

Outros números finais: RQ1 consistência piora em **17/20**; prémio de tokens **9–925×** (GPT curtas 9–31×, código 146–211×; Qwen 666–925×); RQ4 spread curtas **0.04**, código **0.26**; vencedores Mohler Qwen on 0.659, SemEval GLM off 0.621, RIAYN GLM on 0.803; RQ6 (8 configs) código **ρ=0.81 (p=.015)**, curtas **ρ=0.36 (p=.39)**, topo transfere; custos re-preçados: todas as experiências **€101.1** (OpenAI 50.4, DeepInfra 50.7), matriz principal **€59.8** vs estimativa **€16.7** (3.6×; OpenAI 1.9×, DeepInfra 4.4×); gasto real hoje ~€59 (DeepInfra $20.40 incl. $18.24 GLM-5.3 apagado; OpenAI €40.20).

Incidentes resolvidos (código já corrigido e com testes): parser com `[...]` e `{{...}}`; runners não morrem numa célula; ledger em journal com lock; RunStore com lock; monitor com barra global; watchdog de custos (`experiments/run/cost_watchdog.py`); figuras do RQ1 usavam base diferente do texto (corrigido via `rq1_cells`); RIAYN é só DSA (corrigido no Método e na Tabela I).

---

## 4. Estado da reescrita

**Feito** (commits no branch): template Access; título e nomes; PT-CS (Intro, Método, Ameaças parcial); Resultados RQ1–RQ6 reescritos; Método (dimensões, modelos, matriz, métricas: Holm, TOST, custo re-preçado; sem datas); Discussão; tabelas (`tab_rq1_values` com Holm, `tab_framework` derivada, `tab_guide_regret` nova, Tabela I); figuras (RQ1, RQ2 3 modelos, RQ3 2 modelos, RQ4 custo re-preçado, RQ5 painéis de efeito, RQ6 8 configs).

**Feito depois da compactação (2026-10-15):** 1. guia reescrito com D13 (linha nova "Choosing the model",
Tabela 5 `tab_guide_regret` com GLM-5.1 off e o modelo mais barato lado a lado, parágrafo C10); 2. RQ4 alinhado
(respostas curtas: "reasoning off é a escolha eficiente; o modelo pouco importa, 0.02"); 3. Ameaças (sem
"reference point"; âmbito e conversa só no PT-CS; temperatura 0 agora **9–60%**); 4. Conclusão reescrita
(quatro resultados + default do guia); 5. Abstract (249 palavras: 5/20 e 2 após Holm, 9–925×, 17/20,
guidance 11/12 em três famílias 0.10–0.26, exame inteiro e critério nunca melhoram, transferência,
default a ≤0.08 do melhor com até 30× menos custo); 6. Introdução (quatro famílias com toggle; GPT deixa de
ser "reference point"); 7. comentários de cabeçalho; 8. compilado (16 páginas; overfull só do template);
9. CLAUDE.md atualizado. Também: Discussão alinhada com D13; aberturas "RQ4 asks"/"The sixth research
question" reescritas (§9.2).

**Falta (opcional):** documento de resposta ao Daniel (a partir da secção 2); publicar como artifact.

---

## 5. Onde está cada coisa (regenerar sempre daqui)

- Tabelas: `python -m experiments.analysis.make_phase5_tables` (inclui `dim_contrasts`, `rq1_cells`, Holm, TOST, `tab_guide_regret`).
- Figuras: `eval "$(/usr/libexec/path_helper)"; .venv/bin/python -m experiments.figures.phase6`.
- Números do texto: `python -m experiments.analysis.audit_pct_baselines` (rq1–rq4, rq3_cost, zero_collapse, zero_rates, overflow, temp0_variation, cost_by_period, rq4_winners, rq6_transfer) e `python -m experiments.analysis.bloco_c` (C7–C10).
- Artigo: `make paper` (ou `cd article && latexmk -pdf main.tex`).
- Corridas: `experiments/run/bloco_c_run.py` (estado em `data/processed/runs/_bloco_c_status.json`), monitor `python -m experiments.run.monitor` (http://127.0.0.1:8765), vigilante de custos `experiments/run/cost_watchdog.py`.
- Preços: `experiments/configs/pricing.yaml` (preços reais faturados); faturação DeepInfra: `GET https://api.deepinfra.com/payment/usage?from=YYYY.MM`.
