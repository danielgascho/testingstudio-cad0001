import streamlit as st
import pandas as pd
import random
import time
from google import genai
from google.genai import errors
from sprint3 import DEFINICOES, C_USOS, P_USOS, UNIVERSO_DU, MUTANTES, analisar_du, analisar_mutacao
from caixa_branca import (
    NOS, ARESTAS, DECISOES, CASOS, Caso, executar,
    esperado_especificacao, cobertura, diagrama,
)


MODELO_GEMINI = 'gemini-3.8-flash'


def chave_preenchida(api_key):
    if not api_key:
        st.error('Insira sua API Key do Google AI Studio na barra lateral.')
        return False
    if any(caractere.isspace() for caractere in api_key):
        st.error('A chave contém espaços ou quebras de linha. Copie somente a chave completa do AI Studio.')
        return False
    return True


def criar_cliente(api_key):
    # A aplicação usa a Gemini Developer API, mesmo se o ambiente ativar Vertex AI.
    return genai.Client(
        api_key=api_key,
        vertexai=False,
        # As tentativas são controladas abaixo para mostrar o andamento na tela.
        http_options={'retry_options': {'attempts': 1}}
    )


def executar_com_tentativas(operacao):
    aviso = st.empty()
    try:
        for tentativa in range(4):
            try:
                return operacao()
            except errors.APIError as erro:
                if erro.code not in (500, 502, 503, 504) or tentativa == 3:
                    raise
                espera = 2 ** (tentativa + 1) + random.uniform(0, 1)
                aviso.warning(
                    f'O Gemini está temporariamente indisponível (HTTP {erro.code}). '
                    f'Nova tentativa {tentativa + 2}/4 em {espera:.0f} segundos...'
                )
                time.sleep(espera)
    finally:
        aviso.empty()


def exibir_erro_gemini(erro):
    if erro.code == 401:
        st.error('Falha de autenticação (401): o Google recusou a credencial enviada.')
        if 'ACCESS_TOKEN_TYPE_UNSUPPORTED' in str(erro):
            st.info(
                'O Google retornou ACCESS_TOKEN_TYPE_UNSUPPORTED. '
                'Chaves com prefixo AQ. são aceitas pelo Gemini; o prefixo sozinho não indica erro. '
                'Crie uma nova chave no Google AI Studio, copie o valor completo '
                'e tente novamente em “Testar conexão”. Se persistir, confira a chave '
                'e o projeto no AI Studio e encaminhe o código do erro ao suporte do Google.'
            )
        else:
            st.info('Confira se a chave está ativa no Google AI Studio e copie seu valor completo novamente.')
        st.markdown('[Gerenciar chaves no Google AI Studio](https://aistudio.google.com/api-keys)')
    elif erro.code == 403:
        st.error('Acesso negado (403): confira as permissões e restrições da chave e do projeto para a Gemini API.')
    elif erro.code == 404:
        st.error(f'O modelo {MODELO_GEMINI} não foi encontrado ou não está disponível para esse projeto (404).')
    elif erro.code == 429:
        st.error('Limite de uso atingido (429): confira a cota do projeto no AI Studio e tente novamente mais tarde.')
    elif erro.code in (500, 502, 503, 504):
        st.error(
            f'O serviço do Gemini está temporariamente indisponível (HTTP {erro.code}), '
            'mesmo após 4 tentativas. Aguarde alguns minutos e execute novamente.'
        )
        st.markdown('[Consultar o status do Gemini](https://aistudio.google.com/status)')
    else:
        # Evita exibir respostas brutas que possam conter dados da requisição.
        st.error(f'A Gemini API retornou um erro (HTTP {erro.code}). Tente novamente mais tarde.')

# 1. Configuração da Página Web
st.set_page_config(
    page_title='TestingStudio Web - Sprints 1, 2 e 3',
    page_icon='🧪',
    layout='wide'
)

