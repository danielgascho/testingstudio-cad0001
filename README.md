# TestingStudio Web — CAD0001

Aplicação da disciplina Teste de Software I com quatro sprints implementadas:

- **Sprint 1 — Caixa-Preta:** relatório Gemini com PCE, AVL e divergência de NULL, além dos pontos de fronteira.
- **Sprint 2 — Caixa-Branca:** execução local de uma versão equivalente em Python, grafo, caminhos, McCabe e cobertura.
- **Sprint 3 — Fluxo de Dados e Mutação:** pares DU, sequência de definições/usos, dez mutantes e escore de mutação.
- **Sprint 4 — Pitch e Validação:** matriz RTM bidirecional, validação funcional, evidências e roteiro de apresentação.

## Executar

Na pasta do projeto, com Python e as dependências instaladas:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

A aba de Caixa-Branca funciona sem API Key. A Caixa-Preta precisa de uma chave do Google AI Studio. Erros temporários 500/502/503/504 têm até quatro tentativas com intervalos crescentes; autenticação e cota recebem mensagens próprias.

## Como demonstrar a Sprint 2

1. Abra **Sprint 2 · Caixa-Branca** com o fonte padrão.
2. Os sete casos básicos executam todos os nós e todas as arestas.
3. Selecione somente CT01 para observar a redução da cobertura.
4. Destaque CT05 no grafo: o primeiro negativo termina em RETURN -1, sem visitar N11 e N12.
5. Destaque CT02: NULL vira zero e o cálculo prossegue. A saída diverge do requisito, portanto o caso é FAIL, apesar de contribuir para a cobertura.
6. Adicione um caso próprio com números ou NULL e baixe o CSV dos resultados.

O grafo tem 17 nós, 22 arestas e 6 decisões binárias: `V(G) = 22 − 17 + 2 = 6 + 1 = 7`. Inclui os nós especiais de entrada e saída. O OR é representado com curto-circuito da esquerda para a direita, conforme o modelo Python. Se a condição composta fosse um único nó, a complexidade seria 5: as duas contagens correspondem a convenções diferentes de representação.

Os sete caminhos básicos são independentes, mas não representam todos os caminhos possíveis. McCabe não garante ausência de defeitos nem determina universalmente a quantidade mínima de testes para cobertura de arestas.

## Limites

A aplicação não executa nem compila 4GL. A execução instrumentada preserva a fórmula, a rejeição dos negativos e a conversão NULL→0 do CAD0001 padrão. As porcentagens medem esse modelo equivalente. Se o fonte editável mudar, a análise estrutural fica bloqueada para evitar associar um grafo antigo a código diferente.

Entradas usam Decimal, até duas casas decimais e o intervalo de DECIMAL(12,2). Não há simulação do overflow ou arredondamento do resultado no runtime 4GL. O oráculo do requisito rejeita NULL; o comportamento implementado o aceita como zero. 100% de cobertura pode coexistir com FAIL de requisito.

O relatório de Caixa-Preta é análise gerada pelo Gemini; seus resultados não são execução nativa de testes do CAD0001. Ele fica preservado na sessão ao interagir com a Sprint 2 e só é mostrado para o fonte correspondente.

## Como demonstrar a Sprint 3

1. Abra **Sprint 3 · Dados e Mutantes**. Por padrão, a análise reutiliza os casos selecionados na Sprint 2, incluindo os personalizados. Desmarque essa opção para montar uma seleção independente entre os 13 casos existentes.
2. Em **Definição–uso (DU)**, veja as definições, c-usos nos nós e p-usos nas arestas. Cada uso está ligado à última definição da variável, sem redefinição intermediária. Escolha um caso para acompanhar a sequência de eventos.
3. O universo contém 25 pares factíveis: as decisões dependem exclusivamente das classes NULL/negativo/não negativo, portanto as 27 combinações de representantes cobrem todos os fluxos possíveis. Os pares de uma atribuição de zero até o ramo verdadeiro de `< 0` são impossíveis e excluídos. O critério é todos os pares DU factíveis; não todos os caminhos DU.
4. Em **Mutantes e escore**, examine as dez alterações e as saídas de cada caso contra o original. Há três mutantes relacionais (ROR), dois aritméticos (AOR), um conector lógico (COR), dois literais (LVR), uma permutação equivalente e uma remoção de termo.
5. Os sete casos básicos cobrem os 25 pares e matam os nove mutantes não equivalentes. M09 apenas inverte os fatores da multiplicação e é equivalente por comutatividade no domínio deste modelo. O escore é `mortos / (total − equivalentes) × 100`.
6. Selecione somente CT01: cobre 13 pares DU, mata três mutantes e obtém escore 33,3%. Os demais sobreviventes não são automaticamente equivalentes. Adicione testes de zero, negativos e NULL e observe as mudanças.
7. Sem casos, a cobertura DU é zero, nove mutantes aparecem como não executados e o escore fica indefinido. Os CSVs permitem baixar cobertura DU, resumo de mutantes e matriz de resultados.

