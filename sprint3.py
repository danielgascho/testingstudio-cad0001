"""Fluxo de dados e mutantes controlados do modelo Python do CAD0001."""

from dataclasses import dataclass
from decimal import Decimal
from itertools import product

from caixa_branca import executar, ler_valor


# No original, os próprios parâmetros são redefinidos quando recebem NULL.
DEFINICOES = {'INICIO': ('p_val1', 'p_val2', 'p_val3'),
              'N2': ('p_val1',), 'N4': ('p_val2',), 'N6': ('p_val3',),
              'N7': ('l_val_calculado',)}
C_USOS = {'N7': ('p_val1', 'p_val2', 'p_val3'), 'N8': ('l_val_calculado',)}
P_USOS = {'N1': 'p_val1', 'N3': 'p_val2', 'N5': 'p_val3'}


@dataclass(frozen=True, order=True)
class ParDU:
    variavel: str
    definicao: str
    uso: str
    tipo: str


def pares_do_caminho(caminho):
    """Liga cada uso à última definição, em caminho livre de redefinição."""
    ultimas = {}
    pares = set()
    for indice, no in enumerate(caminho):
        for variavel in C_USOS.get(no, ()):
            pares.add(ParDU(variavel, ultimas[variavel], no, 'c-uso'))
        if no in P_USOS:
            variavel = P_USOS[no]
            pares.add(ParDU(variavel, ultimas[variavel], f'{no} → {caminho[indice + 1]}', 'p-uso'))
        # Em N7 os operandos são usados antes de definir o resultado.
        for variavel in DEFINICOES.get(no, ()):
            ultimas[variavel] = no
    return frozenset(pares)


def universo_du():
    # As três decisões dependem somente de NULL/não NULL: 2³ = 8 fluxos.
    return frozenset(par for entrada in product((None, '100'), repeat=3)
                     for par in pares_do_caminho(executar(entrada)[1]))


UNIVERSO_DU = universo_du()


def analisar_du(casos):
    por_par = {par: [] for par in sorted(UNIVERSO_DU)}
    for caso in casos:
        for par in pares_do_caminho(executar(caso.entradas)[1]):
            por_par[par].append(caso.id)
    return por_par


@dataclass(frozen=True)
class Mutante:
    id: str
    operador: str
    original: str
    alterado: str
    equivalente: str = ''


MUTANTES = (
    Mutante('M01', 'AOR', '(p_val1 * p_val2) + p_val3', '(p_val1 + p_val2) + p_val3'),
    Mutante('M02', 'AOR', '(p_val1 * p_val2) + p_val3', '(p_val1 * p_val2) - p_val3'),
    Mutante('M03', 'Substituição de literal', 'NULL no parâmetro 1 → 0', 'NULL no parâmetro 1 → 1'),
    Mutante('M04', 'Substituição de literal', 'NULL no parâmetro 2 → 0', 'NULL no parâmetro 2 → 1'),
    Mutante('M05', 'Substituição de literal', 'NULL no parâmetro 3 → 0', 'NULL no parâmetro 3 → 1'),
    Mutante('M06', 'Remoção de termo', '(p_val1 * p_val2) + p_val3', 'p_val1 * p_val2'),
    Mutante('M07', 'LVR (variável local)', '(p_val1 * p_val2) + p_val3', '(p_val1 * p_val3) + p_val3'),
    Mutante('M08', 'Substituição de retorno', 'RETURN l_val_calculado', 'RETURN 0'),
    Mutante('M09', 'Permutação de operandos', 'p_val1 * p_val2', 'p_val2 * p_val1',
            'A multiplicação de Decimal é comutativa no domínio deste modelo. As demais etapas são idênticas.'),
    Mutante('M10', 'AOR', '(p_val1 * p_val2) + p_val3', '(p_val1 * p_val2) * p_val3'),
)


def executar_mutante(entradas, id_mutante):
    if id_mutante not in {m.id for m in MUTANTES}:
        raise ValueError('Mutante desconhecido.')
    if len(entradas) != 3:
        raise ValueError('São necessários três parâmetros.')
    valores = [ler_valor(v) for v in entradas]
    p = [Decimal('0') if v is None else v for v in valores]
    for i in range(3):
        if id_mutante == f'M0{i + 3}' and valores[i] is None:
            p[i] = Decimal('1')
    if id_mutante == 'M01':
        return p[0] + p[1] + p[2]
    if id_mutante == 'M02':
        return p[0] * p[1] - p[2]
    if id_mutante == 'M06':
        return p[0] * p[1]
    if id_mutante == 'M07':
        return p[0] * p[2] + p[2]
    if id_mutante == 'M08':
        return Decimal('0')
    if id_mutante == 'M09':
        return p[1] * p[0] + p[2]
    if id_mutante == 'M10':
        return p[0] * p[1] * p[2]
    return p[0] * p[1] + p[2]


def analisar_mutacao(casos):
    """Morto = saída diferente do original; não confundir com falha de requisito."""
    casos = tuple(casos)
    originais = {c.id: executar(c.entradas)[0] for c in casos}
    resumo, matriz = [], []
    for mutante in MUTANTES:
        detectores = []
        for caso in casos:
            obtido = executar_mutante(caso.entradas, mutante.id)
            detectou = obtido != originais[caso.id]
            if detectou:
                detectores.append(caso.id)
            matriz.append({'Mutante': mutante.id, 'Caso': caso.id,
                           'Original': f'{originais[caso.id]:.2f}', 'Mutante obtido': f'{obtido:.2f}',
                           'Detectou alteração': detectou})
        status = ('Equivalente' if mutante.equivalente else
                  'Não executado' if not casos else 'Morto' if detectores else 'Sobrevivente')
        resumo.append({'ID': mutante.id, 'Operador': mutante.operador,
                       'Original': mutante.original, 'Alterado': mutante.alterado,
                       'Situação': status, 'Testes que detectam': ', '.join(detectores) or '—',
                       'Justificativa de equivalência': mutante.equivalente or '—'})
    mortos = sum(r['Situação'] == 'Morto' for r in resumo)
    equivalentes = sum(bool(m.equivalente) for m in MUTANTES)
    escore = 100 * mortos / (len(MUTANTES) - equivalentes) if casos else None
    return resumo, matriz, escore
