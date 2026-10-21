# TestingStudio Web — CAD0001

Ferramenta educacional de auditoria com quatro sprints. O objeto ativo é o **arquivo completo original `cad0001_item_calculo.txt`**, lido da pasta do projeto. Seus defeitos são preservados para que a auditoria os revele.

## Executar

Com Python e as dependências instaladas, na pasta do projeto:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Acesse http://localhost:8501. As quatro sprints funcionam localmente sem API Key. O comentário opcional do Gemini requer uma chave do Google AI Studio. Erros temporários 500/502/503/504 têm até quatro tentativas; autenticação e cota recebem mensagens próprias. O comentário da IA não altera os resultados locais.

## O que a revisão corrigiu

O exemplo simplificado do manual contém uma guarda de negativos que não existe no original completo. O aplicativo usava esse exemplo e, por isso, suas métricas não representavam o arquivo enviado. Agora todas as sprints usam um modelo explícito da função original, com nome do arquivo, SHA-256 e origem da evidência nos relatórios.

O original converte NULL em zero e calcula com negativos. Pela regra do manual, negativos devem retornar -1 e NULL pertence à classe inválida. O projeto adota -1 também para rejeitar NULL, como critério explícito: o manual não estabelece literalmente esse retorno para NULL. O esperado é mantido separado do comportamento implementado.

`codigo_fonte.txt` é mantido apenas como referência histórica do exemplo simplificado do manual; não é carregado nem executado pela aplicação. O fonte ativo é `cad0001_item_calculo.txt`.

## Sprint 1 — PCE e AVL

- Exibe o fonte completo, as classes de equivalência de cada parâmetro e os limites do tipo.
- Calcula ε pela escala declarada: DECIMAL(12,2) → ε = 10⁻² = 0,01.
- Mostra On 0,00, Off -0,01, Interior 100,00 e Exterior -100,00; acrescenta +0,01 como vizinho válido.
- Executa os **19 casos do modelo Python**, com **8 PASS e 11 FAIL**. Zero e +ε são isolados em cada parâmetro; NULL é uma classe separada.
- Exporta as evidências com a versão do objeto. A análise opcional Gemini é identificada como comentário textual, sem execução 4GL.

Exemplos: `(100,100,100)` retorna 10100 e passa; `(-0.01,100,100)` retorna 99 em vez de -1 e falha; `(NULL,100,100)` retorna 100 em vez da rejeição e falha. PASS significa atender ao esperado, inclusive ao rejeitar uma entrada inválida.

Os 19 casos não são a tabela anterior da imagem: os primeiros 13 preservam os cenários do catálogo local e há seis complementos de AVL. CT10 usa (-1,-1,-1), cujo resultado 0 é representável; três valores -0,01 exigiriam validar arredondamento no runtime.

## Sprint 2 — Caixa branca

Grafo da função `cad0001_calcula_valor`, com três decisões de NULL, 10 nós e 12 arestas:

`V(G) = E − N + 2 = 12 − 10 + 2 = P + 1 = 4`.

CT01, CT02, CT03 e CT04 formam quatro caminhos básicos independentes e cobrem todos os nós e arestas do modelo. Selecionar apenas CT01 reduz a cobertura. Remover um caso da seleção não apaga o catálogo: selecione novamente seu ID para executá-lo. Casos próprios podem ser adicionados e limpos na interface.

O original não tem OR de negativos nem retorno antecipado -1. Essas estruturas foram removidas do modelo. McCabe não prova ausência de defeitos e não determina universalmente o mínimo de testes para cobertura de arestas.

## Sprint 3 — DU e mutação

Há **13 pares DU factíveis**, obtidos pelos oito fluxos NULL/não NULL. Os parâmetros são definidos na entrada e redefinidos apenas nos ramos NULL; o cálculo usa a última definição e o retorno usa o resultado. O critério é todos os pares DU factíveis, não todos os caminhos DU.

Os dez mutantes agora alteram construções existentes no original: três operações aritméticas, três literais da normalização, uma remoção de termo, uma substituição de variável local, uma substituição de retorno e uma permutação equivalente. Não são gerados mutantes sobre uma guarda de negativos inexistente.

M09 é equivalente por comutatividade. Os quatro casos básicos cobrem os 13 pares e matam os nove mutantes não equivalentes: escore `mortos/(total−equivalentes) = 9/(10−1) = 100%`. Só CT01 cobre sete pares e mata cinco mutantes (55,6%). Sobreviver não comprova equivalência.

O oráculo de mutação compara o modelo original e suas variantes, no domínio Decimal Python. Essa comparação é separada do PASS/FAIL contra a regra funcional. As variantes não são compiladas em 4GL.

## Sprint 4 — RTM, validação e pitch

O plano completo tem **19 casos: 8 PASS, 11 FAIL, zero pendentes**. Os quatro requisitos têm testes executados e dois são aprovados no plano. A rejeição de negativos e a rejeição de NULL estão reprovadas, mesmo com 100% da cobertura estrutural, DU e mutação do catálogo.

A RTM registra origem do requisito, critério adotado, casos, resultados e versão do alvo. Vínculo não significa aprovação. Remover casos da execução os deixa pendentes; selecionar somente casos verdes não aprova o plano completo. A seleção pode reutilizar os casos da Sprint 2, inclusive personalizados.

Os CSVs, relatório final e roteiro do pitch refletem a seleção atual. O pitch explica os defeitos do original e os limites da evidência.

## Escopo e limites

- A execução é do **modelo Python instrumentado da função de cálculo**, não do fonte Informix-4GL. O grafo é explícito para essa versão; não há parser geral de 4GL.
- O SHA-256 identifica o conteúdo normalizado para quebras LF, permitindo checkout em Windows/Linux. Alterar o texto, inclusive comentários, bloqueia as evidências locais e métricas das quatro sprints. Use **Restaurar fonte do arquivo** para voltar ao conteúdo salvo; o Gemini pode analisar texto alterado, sem associá-lo às métricas antigas.
- Entradas têm até duas casas e magnitude máxima 9.999.999.999,99. Resultados que excedem o tipo ou exigem arredondamento são recusados pelo modelo, sem atribuição local de PASS/FAIL. É necessário validar esses casos no runtime nativo.
- Obter -1 não demonstra sozinho uma rejeição: `(-1×2)+1` também dá -1 por aritmética. Os representantes negativos do plano evitam essa coincidência.
- O original completo contém INSERT, UPDATE e DELETE em duas tabelas. Transações, COMMIT/ROLLBACK, restrições e menu não são executados nem estão incluídos nestas métricas; requerem testes de integração próprios.

Veja [a revisão e os critérios de QA](docs/REVISAO_QA.md).

## Testes automatizados da ferramenta

```powershell
python -m unittest -v test_caixa_preta test_caixa_branca test_sprint3 test_sprint4 test_interface
```

Os 28 testes automatizados verificam leitura e identidade do original, épsilon por escala, regressão de negativos/NULL, limites do modelo, caminhos independentes, pares DU, mutantes, RTM, pendências, exportações e interação da interface. As chamadas Gemini são simuladas.

Os testes automatizados da ferramenta devem passar enquanto ela evidencia FAIL nos casos do programa auditado. São verificações de objetivos diferentes.
