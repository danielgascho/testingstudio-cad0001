"""Modelo instrumentado da função de cálculo ORIGINAL, sem executar Informix-4GL."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


NOS = {
    'INICIO': 'Entrada: p_val1, p_val2, p_val3',
    'N1': 'p_val1 IS NULL?', 'N2': 'p_val1 = 0',
    'N3': 'p_val2 IS NULL?', 'N4': 'p_val2 = 0',
    'N5': 'p_val3 IS NULL?', 'N6': 'p_val3 = 0',
    'N7': 'l_val_calculado = (p_val1 * p_val2) + p_val3',
    'N8': 'RETURN l_val_calculado', 'FIM': 'Saída da função',
}
ARESTAS = (
    ('INICIO', 'N1', ''), ('N1', 'N2', 'V'), ('N1', 'N3', 'F'), ('N2', 'N3', ''),
    ('N3', 'N4', 'V'), ('N3', 'N5', 'F'), ('N4', 'N5', ''),
    ('N5', 'N6', 'V'), ('N5', 'N7', 'F'), ('N6', 'N7', ''),
    ('N7', 'N8', ''), ('N8', 'FIM', ''),
)
DECISOES = frozenset({'N1', 'N3', 'N5'})
COMPLEXIDADE = len(ARESTAS) - len(NOS) + 2
MAXIMO = Decimal('9999999999.99')
EPSILON = Decimal('0.01')


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
    Caso('CT05', 'Off-point no parâmetro 1', ('-0.01', '100', '100')),
    Caso('CT06', 'Off-point no parâmetro 2', ('100', '-0.01', '100')),
    Caso('CT07', 'Off-point no parâmetro 3', ('100', '100', '-0.01')),
    Caso('CT08', 'Todos zero', ('0', '0', '0')),
    Caso('CT09', 'Todos NULL', (None, None, None)),
    Caso('CT10', 'Todos negativos (resultado representável)', ('-1', '-1', '-1')),
    Caso('CT11', 'Exterior no parâmetro 1', ('-100', '100', '100')),
    Caso('CT12', 'Exterior no parâmetro 2', ('100', '-100', '100')),
    Caso('CT13', 'Exterior no parâmetro 3', ('100', '100', '-100')),
    Caso('CT14', 'On-point no parâmetro 1', ('0', '100', '100')),
    Caso('CT15', 'On-point no parâmetro 2', ('100', '0', '100')),
    Caso('CT16', 'On-point no parâmetro 3', ('100', '100', '0')),
    Caso('CT17', 'Vizinho válido no parâmetro 1', ('0.01', '100', '100')),
    Caso('CT18', 'Vizinho válido no parâmetro 2', ('100', '0.01', '100')),
    Caso('CT19', 'Vizinho válido no parâmetro 3', ('100', '100', '0.01')),
)


class LimiteModelo(ValueError):
    """O resultado exige semântica de arredondamento/overflow do runtime nativo."""


def ler_valor(texto):
    if texto is None or str(texto).strip().upper() == 'NULL':
        return None
    try:
        valor = Decimal(str(texto).strip().replace(',', '.'))
        if (not valor.is_finite() or abs(valor) > MAXIMO
                or valor != valor.quantize(EPSILON)):
            raise ValueError
        return valor
    except (InvalidOperation, ValueError):
        raise ValueError('Informe NULL ou um número com até duas casas decimais, dentro de DECIMAL(12,2).') from None


def executar(entradas):
    """Reproduz as três decisões de NULL; não acrescenta rejeição de negativos."""
    if len(entradas) != 3:
        raise ValueError('São necessários três parâmetros.')
    valores = tuple(ler_valor(v) for v in entradas)
    caminho = ['INICIO']
    normalizados = []
    for valor, decisao, nulo in zip(valores, ['N1', 'N3', 'N5'], ['N2', 'N4', 'N6']):
        caminho.append(decisao)
        if valor is None:
            caminho.append(nulo)
        normalizados.append(Decimal('0') if valor is None else valor)
    resultado = normalizados[0] * normalizados[1] + normalizados[2]
    if abs(resultado) > MAXIMO or resultado != resultado.quantize(EPSILON):
        raise LimiteModelo('Este cálculo exige arredondamento ou excede DECIMAL(12,2). Valide no runtime Informix; o modelo não atribui PASS/FAIL nesse caso.')
    caminho.extend(['N7', 'N8', 'FIM'])
    return resultado, tuple(caminho)


def esperado_especificacao(entradas):
    """Oráculo funcional independente: rejeitar negativos e NULL (sentinela -1 adotada)."""
    if len(entradas) != 3:
        raise ValueError('São necessários três parâmetros.')
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
