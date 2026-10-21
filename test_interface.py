import unittest
from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest


class InterfaceTests(unittest.TestCase):
    def test_cobertura_e_casos(self):
        app = AppTest.from_file('app.py', default_timeout=15).run()
        self.assertFalse(app.exception)
        self.assertEqual([m.value for m in app.metric][:4], ['4', '4', '100.0%', '100.0%'])
        app.multiselect(key='suite_branca').set_value(['CT01']).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[1].value, '1')
        self.assertNotEqual(app.metric[2].value, '100.0%')
        app.selectbox(key='grafo_branca').select('CT01').run()
        self.assertFalse(app.exception)
        app.text_input(key='branca_param_0').set_value('NULL')
        next(b for b in app.button if b.label == 'Adicionar à suíte').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[1].value, '2')
        app.multiselect(key='suite_branca').set_value([]).run()
        next(b for b in app.button if b.label == 'Limpar casos próprios').click().run()
        self.assertFalse(app.exception)
        self.assertEqual([m.value for m in app.metric][1:4], ['0', '0.0%', '0.0%'])
        app.text_area[0].set_value('fonte diferente').run()
        self.assertFalse(app.exception)
        self.assertFalse(app.metric)
        self.assertTrue(any('fonte foi alterado' in w.value for w in app.warning))

    def test_relatorio_preta_persiste_sem_chamada_externa(self):
        with patch('google.genai.Client') as cliente:
            resp = MagicMock(text='Relatório simulado para verificar persistência')
            cliente.return_value.__enter__.return_value.models.generate_content.return_value = resp
            app = AppTest.from_file('app.py', default_timeout=15).run()
            app.text_input(key='gemini_api_key').set_value('chave-teste')
            next(b for b in app.button if b.label == 'Gerar comentário com Gemini').click().run()
            self.assertFalse(app.exception)
            app.multiselect(key='suite_branca').set_value(['CT01']).run()
            self.assertTrue(any(m.value == resp.text for m in app.markdown))
            self.assertEqual(cliente.call_count, 1)
            app.text_area(key='fonte_cad0001').set_value('outro fonte').run()
            self.assertFalse(any(m.value == resp.text for m in app.markdown))
            self.assertFalse(app.metric)
            next(b for b in app.button if b.label == 'Restaurar fonte do arquivo').click().run()
            self.assertFalse(app.exception)
            self.assertTrue(any(m.value == resp.text for m in app.markdown))
            self.assertEqual(cliente.call_count, 1)

    def test_sprint3_suite_compartilhada_e_independente(self):
        app = AppTest.from_file('app.py', default_timeout=15).run()
        self.assertFalse(app.exception)
        self.assertEqual([m.value for m in app.metric][4:11], ['13', '13', '100.0%', '9', '0', '1', '100.0%'])
        app.multiselect(key='suite_branca').set_value(['CT01']).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[10].value, '55.6%')
        self.assertEqual(app.metric[5].value, '7')
        app.selectbox(key='s3_mutante').select('M09').run()
        self.assertFalse(app.exception)
        app.multiselect(key='suite_branca').set_value([]).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[10].value, '—')
        app.checkbox(key='s3_reusar').uncheck().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[10].value, '100.0%')
        app.multiselect(key='suite_s3').set_value(['CT08']).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[10].value, '0.0%')

    def test_sprint4_reprovacao_pendencias_e_compartilhamento(self):
        app = AppTest.from_file('app.py', default_timeout=15).run()
        self.assertFalse(app.exception)
        metricas = lambda: {m.label: m.value for m in app.metric}
        self.assertEqual(metricas()['Casos de validação executados'], '19')
        self.assertEqual(metricas()['PASS na validação'], '8')
        self.assertEqual(metricas()['FAIL na validação'], '11')
        self.assertEqual(metricas()['Requisitos com teste executado'], '4/4')
        self.assertEqual(metricas()['Requisitos aprovados no plano'], '2/4')
        app.multiselect(key='suite_s4').set_value(['CT01']).run()
        self.assertFalse(app.exception)
        self.assertEqual(metricas()['Casos pendentes no plano'], '18')
        self.assertEqual(metricas()['Requisitos aprovados no plano'], '0/4')
        self.assertTrue(any('incompleta' in w.value for w in app.warning))
        app.multiselect(key='suite_s4').set_value([]).run()
        self.assertFalse(app.exception)
        self.assertEqual(metricas()['Casos de validação executados'], '0')
        self.assertEqual(metricas()['Requisitos com teste executado'], '0/4')
        app.checkbox(key='s4_reusar').check().run()
        self.assertFalse(app.exception)
        self.assertEqual(metricas()['Casos de validação executados'], '4')
        self.assertEqual(metricas()['FAIL na validação'], '3')

    def test_caixa_preta_funciona_sem_gemini_e_le_o_arquivo(self):
        with patch('google.genai.Client') as cliente:
            app = AppTest.from_file('app.py', default_timeout=15).run()
            self.assertFalse(app.exception)
            self.assertIn('FUNCTION cad0001_incluir()', app.text_area(key='fonte_cad0001').value)
            tabelas = [d.value for d in app.dataframe if 'Obtido (modelo Python)' in d.value.columns]
            self.assertEqual(len(tabelas), 1)
            self.assertEqual(len(tabelas[0]), 19)
            negativo = tabelas[0].set_index('Caso').loc['CT05']
            self.assertEqual((negativo['Obtido (modelo Python)'], negativo['Situação']), ('99.00', 'FAIL'))
            cliente.assert_not_called()

    def test_caso_dependente_do_runtime_nao_e_adicionado(self):
        app = AppTest.from_file('app.py', default_timeout=15).run()
        for i, valor in enumerate(('0.01', '0.01', '0')):
            app.text_input(key=f'branca_param_{i}').set_value(valor)
        next(b for b in app.button if b.label == 'Adicionar à suíte').click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any('arredondamento' in e.value for e in app.error))
        self.assertEqual({m.label: m.value for m in app.metric}['Casos executados'], '4')


if __name__ == '__main__':
    unittest.main()
