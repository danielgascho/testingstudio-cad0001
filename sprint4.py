"""Validação do plano de testes e rastreabilidade do CAD0001."""

from datetime import datetime, timezone

from caixa_branca import CASOS, NOS, ARESTAS, executar, esperado_especificacao, cobertura, ler_valor
from sprint3 import UNIVERSO_DU, analisar_du, analisar_mutacao
from fonte import EVIDENCIA, exigir_referencia, ler_fonte


REQUISITOS = {
    'REQ-CAD01': 'Calcular (param1 × param2) + param3 para entradas numéricas não negativas.',
    'REQ-CAD02': 'Aceitar zero como entrada válida.',
    'REQ-CAD03': 'Retornar -1 quando qualquer parâmetro for negativo.',
    'REQ-CAD04': 'Rejeitar NULL (classe inválida no manual); retorno -1 adotado como critério deste projeto.',
}
ORIGENS = {
    'REQ-CAD01': 'Manual Sprint 1, seção 3: fórmula de cálculo.',
    'REQ-CAD02': 'Manual Sprint 1, seção 2: classe válida ≥ 0 e On-point.',
    'REQ-CAD03': 'Manual Sprint 1, tabela 1: Off/Exterior devem retornar -1.',
    'REQ-CAD04': 'Manual Sprint 1, seção 2: NULL inválido. Sentinela -1 é convenção explícita do projeto.',
}


def vinculos(entradas):
    valores = tuple(ler_valor(v) for v in entradas)
    ids = []
    if all(v is not None and v >= 0 for v in valores):
        ids.append('REQ-CAD01')
        if any(v == 0 for v in valores):
            ids.append('REQ-CAD02')
    if any(v is not None and v < 0 for v in valores):
        ids.append('REQ-CAD03')
    if any(v is None for v in valores):
        ids.append('REQ-CAD04')
    return tuple(ids)


def validar(casos, fonte=None):
    fonte = fonte or ler_fonte()
    exigir_referencia(fonte)
    casos = tuple(casos)
    if len({c.id for c in casos}) != len(casos):
        raise ValueError('Os identificadores dos casos precisam ser únicos.')
    plano = {c.id: c for c in CASOS}
    for c in casos:
        if c.id in plano and c != plano[c.id]:
            raise ValueError('Um caso do plano base não pode ser substituído por outro conteúdo.')
        plano[c.id] = c
    execucoes = {}
    caminhos = []
    for caso in casos:
        obtido, caminho = executar(caso.entradas)
        esperado = esperado_especificacao(caso.entradas)
        execucoes[caso.id] = (obtido, esperado, obtido == esperado)
        caminhos.append(caminho)
    testes = []
    for caso in plano.values():
        ids = vinculos(caso.entradas)
        execucao = execucoes.get(caso.id)
        valores = [ler_valor(v) for v in caso.entradas]
        fluxo = ('Exceção' if any(v is None or v < 0 for v in valores) else
                 'Alternativo / limite' if any(v == 0 for v in valores) else 'Principal')
        testes.append({
            'Caso': caso.id, 'Cenário': caso.descricao, 'Fluxo': fluxo,
            'Entradas': ', '.join('NULL' if v is None else str(v) for v in caso.entradas),
            'Requisitos': ', '.join(ids),
            'Esperado': f'{esperado_especificacao(caso.entradas):.2f}',
            'Obtido': f'{execucao[0]:.2f}' if execucao else '—',
            'Situação': ('PASS' if execucao[2] else 'FAIL') if execucao else 'Não executado',
            'Origem da evidência': EVIDENCIA if execucao else 'Não executado',
            'Fonte': fonte.nome, 'SHA-256 (LF)': fonte.sha256,
        })
    matriz = []
    for id_req, descricao in REQUISITOS.items():
        ligados = [t for t in testes if id_req in t['Requisitos'].split(', ')]
        falhas = [t['Caso'] for t in ligados if t['Situação'] == 'FAIL']
        aprovados = [t['Caso'] for t in ligados if t['Situação'] == 'PASS']
        pendentes = [t['Caso'] for t in ligados if t['Situação'] == 'Não executado']
        situacao = ('Reprovado' if falhas else 'Sem execução' if not aprovados else
                    'Parcial' if pendentes else 'Aprovado no plano')
        matriz.append({
            'Requisito': id_req, 'Descrição': descricao,
            'Origem / critério': ORIGENS[id_req],
            'Fonte': fonte.nome, 'SHA-256 (LF)': fonte.sha256,
            'Casos planejados': ', '.join(t['Caso'] for t in ligados),
            'PASS': ', '.join(aprovados) or '—', 'FAIL': ', '.join(falhas) or '—',
            'Pendentes': ', '.join(pendentes) or '—', 'Situação': situacao,
        })
    nos, arestas = cobertura(caminhos)
    du = analisar_du(casos)
    mutantes, _, escore = analisar_mutacao(casos)
    passados = sum(t['Situação'] == 'PASS' for t in testes)
    falhos = sum(t['Situação'] == 'FAIL' for t in testes)
    pendentes = sum(t['Situação'] == 'Não executado' for t in testes)
    veredito = ('Reprovado no plano' if falhos else 'Validação incompleta' if pendentes else 'Aprovado no plano')
    return {
        'matriz': matriz, 'testes': testes, 'veredito': veredito,
        'fonte': fonte.nome, 'sha256': fonte.sha256, 'evidencia': EVIDENCIA,
        'executados': len(casos), 'pass': passados, 'fail': falhos, 'pendentes': pendentes,
        'requisitos_vinculados': sum(any(t['Requisitos'] and r['Requisito'] in t['Requisitos'].split(', ')
                                       and t['Situação'] != 'Não executado' for t in testes) for r in matriz),
        'requisitos_aprovados': sum(r['Situação'] == 'Aprovado no plano' for r in matriz),
        'orfaos': [t['Caso'] for t in testes if not t['Requisitos']],
        'cobertura_nos': 100 * len(nos) / len(NOS),
        'cobertura_arestas': 100 * len(arestas) / len(ARESTAS),
        'cobertura_du': 100 * sum(bool(ids) for ids in du.values()) / len(UNIVERSO_DU),
        'escore_mutacao': escore,
        'mutantes_mortos': sum(m['Situação'] == 'Morto' for m in mutantes),
    }