st.title('TestingStudio Web — Auditoria do CAD0001')
st.caption('Disciplina: Teste de Software I | Prof. Frank Piffer')

# 2. Sidebar para Autenticação
with st.sidebar:
    st.header('Autenticação')

    api_key = st.text_input(
        'Gemini API Key (aistudio.google.com):',
        type='password', key='gemini_api_key'
    ).strip()

    st.caption('Cole somente a chave completa do AI Studio, sem aspas. Chaves AIza e AQ. são aceitas.')

    if st.button('Testar conexão'):
        if chave_preenchida(api_key):
            try:
                with st.spinner('Verificando acesso ao Gemini...'):
                    with criar_cliente(api_key) as client:
                        executar_com_tentativas(lambda: client.models.get(model=MODELO_GEMINI))
                st.success('Conexão confirmada: o Google permitiu consultar o modelo. Agora execute a auditoria.')
                st.caption('Este teste consulta o modelo; a geração do relatório também depende da cota disponível.')
            except errors.APIError as erro:
                exibir_erro_gemini(erro)
            except Exception:
                st.error('Não foi possível conectar ao Gemini. Confira a conexão com a internet e tente novamente.')

# 3. Leitura e Exibição do Fonte CAD0001
cad_default = '''FUNCTION cad0001_calcula_valor(val_param1, val_param2, val_param3)
    DEFINE p_val1, p_val2, p_val3 DECIMAL(12,2)

    IF val_param1 IS NULL THEN LET p_val1 = 0 ELSE LET p_val1 = val_param1 END IF
    IF val_param2 IS NULL THEN LET p_val2 = 0 ELSE LET p_val2 = val_param2 END IF
    IF val_param3 IS NULL THEN LET p_val3 = 0 ELSE LET p_val3 = val_param3 END IF

    IF p_val1 < 0 OR p_val2 < 0 OR p_val3 < 0 THEN RETURN -1 END IF

    LET l_val_calculado = (p_val1 * p_val2) + p_val3

    RETURN l_val_calculado
END FUNCTION'''

codigo = st.text_area(
    'Fonte CAD0001:',
    value=cad_default,
    height=220
)

aba_preta, aba_branca, aba_dados = st.tabs([
    'Sprint 1 · Caixa-Preta', 'Sprint 2 · Caixa-Branca', 'Sprint 3 · Dados e Mutantes',
])

with aba_preta:
    # 4. Botão de Auditoria e Integração com Gemini
    if st.button(
        'Executar Auditoria de Caixa-Preta (PCE & AVL)',
        type='primary'
    ):

        if chave_preenchida(api_key):
            try:
                prompt = f'''
    Analise o programa CAD0001 utilizando técnicas de Teste de Caixa-Preta.

    Considere a especificação da Sprint 1:

    - Valores numéricos maiores ou iguais a 0.00 pertencem à classe válida.
    - Valores negativos menores que 0.00 pertencem à classe inválida.
    - Valores NULL devem ser identificados como classe inválida segundo a especificação.

    IMPORTANTE:
    O código-fonte transforma valores NULL em 0 antes da validação.
    Portanto, destaque no relatório essa divergência entre a especificação
    e o comportamento implementado.

    Realize:

    1. Particionamento em Classes de Equivalência (PCE).
    2. Identifique as classes válidas e inválidas de val_param1,
       val_param2 e val_param3.
    3. Realize a Análise do Valor Limite (AVL).
    4. Considere epsilon = 0.01.
    5. Analise:
       - On-Point: 0.00
       - Off-Point: -0.01
       - Interior: 100.00
       - Exterior: -100.00
    6. Gere uma tabela de casos de teste.
    7. Informe os resultados esperados.
    8. Destaque possíveis divergências entre requisito e implementação.

    Código CAD0001:

    {codigo}
    '''

                with st.spinner('Analisando limites com Gemini...'):
                    with criar_cliente(api_key) as client:
                        resp = executar_com_tentativas(lambda: client.models.generate_content(
                            model=MODELO_GEMINI,
                            contents=prompt
                        ))

                st.session_state['relatorio_preta'] = (codigo, resp.text)

            except errors.APIError as erro:
                exibir_erro_gemini(erro)
            except Exception:
                st.error('Não foi possível concluir a auditoria. Confira a conexão com a internet e tente novamente.')

    relatorio = st.session_state.get('relatorio_preta')
    if relatorio and relatorio[0] == codigo:
        tab1, tab2 = st.tabs([
            'Relatório (PCE & AVL)',
            'Gráfico de Fronteira'
        ])

        with tab1:
            st.markdown(relatorio[1])

        with tab2:
            st.subheader(
                'Gráfico dos Pontos Limites (AVL)'
            )

            df = pd.DataFrame({
                'Ponto': [
                    'Off (-0.01)',
                    'On (0.00)',
                    'Interior (100.00)',
                    'Exterior (-100.00)'
                ],
                'Valor': [
                    -0.01,
                    0.00,
                    100.00,
                    -100.00
                ]
            })

            st.dataframe(df)

            st.bar_chart(
                df,
                x='Ponto',
                y='Valor'
            )

