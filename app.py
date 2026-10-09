import streamlit as st
import pandas as pd
import random
import time
from google import genai
from google.genai import errors
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
    page_title='TestingStudio Web - Sprints 1 e 2',
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

aba_preta, aba_branca = st.tabs(['Sprint 1 · Caixa-Preta', 'Sprint 2 · Caixa-Branca'])

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
