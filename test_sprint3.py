import unittest
from decimal import Decimal
from itertools import product

from caixa_branca import CASOS, executar
from sprint3 import ParDU, UNIVERSO_DU, analisar_du, analisar_mutacao, executar_mutante, pares_do_caminho


class Sprint3Tests(unittest.TestCase):
    def test_universo_e_base_du(self):
        self.assertEqual(len(UNIVERSO_DU), 13)
        cobertura = analisar_du([c for c in CASOS if c.basico])
        self.assertTrue(all(cobertura.values()))
        self.assertFalse(any(analisar_du([]).values()))
        self.assertIn(ParDU('p_val1', 'INICIO', 'N1 → N2', 'p-uso'), UNIVERSO_DU)
        self.assertIn(ParDU('p_val1', 'N2', 'N7', 'c-uso'), UNIVERSO_DU)

    def test_du_redefinicao_dos_parametros_null(self):
        pares = pares_do_caminho(executar((None, '100', '100'))[1])
        self.assertIn(ParDU('p_val1', 'N2', 'N7', 'c-uso'), pares)
        self.assertNotIn(ParDU('p_val1', 'INICIO', 'N7', 'c-uso'), pares)
        pares = pares_do_caminho(executar(('-1', '100', '100'))[1])
        self.assertIn(ParDU('p_val1', 'INICIO', 'N7', 'c-uso'), pares)
        self.assertIn(ParDU('p_val1', 'INICIO', 'N1 → N3', 'p-uso'), pares)

    def test_universo_nao_omite_pares_em_outros_valores(self):
        outros = set()
        for entrada in product((None, '-100', '-1', '0', '1', '100'), repeat=3):
            outros.update(pares_do_caminho(executar(entrada)[1]))
        self.assertEqual(outros, set(UNIVERSO_DU))

    def test_mutantes_com_saidas_conhecidas(self):
        cenarios = [
            ('M01', ('2', '3', '4'), '9'), ('M02', ('2', '3', '4'), '2'),
            ('M03', (None, '2', '3'), '5'), ('M04', ('2', None, '3'), '5'),
            ('M05', ('2', '3', None), '7'), ('M06', ('2', '3', '4'), '6'),
            ('M07', ('2', '3', '4'), '12'), ('M08', ('-1', '2', '3'), '0'),
            ('M09', ('2', '3', '4'), '10'), ('M10', ('2', '3', '4'), '24'),
        ]
        for id_mutante, entrada, esperado in cenarios:
            with self.subTest(mutante=id_mutante):
                self.assertEqual(executar_mutante(entrada, id_mutante), Decimal(esperado))
        with self.assertRaises(ValueError):
            executar_mutante(('1', '2', '3'), 'inexistente')

    def test_escore_e_sobrevivente_nao_equivalente(self):
        resumo, matriz, escore = analisar_mutacao([CASOS[0]])
        self.assertAlmostEqual(escore, 500 / 9)
        self.assertEqual(len(matriz), 10)
        self.assertEqual(resumo[2]['Situação'], 'Sobrevivente')
        resumo, matriz, escore = analisar_mutacao([c for c in CASOS if c.basico])
        self.assertEqual(escore, 100)
        self.assertEqual(sum(r['Situação'] == 'Morto' for r in resumo), 9)
        resumo, matriz, escore = analisar_mutacao([])
        self.assertIsNone(escore)
        self.assertFalse(matriz)
        self.assertEqual(sum(r['Situação'] == 'Não executado' for r in resumo), 9)

    def test_equivalente_e_oraculo_original(self):
        for entrada in product((None, '-1', '0', '1', '100'), repeat=3):
            self.assertEqual(executar_mutante(entrada, 'M09'), executar(entrada)[0])
        _, matriz, _ = analisar_mutacao([CASOS[1]])
        m03 = next(r for r in matriz if r['Mutante'] == 'M03')
        self.assertEqual(m03['Original'], '100.00')
        self.assertEqual(m03['Mutante obtido'], '200.00')
        self.assertTrue(m03['Detectou alteração'])


if __name__ == '__main__':
    unittest.main()