with aba_branca:
    st.header('Caixa-Branca: fluxo de controle e cobertura')
    st.caption(
        'Execução local de uma versão equivalente em Python do CAD0001 padrão. '
        'Esta análise não executa o fonte 4GL e não precisa de uma chave Gemini.'
    )
    if codigo.strip() != cad_default.strip():
        st.warning(
            'O fonte foi alterado. Este modelo de caixa-branca corresponde somente ao CAD0001 padrão. '
            'Restaure o fonte padrão para usar o grafo e a execução abaixo.'
        )
    else:
        with st.expander('Como o grafo e McCabe foram definidos'):
            st.markdown(
                'Cada decisão de nulidade tem dois ramos: atribuir zero ou copiar o valor. '
                'O `OR` dos negativos é expandido em três decisões, avaliadas da esquerda para a direita: '
                'ao encontrar um negativo, a versão Python retorna `-1` sem avaliar os próximos termos. '
                'Essa é a convenção deste modelo; não é uma medição do compilador 4GL. '
                'Se o `OR` fosse um único nó de decisão, o grafo teria complexidade 5. '
                'Entrada e saída são nós especiais incluídos na contagem.'
            )
            st.markdown(
                f'**V(G) = E − N + 2 = {len(ARESTAS)} − {len(NOS)} + 2 = 7**. '
                f'Pela outra fórmula: **P + 1 = {len(DECISOES)} + 1 = 7**. '
                'Os sete casos básicos abaixo formam uma base de caminhos independentes deste grafo. '
                'Isso não significa testar todos os caminhos nem provar ausência de defeitos.'
            )
            st.dataframe(
                pd.DataFrame([{'Nó': n, 'Conteúdo': t} for n, t in NOS.items()]),
                hide_index=True, alt='Blocos e decisões do modelo de fluxo de controle do CAD0001',
            )

        por_id = {caso.id: caso for caso in CASOS}
        selecionados = st.multiselect(
            'Casos de teste da suíte', options=list(por_id),
            default=[caso.id for caso in CASOS if caso.basico],
            format_func=lambda id: f'{id} · {por_id[id].descricao}', key='suite_branca',
        )
        with st.form('caso_personalizado'):
            st.markdown('**Adicionar um caso próprio**')
            cols = st.columns(3)
            entradas = tuple(col.text_input(f'Parâmetro {i + 1}', value='100', key=f'branca_param_{i}') for i, col in enumerate(cols))
            st.caption('Use vírgula ou ponto decimal; digite NULL para representar ausência de valor.')
            adicionar = st.form_submit_button('Adicionar à suíte')
        if adicionar:
            try:
                executar(entradas)
                extras = st.session_state.setdefault('casos_branca', [])
                extras.append(Caso(f'EX{len(extras) + 1:02}', 'Caso personalizado', entradas))
            except ValueError as erro:
                st.error(str(erro))
        if st.button('Limpar casos próprios'):
            st.session_state['casos_branca'] = []

        suite = [por_id[id] for id in selecionados] + st.session_state.get('casos_branca', [])
        execucoes = [(caso, *executar(caso.entradas)) for caso in suite]
        nos_cobertos, arestas_cobertas = cobertura([caminho for _, _, caminho in execucoes])
        metricas = st.columns(4)
        metricas[0].metric('Complexidade McCabe', 7)
        metricas[1].metric('Casos executados', len(suite))
        metricas[2].metric('Cobertura de nós', f'{100 * len(nos_cobertos) / len(NOS):.1f}%', f'{len(nos_cobertos)}/{len(NOS)} nós', delta_color='off')
        metricas[3].metric('Cobertura de arestas', f'{100 * len(arestas_cobertas) / len(ARESTAS):.1f}%', f'{len(arestas_cobertas)}/{len(ARESTAS)} arestas', delta_color='off')
        st.info(
            'Cobertura mede o fluxo executado. PASS/FAIL compara a saída com o requisito: '
            'negativos e NULL deveriam retornar -1. A implementação preservada converte NULL em zero, '
            'portanto pode cobrir todos os ramos e ainda falhar nesses casos.'
        )
        linhas = []
        for caso, resultado, caminho in execucoes:
            esperado = esperado_especificacao(caso.entradas)
            linhas.append({
                'ID': caso.id, 'Cenário': caso.descricao,
                **{f'Parâmetro {i + 1}': 'NULL' if valor is None else str(valor) for i, valor in enumerate(caso.entradas)},
                'Esperado (requisito)': f'{esperado:.2f}', 'Obtido (versão Python)': f'{resultado:.2f}',
                'Situação': 'PASS' if resultado == esperado else 'FAIL',
                'Caminho': ' → '.join(caminho),
            })
        if linhas:
            tabela = pd.DataFrame(linhas)
            st.dataframe(tabela, hide_index=True, alt='Casos executados, resultados e caminhos percorridos')
            st.download_button('Baixar resultados CSV', tabela.to_csv(index=False).encode('utf-8-sig'), 'caixa_branca_cad0001.csv', 'text/csv')
        else:
            st.caption('Selecione um caso para executar e medir a cobertura.')

        visualizacao = st.selectbox(
            'Destacar no grafo', ['Cobertura da suíte'] + [caso.id for caso in suite], key='grafo_branca',
        )
        if visualizacao == 'Cobertura da suíte':
            nos_grafo, arestas_grafo = nos_cobertos, arestas_cobertas
        else:
            caminho = next(caminho for caso, _, caminho in execucoes if caso.id == visualizacao)
            nos_grafo, arestas_grafo = cobertura([caminho])
        st.caption('Verde: nós e arestas percorridos. Cinza: ainda não percorridos na seleção. V/F: verdadeiro/falso.')
        st.mermaid_chart(diagrama(nos_grafo, arestas_grafo), alt='Grafo do CAD0001 com os nós e as arestas executados destacados em verde')
        with st.expander('Arestas e pendências de cobertura da suíte'):
            st.dataframe(pd.DataFrame([
                {'Origem': a, 'Destino': b, 'Desvio': d or 'Sequência', 'Coberta': (a, b) in arestas_cobertas}
                for a, b, d in ARESTAS
            ]), hide_index=True, alt='Todas as arestas e sua cobertura pela suíte selecionada')
            pendentes = [n for n in NOS if n not in nos_cobertos]
            st.caption('Nós pendentes: ' + (', '.join(pendentes) if pendentes else 'nenhum'))
        with st.expander('Limites da execução equivalente'):
            st.markdown(
                'Os valores usam `Decimal` em Python, sem erros de ponto flutuante binário. '
                'As entradas respeitam duas casas e o intervalo de DECIMAL(12,2). '
                'O cálculo não simula overflow ou arredondamento do resultado pelo runtime 4GL. '
                'A cobertura apresentada vale para este modelo fixo do CAD0001, não para fontes arbitrários.'
            )

