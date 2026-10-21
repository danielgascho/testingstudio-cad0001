import unittest
from decimal import Decimal

from caixa_branca import CASOS, executar, esperado_especificacao
from caixa_preta import analisar, classes_equivalencia, pontos_avl
from fonte import Fonte, HASH_REFERENCIA, hash_conteudo, ler_fonte, modelo_compativel
from sprint4 import validar


class CaixaPretaTests(unittest.TestCase):
    def test_leitura_do_original_e_identidade(self):
        fonte = ler_fonte()
        self.assertEqual(fonte.nome, 'cad0001_item_calculo.txt')
        self.assertEqual(fonte.sha256, HASH_REFERENCIA)
        self.assertIn('FUNCTION cad0001_incluir()', fonte.codigo)
        self.assertEqual(len(fonte.codigo.splitlines()), 204)
        self.assertNotIn('RETURN -1', fonte.codigo)
        self.assertEqual(hash_conteudo(fonte.codigo.replace('\n', '\r\n')), fonte.sha256)

    def test_epsilon_e_limite_derivados_do_tipo(self):
        fonte = ler_fonte()
        self.assertEqual(fonte.decimal, (12, 2))
        self.assertEqual(fonte.epsilon, Decimal('0.01'))
        self.assertEqual(fonte.maximo, Decimal('9999999999.99'))
        outro_tipo = Fonte(fonte.codigo.replace('12,2', '14,3'), 'outro.txt')
        self.assertEqual(outro_tipo.epsilon, Decimal('0.001'))
        self.assertEqual(outro_tipo.maximo, Decimal('99999999999.999'))
        self.assertEqual(len(classes_equivalencia(fonte)), 12)
        self.assertEqual([p['Valor'] for p in pontos_avl(fonte)], [-100, -0.01, 0, 0.01, 100])

    def test_resultados_negativos_null_e_versao_da_evidencia(self):
        linhas = analisar()
        self.assertEqual((len(linhas), sum(l['Situação'] == 'PASS' for l in linhas)), (19, 8))
        caso = next(l for l in linhas if l['Caso'] == 'CT05')
        self.assertEqual((caso['Esperado (regra)'], caso['Obtido (modelo Python)'], caso['Situação']), ('-1.00', '99.00', 'FAIL'))
        self.assertTrue(all(l['SHA-256 (LF)'] == HASH_REFERENCIA for l in linhas))
        self.assertTrue(all('sem execução nativa' in l['Origem da evidência'] for l in linhas))
        self.assertEqual({c.entradas for c in CASOS if c.id in ('CT14', 'CT15', 'CT16')},
                         {('0', '100', '100'), ('100', '0', '100'), ('100', '100', '0')})

    def test_fonte_diferente_nao_recebe_metricas_da_referencia(self):
        fonte = Fonte(ler_fonte().codigo + '\n# alteração', 'cad0001_item_calculo.txt')
        self.assertFalse(modelo_compativel(fonte.codigo))
        for analisar_fonte in [lambda: analisar(fonte=fonte), lambda: validar(CASOS, fonte=fonte)]:
            with self.assertRaisesRegex(ValueError, 'fonte foi alterado'):
                analisar_fonte()

    def test_coincidencia_com_sentinela_nao_prova_rejeicao(self):
        entrada = ('-1', '2', '1')
        self.assertEqual(executar(entrada)[0], esperado_especificacao(entrada))
        # O mesmo caminho do caso válido comprova que o modelo não tem guarda de negativos.
        self.assertEqual(executar(entrada)[1], executar(('1', '2', '1'))[1])


if __name__ == '__main__':
    unittest.main()