def pitch(dados):
    return f'''# Pitch — TestingStudio Web

## 1. Problema e objetivo (30 segundos)
Analisar um programa exige verificar regras de negócio e investigar o comportamento interno.
O TestingStudio reúne essas perspectivas em uma ferramenta educacional para o CAD0001.

## 2. Solução construída (40 segundos)
A Sprint 1 lê o CAD0001 original, calcula PCE/AVL e compara saídas do modelo com a regra.
O Gemini é um comentário opcional, separado das evidências determinísticas.
A Sprint 2 executa um modelo instrumentado da função original e mostra GFC, McCabe e cobertura.
A Sprint 3 acompanha definições e usos das variáveis e mede a detecção de mutantes.
A Sprint 4 liga requisitos aos testes e consolida as evidências da validação.

## 3. Demonstração (60 segundos)
Mostre CT01: 100 × 100 + 100 = 10100.
Mostre CT05: esperava-se -1 para o negativo, mas o original calcula 99; o caso falha.
Mostre CT02: NULL é inválido, mas o modelo retorna 100; adotamos -1 para sua rejeição.
Na RTM, relacione essas falhas a REQ-CAD03 e REQ-CAD04. Remova um teste e mostre a pendência.
Nos mutantes, mostre que trocar o zero da normalização de NULL por um é detectado por CT02.

## 4. Evidências da seleção atual (30 segundos)
Foram executados {dados['executados']} casos: {dados['pass']} PASS e {dados['fail']} FAIL,
com {dados['pendentes']} casos do plano ainda pendentes.
A cobertura de nós é {dados['cobertura_nos']:.1f}%, de arestas {dados['cobertura_arestas']:.1f}%
e de pares DU {dados['cobertura_du']:.1f}%. O resultado funcional é: {dados['veredito']}.

## 5. Conclusão e limites (20 segundos)
A ferramenta evidencia a ausência da rejeição de negativos e a conversão de NULL para zero.
O original foi preservado para auditar esses defeitos. Cobertura alta não comprova conformidade funcional.
A execução apresentada usa o modelo Python do original, sem compilar 4GL ou simular seu overflow/arredondamento.
Fonte: {dados['fonte']}; SHA-256 (LF): {dados['sha256']}.
O resultado da validação é limitado ao plano e às entradas executadas.
'''


def relatorio(dados):
    gerado = datetime.now(timezone.utc).isoformat(timespec='seconds')
    linhas = [
        '# Validação do CAD0001 — TestingStudio', f'Gerado em UTC: {gerado}',
        f"Fonte: {dados['fonte']}; SHA-256 do conteúdo com quebras LF: {dados['sha256']}.",
        f"Origem da evidência: {dados['evidencia']}.",
        f"Resultado funcional: **{dados['veredito']}**",
        f"Casos: {dados['executados']} executados, {dados['pass']} PASS, {dados['fail']} FAIL, {dados['pendentes']} pendentes.",
        f"Requisitos aprovados no plano: {dados['requisitos_aprovados']}/{len(REQUISITOS)}.",
        f"Cobertura nós: {dados['cobertura_nos']:.1f}%; arestas: {dados['cobertura_arestas']:.1f}%; DU: {dados['cobertura_du']:.1f}%.",
        'Escore de mutação: ' + ('indefinido.' if dados['escore_mutacao'] is None else f"{dados['escore_mutacao']:.1f}%."),
        '## Rastreabilidade de requisitos',
    ]
    for r in dados['matriz']:
        linhas.extend([f"### {r['Requisito']} — {r['Situação']}", r['Descrição'], r['Origem / critério'],
                       f"Casos planejados: {r['Casos planejados']}",
                       f"PASS: {r['PASS']}; FAIL: {r['FAIL']}; pendentes: {r['Pendentes']}."])
    linhas.append('## Evidências por caso')
    for t in dados['testes']:
        linhas.append(f"- {t['Caso']} ({t['Requisitos']}): entradas {t['Entradas']}; esperado {t['Esperado']}; obtido {t['Obtido']}; {t['Situação']}.")
    linhas.extend([
        '## Limites e conclusão',
        'Os identificadores REQ-CAD foram definidos para organizar as regras do CAD0001 neste projeto.',
        'Rastreabilidade indica vínculos, não aprovação automática. Requisito parcial não é aprovado.',
        'A cobertura e a mutação medem o modelo Python, enquanto PASS/FAIL compara sua saída com a especificação.',
        'A ausência da rejeição de negativos e NULL→0 foram preservadas; o código auditado não foi corrigido.',
        'O manual classifica NULL como inválido; retornar -1 para NULL é um critério adotado pelo projeto.',
        'O fonte completo contém CRUD; as métricas e testes cobrem somente sua função de cálculo.',
        'Não há execução nativa de 4GL nem teste exaustivo. Overflow e arredondamento exigem validação no runtime.',
        'O relatório Gemini da Sprint 1 é análise textual; estas evidências são de execução local.',
    ])
    return '\n\n'.join(linhas)
