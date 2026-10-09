# TestingStudio Web — CAD0001

Aplicação da disciplina Teste de Software I com duas sprints implementadas:

- **Sprint 1 — Caixa-Preta:** relatório Gemini com PCE, AVL e divergência de NULL, além dos pontos de fronteira.
- **Sprint 2 — Caixa-Branca:** execução local de uma versão equivalente em Python, grafo, caminhos, McCabe e cobertura.

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

## Testes

```powershell
python -m unittest -v test_caixa_branca test_interface
```

Os testes verificam 125 combinações contra uma referência matemática, consistência dos caminhos, curto-circuito, independência dos caminhos básicos, cobertura completa, divergência de NULL, validação de entradas e interações da interface. As chamadas ao Gemini nos testes são simuladas.