with aba_dados:
    st.header('Fluxo de dados e testes de mutação')
    st.caption('Análise local do mesmo modelo Python do CAD0001 padrão, sem chamadas ao Gemini.')
    if codigo.strip() != cad_default.strip():
        st.warning('Restaure o fonte padrão para executar a Sprint 3. O modelo não analisa fontes alterados.')
    else:
        usar_suite_branca = st.checkbox('Usar a suíte selecionada na Sprint 2, incluindo casos próprios', value=True, key='s3_reusar')
        if usar_suite_branca:
            casos_s3 = suite
            st.caption('Alterações nos casos da Sprint 2 atualizam os resultados abaixo automaticamente.')
        else:
            ids_s3 = st.multiselect(
                'Casos para a Sprint 3', options=[c.id for c in CASOS],
                default=[c.id for c in CASOS if c.basico],
                format_func=lambda id: f'{id} · {por_id[id].descricao}', key='suite_s3',
            )
            casos_s3 = [por_id[id] for id in ids_s3]
        st.caption(f'Casos em execução: {len(casos_s3)}. ' + (', '.join(c.id for c in casos_s3) or 'Nenhum selecionado.'))
        dados_tab, mutantes_tab = st.tabs(['Definição–uso (DU)', 'Mutantes e escore'])
        with dados_tab:
            st.markdown(
                '**Definição (d):** atribuição de um valor à variável. '
                '**c-uso:** uso em cálculo, atribuição ou retorno. '
                '**p-uso:** uso em decisão, identificado pela aresta percorrida. '
                'Um par DU liga a definição ao uso sem outra definição da mesma variável no caminho.'
            )
            du_casos = analisar_du(casos_s3)
            cobertos = sum(bool(ids) for ids in du_casos.values())
            cols_du = st.columns(3)
            cols_du[0].metric('Pares DU factíveis', len(UNIVERSO_DU))
            cols_du[1].metric('Pares DU cobertos', cobertos)
            cols_du[2].metric('Cobertura de pares DU', f'{100 * cobertos / len(UNIVERSO_DU):.1f}%')
            st.caption(
                'Critério: todos os pares DU factíveis deste modelo, com p-usos nas arestas. '
                'O universo é obtido pelas 27 combinações de NULL, negativo e não negativo; '
                'essas classes determinam todas as decisões do CAD0001. Não é cobertura de todos os caminhos DU.'
            )
            tabela_du = pd.DataFrame([
                {'Variável': par.variavel, 'Definição': par.definicao, 'Uso': par.uso,
                 'Tipo': par.tipo, 'Coberto': bool(ids), 'Casos que cobrem': ', '.join(ids) or '—'}
                for par, ids in du_casos.items()
            ])
            st.dataframe(tabela_du, hide_index=True, alt='Pares definição–uso factíveis e testes que os exercitam')
            st.download_button('Baixar cobertura DU', tabela_du.to_csv(index=False).encode('utf-8-sig'), 'cad0001_pares_du.csv', 'text/csv')
            st.info(
                'Após p_val receber zero em N2, N5 ou N8, o ramo verdadeiro de p_val < 0 é impossível. '
                'Esses três pares infactíveis ficam fora do denominador. As entradas val_param são definidas em INICIO.'
            )
            if casos_s3:
                caso_du_id = st.selectbox('Acompanhar variáveis de um caso', [c.id for c in casos_s3], key='s3_caso_du')
                caso_du = next(c for c in casos_s3 if c.id == caso_du_id)
                resultado_du, caminho_du = executar(caso_du.entradas)
                st.caption('Entradas: ' + ', '.join('NULL' if v is None else str(v) for v in caso_du.entradas))
                st.code(' → '.join(caminho_du), language=None)
                eventos = []
                for indice, no in enumerate(caminho_du):
                    eventos.append({
                        'Passo': indice + 1, 'Nó': no,
                        'Definições': ', '.join(DEFINICOES.get(no, ())) or '—',
                        'c-usos': ', '.join(C_USOS.get(no, ())) or '—',
                        'p-uso na aresta': (f'{P_USOS[no]}: {no} → {caminho_du[indice + 1]}' if no in P_USOS else '—'),
                    })
                st.dataframe(pd.DataFrame(eventos), hide_index=True, alt='Sequência de definições e usos no caso selecionado')
                st.caption(f'Resultado da versão Python: {resultado_du:.2f}. Em N14, os operandos são usados antes de definir resultado.')

        with mutantes_tab:
            st.markdown(
                'Cada mutante contém **uma alteração controlada**. Ele é **morto** quando algum caso produz '
                'uma saída diferente da versão original; é **sobrevivente** quando nenhum caso selecionado detecta a mudança. '
                'Sobreviver não comprova equivalência.'
            )
            st.info(
                'Aqui o oráculo é o comportamento original, incluindo NULL → 0. '
                'O PASS/FAIL de requisito da Sprint 2 é uma avaliação separada. '
                'Um escore alto não corrige a divergência de NULL nem comprova que o programa atende à especificação.'
            )
            resumo_mutantes, matriz_mutantes, escore = analisar_mutacao(casos_s3)
            mortos = sum(r['Situação'] == 'Morto' for r in resumo_mutantes)
            sobreviventes = sum(r['Situação'] == 'Sobrevivente' for r in resumo_mutantes)
            equivalentes = sum(bool(m.equivalente) for m in MUTANTES)
            cols_mut = st.columns(4)
            cols_mut[0].metric('Mutantes mortos', mortos)
            cols_mut[1].metric('Sobreviventes', sobreviventes)
            cols_mut[2].metric('Equivalentes comprovados', equivalentes)
            cols_mut[3].metric('Escore de mutação', '—' if escore is None else f'{escore:.1f}%')
            st.caption(
                f'Escore = mortos / (total − equivalentes) × 100 = mortos / ({len(MUTANTES)} − {equivalentes}) × 100. '
                'Sem casos selecionados, o escore fica indefinido e os mutantes não equivalentes ficam como não executados.'
            )
            tabela_mutantes = pd.DataFrame(resumo_mutantes)
            st.dataframe(tabela_mutantes, hide_index=True, alt='Alterações dos dez mutantes e resultados de sua execução')
            st.download_button('Baixar resumo dos mutantes', tabela_mutantes.to_csv(index=False).encode('utf-8-sig'), 'cad0001_mutantes.csv', 'text/csv')
            st.caption(
                'ROR: operador relacional; AOR: aritmético; COR: conector lógico; LVR: valor literal. '
                'M09 é equivalente pela comutatividade da multiplicação no domínio Decimal deste modelo, '
                'independentemente dos resultados da suíte.'
            )
            if matriz_mutantes:
                detalhe_id = st.selectbox('Ver resultados de um mutante', [m.id for m in MUTANTES], key='s3_mutante')
                detalhe = pd.DataFrame([r for r in matriz_mutantes if r['Mutante'] == detalhe_id])
                st.dataframe(detalhe, hide_index=True, alt='Comparação de saídas do mutante selecionado com a versão original')
                st.download_button('Baixar matriz completa de execução', pd.DataFrame(matriz_mutantes).to_csv(index=False).encode('utf-8-sig'), 'cad0001_matriz_mutacao.csv', 'text/csv')
            if sobreviventes:
                st.markdown(
                    '**Como reforçar a suíte:** CT08 (todos zero) detecta M01/M02/M03; '
                    'CT01 detecta M04/M05/M10; CT05 detecta M06/M08; CT02 detecta M07. '
                    'Selecione esses casos e observe quais sobreviventes são mortos.'
                )
