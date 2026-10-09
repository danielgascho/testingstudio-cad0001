"""Modelo executável do CAD0001 para estudo de cobertura, sem executar 4GL."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


NOS = {
    'INICIO': 'Entrada da função',
    'N1': 'val_param1 IS NULL?', 'N2': 'p_val1 = 0', 'N3': 'p_val1 = val_param1',
    'N4': 'val_param2 IS NULL?', 'N5': 'p_val2 = 0', 'N6': 'p_val2 = val_param2',
    'N7': 'val_param3 IS NULL?', 'N8': 'p_val3 = 0', 'N9': 'p_val3 = val_param3',
    'N10': 'p_val1 < 0?', 'N11': 'p_val2 < 0?', 'N12': 'p_val3 < 0?',
    'N13': 'RETURN -1', 'N14': 'resultado = (p_val1 * p_val2) + p_val3',
    'N15': 'RETURN resultado', 'FIM': 'Saída da função',
}
ARESTAS = (
    ('INICIO', 'N1', ''), ('N1', 'N2', 'V'), ('N1', 'N3', 'F'),
    ('N2', 'N4', ''), ('N3', 'N4', ''), ('N4', 'N5', 'V'), ('N4', 'N6', 'F'),
    ('N5', 'N7', ''), ('N6', 'N7', ''), ('N7', 'N8', 'V'), ('N7', 'N9', 'F'),
    ('N8', 'N10', ''), ('N9', 'N10', ''), ('N10', 'N13', 'V'), ('N10', 'N11', 'F'),
    ('N11', 'N13', 'V'), ('N11', 'N12', 'F'), ('N12', 'N13', 'V'), ('N12', 'N14', 'F'),
    ('N13', 'FIM', ''), ('N14', 'N15', ''), ('N15', 'FIM', ''),
)
DECISOES = frozenset({'N1', 'N4', 'N7', 'N10', 'N11', 'N12'})


@dataclass(frozen=True)
class Caso:
    id: str
    descricao: str
    entradas: tuple
    basico: bool = False


CASOS = (
    Caso('CT01', 'Interior: três valores válidos', ('100', '100', '100'), True),
    Caso('CT02', 'NULL no parâmetro 1', (None, '100', '100'), True),
    Caso('CT03', 'NULL no parâmetro 2', ('100', None, '100'), True),
    Caso('CT04', 'NULL no parâmetro 3', ('100', '100', None), True),
    Caso('CT05', 'Negativo no parâmetro 1', ('-0.01', '100', '100'), True),
    Caso('CT06', 'Negativo no parâmetro 2', ('100', '-0.01', '100'), True),
    Caso('CT07', 'Negativo no parâmetro 3', ('100', '100', '-0.01'), True),
    Caso('CT08', 'Todos zero', ('0', '0', '0')),
    Caso('CT09', 'Todos NULL', (None, None, None)),
    Caso('CT10', 'Todos negativos', ('-0.01', '-0.01', '-0.01')),
    Caso('CT11', 'Exterior no parâmetro 1', ('-100', '100', '100')),
    Caso('CT12', 'Exterior no parâmetro 2', ('100', '-100', '100')),
    Caso('CT13', 'Exterior no parâmetro 3', ('100', '100', '-100')),
)


def ler_valor(texto):
    if texto is None or str(texto).strip().upper() == 'NULL':
        return None
    try:
        valor = Decimal(str(texto).strip().replace(',', '.'))
        if (not valor.is_finite() or abs(valor) > Decimal('9999999999.99')
                or valor != valor.quantize(Decimal('0.01'))):
            raise ValueError
        return valor
    except (InvalidOperation, ValueError):
        raise ValueError('Informe NULL ou um número com até duas casas decimais, dentro de DECIMAL(12,2).') from None


def executar(entradas):
    """Preserva NULL→0 e registra o OR com curto-circuito da versão Python."""
    if len(entradas) != 3:
        raise ValueError('São necessários três parâmetros.')
    valores = tuple(ler_valor(v) for v in entradas)
    caminho = ['INICIO']
    normalizados = []
    for valor, decisao, nulo, copia in zip(valores, ['N1', 'N4', 'N7'], ['N2', 'N5', 'N8'], ['N3', 'N6', 'N9']):
        caminho.extend([decisao, nulo if valor is None else copia])
        normalizados.append(Decimal('0') if valor is None else valor)
    resultado = None
    for valor, decisao in zip(normalizados, ['N10', 'N11', 'N12']):
        caminho.append(decisao)
        if valor < 0:
            caminho.append('N13')
            resultado = Decimal('-1')
            break
    if resultado is None:
        caminho.extend(['N14', 'N15'])
        resultado = normalizados[0] * normalizados[1] + normalizados[2]
    caminho.append('FIM')
    return resultado, tuple(caminho)


def esperado_especificacao(entradas):
    valores = tuple(ler_valor(v) for v in entradas)
    if any(v is None or v < 0 for v in valores):
        return Decimal('-1')
    return valores[0] * valores[1] + valores[2]


def cobertura(caminhos):
    nos = {n for caminho in caminhos for n in caminho}
    arestas = {par for caminho in caminhos for par in zip(caminho, caminho[1:])}
    return nos, arestas


def diagrama(nos_cobertos, arestas_cobertas):
    linhas = ['flowchart TD']
    for no, texto in NOS.items():
        rotulo = f'{no}: {texto}'
        if no in DECISOES:
            linhas.append(f'{no}{{"{rotulo}"}}')
        elif no in ('INICIO', 'FIM'):
            linhas.append(f'{no}(["{rotulo}"])')
        else:
            linhas.append(f'{no}["{rotulo}"]')
    for origem, destino, desvio in ARESTAS:
        linhas.append(f'{origem} -->' + (f'|{desvio}|' if desvio else '') + f' {destino}')
    linhas.extend([
        'classDef coberto fill:#d1fae5,stroke:#047857,color:#064e3b',
        'classDef pendente fill:#f1f5f9,stroke:#64748b,color:#334155',
    ])
    for no in NOS:
        linhas.append(f'class {no} ' + ('coberto' if no in nos_cobertos else 'pendente'))
    for indice, (origem, destino, _) in enumerate(ARESTAS):
        cor = '#059669' if (origem, destino) in arestas_cobertas else '#94a3b8'
        linhas.append(f'linkStyle {indice} stroke:{cor},stroke-width:2px')
    return '\n'.join(linhas)
