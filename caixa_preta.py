"""PCE e AVL determinísticas; a regra vem do manual, não do código auditado."""

from caixa_branca import CASOS, executar, esperado_especificacao
from fonte import EVIDENCIA, exigir_referencia, ler_fonte


def classes_equivalencia(fonte):
    return [
        {'Parâmetro': f'P{i}', 'Classe': classe, 'Domínio / exemplo': dominio, 'Esperado': esperado}
        for i in range(1, 4)
        for classe, dominio, esperado in [
            ('Válida', f'0,00 até {fonte.maximo:.2f}', 'Calcular (P1 × P2) + P3, se o resultado for representável'),
            ('Inválida: negativo', '-0,01 ou -100,00', 'Rejeitar com -1 conforme o manual'),
            ('Inválida: NULL', 'Ausência de valor', 'Rejeitar; retorno -1 adotado pelo projeto'),
            ('Fora do tipo', 'Mais de duas casas ou magnitude acima do limite', 'Fora do domínio deste modelo; validar conversão no runtime'),
        ]
    ]


def pontos_avl(fonte):
    return [
        {'Ponto': nome, 'Valor': valor, 'Classe': classe}
        for nome, valor, classe in [
            ('Exterior', -100, 'Inválida'), ('Off-point', float(-fonte.epsilon), 'Inválida'),
            ('On-point', 0, 'Válida'), ('Vizinho válido (+ε)', float(fonte.epsilon), 'Válida'),
            ('Interior', 100, 'Válida'),
        ]
    ]


def analisar(casos=CASOS, fonte=None):
    fonte = fonte or ler_fonte()
    exigir_referencia(fonte)
    linhas = []
    for caso in casos:
        obtido, _ = executar(caso.entradas)
        esperado = esperado_especificacao(caso.entradas)
        linhas.append({
            'Caso': caso.id, 'Cenário': caso.descricao,
            **{f'P{i}': 'NULL' if v is None else str(v) for i, v in enumerate(caso.entradas, 1)},
            'Esperado (regra)': f'{esperado:.2f}', 'Obtido (modelo Python)': f'{obtido:.2f}',
            'Situação': 'PASS' if obtido == esperado else 'FAIL',
            'Origem da evidência': EVIDENCIA, 'Fonte': fonte.nome, 'SHA-256 (LF)': fonte.sha256,
        })
    return linhas
