# Revisão de QA — 21/10/2026

## Fontes e decisão de escopo

A revisão confrontou os 13 materiais enviados da disciplina: Kickoff, manual Sprint 1, CAD0001 original, guia McCabe, estudo Grendene e aulas de 17/08, 19/08, 26/08, 09/09, 16/09, 30/09, 05/10 e 14/10.

O manual Sprint 1 (página 1, seção 1) exige ler `cad0001_item_calculo.txt`. Seu exemplo simplificado tem uma guarda para negativos ausente no arquivo completo. O starter embute esse exemplo em uma string, embora o objetivo exija a leitura do arquivo. Esta revisão adota o **original completo como objeto auditado** e as regras do manual como oráculo.

O arquivo original foi incluído integralmente, sem acrescentar validações. SHA-256 do conteúdo com quebras LF:

`ce12d94b9666f87e23fadd5218705e4c0146616f5eb831e6bf832bb3cd42f070`

## Achados e encaminhamento

| Achado | Correção na ferramenta |
|---|---|
| O alvo era o exemplo do manual, não o arquivo completo | Leitura do original, identidade visível, metadados nas exportações e bloqueio de métricas para outro texto |
| O original calcula com negativos | Modelo sem a guarda inventada; casos negativos falham contra a regra de retorno -1 |
| NULL é inválido no manual, mas convertido para zero no código | Divergência preservada; sentinela -1 para NULL identificada como critério adotado pelo projeto |
| Resposta livre de IA podia parecer execução | Tabela determinística local independente do Gemini; comentário de IA separado |
| Épsilon e gráfico eram constantes | Escala extraída das declarações DECIMAL da função; cálculo ε=10^-s e gráfico associado |
| Zero e +ε não estavam isolados em cada parâmetro | Inclusão de CT14–CT19 |
| GFC, DU e mutantes descreviam outra versão | Reconstrução para três IFs de NULL; V(G)=4, 13 pares DU e mutantes do original |
| RTM/pitch repetiam o resultado anterior | Plano com 19 casos, 8 PASS e 11 FAIL; rejeições de negativos e NULL reprovadas |
| Precisão do runtime não era simulada | Recusa explícita de resultados com frações de centavo ou estouro, sem classificá-los como PASS/FAIL local |

O catálogo atual contém 19 casos educacionais, não testes exaustivos. Quatro deles formam a base de caminhos. As contagens anteriores de 7 caminhos, 25 pares DU e 9 PASS/4 FAIL descreviam o exemplo simplificado e não se aplicam ao original.

A tabela anterior da imagem também tinha 13 casos, mas com entradas diferentes das do catálogo fixo. Para aqueles 13 casos da imagem, a previsão aritmética do original é 5 PASS/8 FAIL. Essa comparação histórica não deve ser apresentada como resultado do plano atual de 19 casos.

## Requisitos e critérios

- **REQ-CAD01:** fórmula `(P1 × P2) + P3` para parâmetros válidos; manual, seção 3.
- **REQ-CAD02:** zero válido; manual, seção 2 e On-point da tabela 1.
- **REQ-CAD03:** negativos rejeitados com -1; manual, Off-point e Exterior.
- **REQ-CAD04:** NULL é classe inválida; manual, seção 2. O código de rejeição -1 é uma convenção explícita deste projeto, pois não está literalmente definido para NULL no material.

Um caso inválido corretamente rejeitado deve passar. O arquivo auditado conter defeitos não é defeito da ferramenta; é necessário que ela os evidencie com o oráculo independente.

## Outras observações dos materiais

- Aulas de PCE/AVL e fundamentos: definir o esperado pela regra, isolar classes inválidas e investigar vizinhos da fronteira. Cobertura não prova ausência de defeitos.
- McCabe: medir o grafo declarado por função. V(G) é a dimensão da base de caminhos independentes; não é uma quantidade universal mínima para cobertura de ramos.
- DU: p-usos pertencem às arestas e c-usos aos nós; ligar cada uso à última definição em caminho sem redefinição intermediária.
- Mutação, aula de 30/09, páginas 14–15: no exemplo `maior(int a, int b)`, trocar `>` por `>=` é equivalente. Quando a=b, retornar a ou b dá o mesmo valor. Assim, os três mortos entre cinco mutantes, excluindo esse equivalente, dão 3/(5−1)=75%; a hipótese de zero equivalentes que produz 60% conflita com esse exemplo. Sobrevivência, por si, não prova equivalência.
- A nomenclatura LVR do projeto foi alinhada à substituição de variável local usada na aula; alterações de constantes são descritas como substituição de literal.
- RTM, aula de 14/10: rastreabilidade bidirecional liga requisito e teste, sem equivaler vínculo a aprovação.
- Unidade/integração e estudo Grendene: o cálculo isolado não comprova as operações do arquivo completo. Escala e esforço de um projeto não constituem percentuais de cobertura.

## Evidência e próximos testes de integração

Os números exibidos são da execução de um modelo Python explicitamente instrumentado, associado à versão do fonte. Não há compilação, execução Informix-4GL ou extração automática geral de GFC/DU de qualquer programa.

Para o CRUD, preparar ambiente e dados próprios e verificar: inclusão nas duas tabelas, alteração com recálculo, exclusão da dependente antes da principal, falhas em cada operação, rollback sem gravação parcial, consistência do relacionamento 1:1 e comportamento para registros não encontrados. Esses são cenários planejados por inspeção, não falhas de banco reproduzidas.

O contrato para arredondamento, estouro e conversão de entradas deve ser confirmado no ambiente Informix antes de ampliar o modelo. O menu chamado pelo fonte é dependência externa ao arquivo.