A mutação usa comparação de saídas com o comportamento original (incluindo NULL→0). Esse oráculo mede a sensibilidade dos casos às alterações, separadamente da conformidade com o requisito, exibida na Sprint 2. Um mutante pode produzir uma saída diferente e ser morto sem que o original cumpra a especificação. Sobrevivência sozinha não prova equivalência.

## Como demonstrar a Sprint 4

1. Abra **Sprint 4 · Pitch e Validação**. Por padrão, os 13 casos do plano são executados. É possível escolher um subconjunto ou reutilizar a seleção da Sprint 2 com casos próprios.
2. O resultado inicial é **9 PASS, 4 FAIL e nenhum caso pendente**. O CAD0001 é reprovado no plano por converter NULL em zero em vez de rejeitá-lo. A ferramenta está evidenciando uma falha do programa auditado.
3. Na **Matriz RTM**, confira quatro requisitos definidos para este projeto: cálculo, zero válido, rejeição dos negativos e rejeição de NULL. A tabela reversa mostra os requisitos associados a cada teste e seu tipo de fluxo (principal, alternativo/limite ou exceção).
4. Os quatro requisitos possuem testes executados, mas somente três são aprovados no plano. Requisito com caso FAIL é reprovado; com execução incompleta e sem FAIL fica parcial; sem caso executado fica sem execução. Ter um vínculo na matriz não significa aprovação.
5. Remova um caso e observe as pendências. Selecionar apenas os casos que passam não aprova o plano: os demais ficam explicitamente não executados. A aprovação de cada requisito exige que todos os seus casos planejados sejam executados e passem.
6. Baixe a RTM e as evidências em CSV e o relatório final em Markdown. Os números refletem a seleção atual, incluindo a cobertura estrutural, DU e mutação dessa mesma seleção.
7. Em **Pitch e demonstração**, use o roteiro de aproximadamente três minutos, com problema, solução, demonstração, resultados e limites. O roteiro também pode ser baixado em Markdown.

A RTM aplica ao CAD0001 os conceitos de derivação de casos e rastreabilidade da aula de 14/10/2026. Os identificadores REQ-CAD são uma organização das regras neste projeto. O plano é limitado aos casos cadastrados e não constitui teste exaustivo ou validação do runtime 4GL. A divergência de NULL permanece preservada; esta sprint documenta o resultado, sem alterar o programa objeto de estudo.

## Testes

```powershell
python -m unittest -v test_caixa_branca test_sprint3 test_sprint4 test_interface
```

Os testes verificam 125 combinações contra uma referência matemática, consistência dos caminhos, curto-circuito, independência dos caminhos básicos, cobertura completa, divergência de NULL, validação de entradas e interações da interface. As chamadas ao Gemini nos testes são simuladas.

Os testes da Sprint 3 também verificam o universo DU contra 216 combinações, as saídas conhecidas de cada mutante, o equivalente em 125 combinações (incluindo limites de entrada), o escore, suíte vazia e a seleção compartilhada/independente na interface.

Os testes da Sprint 4 verificam RTM nos dois sentidos, classificação dos fluxos, reprovação de NULL mesmo com cobertura alta, pendências, suíte vazia, casos próprios, relatórios, roteiro e interações da interface. A suíte completa tem 20 testes automatizados.
