import streamlit as st
import pandas as pd
from google import genai

# 1. Configuração da Página Web
st.set_page_config(
    page_title='TestingStudio Web - Sprint 1',
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
        type='password'
    )

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

# 4. Botão de Auditoria e Integração com Gemini
if st.button(
    'Executar Auditoria de Caixa-Preta (PCE & AVL)',
    type='primary'
):

    if not api_key:
        st.error(
            'Insira sua API Key do Google AI Studio na barra lateral.'
        )

    else:
        try:
            client = genai.Client(api_key=api_key)

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
                resp = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=prompt
                )

            tab1, tab2 = st.tabs([
                'Relatório (PCE & AVL)',
                'Gráfico de Fronteira'
            ])

            with tab1:
                st.markdown(resp.text)

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

        except Exception as erro:
            st.error(
                f'Erro ao executar a auditoria: {erro}'
            )