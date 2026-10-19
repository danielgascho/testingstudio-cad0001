import unittest
from unittest.mock import MagicMock, patch

from streamlit.testing.v1 import AppTest


class InterfaceTests(unittest.TestCase):
    def test_cobertura_e_casos(self):
        app = AppTest.from_file('app.py', default_timeout=15).run()
        self.assertFalse(app.exception)
        self.assertEqual([m.value for m in app.metric][:4], ['7', '7', '100.0%', '100.0%'])
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
            next(b for b in app.button if 'Executar Auditoria' in b.label).click().run()
            self.assertFalse(app.exception)
            app.multiselect(key='suite_branca').set_value(['CT01']).run()
            self.assertTrue(any(m.value == resp.text for m in app.markdown))
            self.assertEqual(cliente.call_count, 1)

    def test_sprint3_suite_compartilhada_e_independente(self):
        app = AppTest.from_file('app.py', default_timeout=15).run()
        self.assertFalse(app.exception)
        self.assertEqual([m.value for m in app.metric][4:11], ['25', '25', '100.0%', '9', '0', '1', '100.0%'])
        app.multiselect(key='suite_branca').set_value(['CT01']).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[10].value, '33.3%')
        self.assertEqual(app.metric[5].value, '13')
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
        self.assertEqual(app.metric[10].value, '33.3%')

    def test_sprint4_reprovacao_pendencias_e_compartilhamento(self):
        app = AppTest.from_file('app.py', default_timeout=15).run()
        self.assertFalse(app.exception)
        metricas = lambda: {m.label: m.value for m in app.metric}
        self.assertEqual(metricas()['Casos de validação executados'], '13')
        self.assertEqual(metricas()['PASS na validação'], '9')
        self.assertEqual(metricas()['FAIL na validação'], '4')
        self.assertEqual(metricas()['Requisitos com teste executado'], '4/4')
        self.assertEqual(metricas()['Requisitos aprovados no plano'], '3/4')
        app.multiselect(key='suite_s4').set_value(['CT01']).run()
        self.assertFalse(app.exception)
        self.assertEqual(metricas()['Casos pendentes no plano'], '12')
        self.assertEqual(metricas()['Requisitos aprovados no plano'], '0/4')
        self.assertTrue(any('incompleta' in w.value for w in app.warning))
        app.multiselect(key='suite_s4').set_value([]).run()
        self.assertFalse(app.exception)
        self.assertEqual(metricas()['Casos de validação executados'], '0')
        self.assertEqual(metricas()['Requisitos com teste executado'], '0/4')
        app.checkbox(key='s4_reusar').check().run()
        self.assertFalse(app.exception)
        self.assertEqual(metricas()['Casos de validação executados'], '7')
        self.assertEqual(metricas()['FAIL na validação'], '3')


if __name__ == '__main__':
    unittest.main()
