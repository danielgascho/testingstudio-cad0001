import itertools
import unittest
from decimal import Decimal

from caixa_branca import ARESTAS, CASOS, NOS, cobertura, executar, esperado_especificacao, ler_valor


class CaixaBrancaTests(unittest.TestCase):
    def test_equivalencia_e_tracos(self):
        arestas = {(a, b) for a, b, _ in ARESTAS}
        for entradas in itertools.product([None, '-0.01', '0', '0.01', '100'], repeat=3):
            with self.subTest(entradas=entradas):
                normalizados = [Decimal('0') if v is None else Decimal(v) for v in entradas]
                referencia = (Decimal('-1') if min(normalizados) < 0 else
                              normalizados[0] * normalizados[1] + normalizados[2])
                resultado, caminho = executar(entradas)
                self.assertEqual(resultado, referencia)
                self.assertEqual(caminho[0], 'INICIO')
                self.assertEqual(caminho[-1], 'FIM')
                self.assertTrue(set(zip(caminho, caminho[1:])) <= arestas)

    def test_base_cobre_grafo_e_tem_caminhos_independentes(self):
        caminhos = [executar(c.entradas)[1] for c in CASOS if c.basico]
        nos, arestas = cobertura(caminhos)
        self.assertEqual(nos, set(NOS))
        self.assertEqual(arestas, {(a, b) for a, b, _ in ARESTAS})
        self.assertEqual(len(ARESTAS) - len(NOS) + 2, 7)
        # Rank dos vetores de incidência de arestas sobre GF(2).
        base = {}
        for caminho in caminhos:
            usados = set(zip(caminho, caminho[1:]))
            vetor = sum(1 << i for i, (a, b, _) in enumerate(ARESTAS) if (a, b) in usados)
            while vetor:
                piv = vetor.bit_length() - 1
                if piv not in base:
                    base[piv] = vetor
                    break
                vetor ^= base[piv]
        self.assertEqual(len(base), 7)

    def test_curto_circuito(self):
        _, caminho = executar(('-0.01', '-0.01', '-0.01'))
        self.assertNotIn('N11', caminho)
        self.assertNotIn('N12', caminho)
        _, caminho = executar(('0', '-0.01', '0'))
        self.assertIn('N11', caminho)
        self.assertNotIn('N12', caminho)

    def test_oraculo_requisito_e_divergencia_null(self):
        self.assertEqual(esperado_especificacao((None, '100', '100')), Decimal('-1'))
        self.assertEqual(executar((None, '100', '100'))[0], Decimal('100'))
        self.assertEqual(executar(('0.10', '0.20', '0.01'))[0], Decimal('0.03'))
        self.assertEqual(esperado_especificacao(('100', '100', '100')), Decimal('10100'))

    def test_validacao_e_suite_vazia(self):
        self.assertIsNone(ler_valor('NULL'))
        self.assertEqual(ler_valor('0,01'), Decimal('0.01'))
        for valor in ['', 'abc', 'NaN', 'Infinity', '0.001', '10000000000']:
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                ler_valor(valor)
        self.assertEqual(cobertura([]), (set(), set()))


if __name__ == '__main__':
    unittest.main()
