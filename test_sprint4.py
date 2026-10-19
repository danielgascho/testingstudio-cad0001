import unittest

from caixa_branca import CASOS, Caso
from sprint4 import REQUISITOS, validar, vinculos, relatorio, pitch


class Sprint4Tests(unittest.TestCase):
    def test_plano_completo_nao_mascara_falhas_com_cobertura(self):
        dados = validar(CASOS)
        self.assertEqual((dados['pass'], dados['fail'], dados['pendentes']), (9, 4, 0))
        self.assertEqual(dados['veredito'], 'Reprovado no plano')
        self.assertEqual(dados['requisitos_vinculados'], 4)
        self.assertEqual(dados['requisitos_aprovados'], 3)
        self.assertFalse(dados['orfaos'])
        self.assertEqual(dados['cobertura_nos'], 100)
        self.assertEqual(dados['cobertura_du'], 100)
        self.assertEqual(dados['escore_mutacao'], 100)
        nulos = next(r for r in dados['matriz'] if r['Requisito'] == 'REQ-CAD04')
        self.assertEqual(nulos['Situação'], 'Reprovado')
        self.assertEqual(nulos['FAIL'], 'CT02, CT03, CT04, CT09')

    def test_parcial_e_vazio_nao_aprovam_requisito(self):
        parcial = validar([CASOS[0]])
        self.assertEqual(parcial['veredito'], 'Validação incompleta')
        self.assertEqual(parcial['requisitos_aprovados'], 0)
        self.assertEqual(parcial['matriz'][0]['Situação'], 'Parcial')
        vazio = validar([])
        self.assertEqual((vazio['executados'], vazio['pendentes']), (0, 13))
        self.assertEqual(vazio['requisitos_vinculados'], 0)
        self.assertIsNone(vazio['escore_mutacao'])
        self.assertTrue(all(r['Situação'] == 'Sem execução' for r in vazio['matriz']))

    def test_rastreabilidade_reversa_e_fluxos(self):
        self.assertEqual(vinculos(('0', '2', '3')), ('REQ-CAD01', 'REQ-CAD02'))
        self.assertEqual(vinculos((None, '-1', '3')), ('REQ-CAD03', 'REQ-CAD04'))
        dados = validar(CASOS)
        for teste in dados['testes']:
            for req in teste['Requisitos'].split(', '):
                self.assertIn(req, REQUISITOS)
                matriz = next(r for r in dados['matriz'] if r['Requisito'] == req)
                self.assertIn(teste['Caso'], matriz['Casos planejados'].split(', '))
        self.assertEqual(dados['testes'][0]['Fluxo'], 'Principal')
        self.assertEqual(dados['testes'][1]['Fluxo'], 'Exceção')
        self.assertEqual(dados['testes'][7]['Fluxo'], 'Alternativo / limite')

    def test_personalizados_e_ids_repetidos(self):
        extra = Caso('EX01', 'Cálculo nominal', ('2', '3', '4'))
        dados = validar([extra])
        self.assertEqual((dados['pass'], dados['pendentes']), (1, 13))
        self.assertIn('EX01', dados['matriz'][0]['PASS'])
        with self.assertRaises(ValueError):
            validar([extra, extra])
        with self.assertRaises(ValueError):
            validar([Caso('CT01', 'Outro conteúdo', ('0', '0', '0'))])

    def test_exportacao_e_pitch_correspondem_a_selecao(self):
        dados = validar(CASOS)
        texto = relatorio(dados)
        self.assertIn('9 PASS, 4 FAIL', texto)
        self.assertIn('REQ-CAD04', texto)
        self.assertIn('CT09', texto)
        self.assertIn('sem compilar 4GL', pitch(dados))
        vazio = validar([])
        self.assertIn('indefinido', relatorio(vazio))
        self.assertIn('13 casos do plano ainda pendentes', pitch(vazio))


if __name__ == '__main__':
    unittest.main()
