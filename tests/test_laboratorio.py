import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from laboratorio.metricas import resumir
from laboratorio.proxy import EstadoDoProxy
from laboratorio.publicador import Publicador


class PublicacaoTest(unittest.TestCase):
    def test_artefato_duplicado_repete_as_entradas(self):
        publicador = Publicador()
        inicial = publicador.atual()
        duplicada = publicador.publicar("duplicada")

        self.assertEqual(len(inicial["features"]), 6)
        self.assertEqual(len(duplicada["features"]), 12)
        self.assertEqual(duplicada["features"][:6], inicial["features"])
        self.assertEqual(duplicada["features"][6:], inicial["features"])
        self.assertEqual(publicador.atual(), duplicada)

    def test_publicacao_desconhecida_preserva_a_versao_ativa(self):
        publicador = Publicador()

        with self.assertRaises(KeyError):
            publicador.publicar("desconhecida")

        self.assertEqual(publicador.atual()["versao"], "inicial")


class ProxyTest(unittest.TestCase):
    def setUp(self):
        self.valida = {"versao": "inicial", "features": ["sinal"] * 6}
        self.invalida = {"versao": "duplicada", "features": ["sinal"] * 12}
        self.restaurada = {"versao": "restaurada", "features": ["sinal"] * 6}

    def test_aguarda_primeira_configuracao(self):
        proxy = EstadoDoProxy(mitigacao=True)

        self.assertEqual(proxy.resposta()[0], 503)

    def test_sem_mitigacao_falha_ate_receber_versao_valida(self):
        proxy = EstadoDoProxy(mitigacao=False)
        proxy.aplicar(self.valida)
        proxy.aplicar(self.invalida)

        self.assertEqual(proxy.resposta(), (500, {"versao": "duplicada"}))

        proxy.aplicar(self.restaurada)

        self.assertEqual(proxy.resposta(), (200, {"versao": "restaurada"}))

    def test_mitigacao_retem_a_ultima_versao_valida(self):
        proxy = EstadoDoProxy(mitigacao=True)
        proxy.aplicar(self.valida)
        evento = proxy.aplicar(self.invalida)

        self.assertEqual(proxy.resposta(), (200, {"versao": "inicial"}))
        self.assertEqual(evento["decisao"], "rejeitada")
        self.assertEqual(evento["ativa"], "inicial")

        proxy.aplicar(self.restaurada)

        self.assertEqual(proxy.resposta(), (200, {"versao": "restaurada"}))

    def test_aceita_arquivo_no_limite(self):
        proxy = EstadoDoProxy(mitigacao=True)
        proxy.aplicar({"versao": "limite", "features": ["sinal"] * 10})

        self.assertEqual(proxy.resposta(), (200, {"versao": "limite"}))

    def test_revalida_conteudo_corrigido_com_a_mesma_versao(self):
        proxy = EstadoDoProxy(mitigacao=False)
        proxy.aplicar(self.invalida)
        proxy.aplicar({"versao": "duplicada", "features": ["sinal"] * 6})

        self.assertEqual(proxy.resposta(), (200, {"versao": "duplicada"}))

    def test_recusa_estrutura_invalida_sem_perder_estado(self):
        proxy = EstadoDoProxy(mitigacao=False)
        proxy.aplicar(self.valida)

        with self.assertRaises(ValueError):
            proxy.aplicar({"versao": "invalida", "features": "texto"})

        self.assertEqual(proxy.resposta(), (200, {"versao": "inicial"}))


class MetricasTest(unittest.TestCase):
    def test_distingue_melhora_temporaria_de_recuperacao(self):
        resultado = resumir([
            {"t_ms": 0, "status": 200},
            {"t_ms": 100, "status": 500},
            {"t_ms": 200, "status": 200},
            {"t_ms": 300, "status": 500},
            {"t_ms": 400, "status": 200},
            {"t_ms": 500, "status": 200},
        ])

        self.assertEqual(resultado["requisicoes"], 6)
        self.assertEqual(resultado["erros"], 2)
        self.assertEqual(resultado["percentual_erros"], 33.33)
        self.assertEqual(resultado["primeiro_erro_ms"], 100)
        self.assertEqual(resultado["primeiro_retorno_ms"], 200)
        self.assertEqual(resultado["recuperacao_estavel_ms"], 400)
        self.assertEqual(resultado["intervalo_ate_recuperacao_ms"], 300)

    def test_sem_erro_nao_inventa_marco_de_recuperacao(self):
        resultado = resumir([{"t_ms": 0, "status": 200}])

        self.assertEqual(resultado["percentual_erros"], 0.0)
        self.assertIsNone(resultado["primeiro_erro_ms"])
        self.assertIsNone(resultado["recuperacao_estavel_ms"])

    def test_janela_encerrada_com_erro_nao_esta_recuperada(self):
        resultado = resumir([{"t_ms": 0, "status": 500}])

        self.assertEqual(resultado["percentual_erros"], 100.0)
        self.assertIsNone(resultado["recuperacao_estavel_ms"])

    def test_rejeita_janela_vazia(self):
        with self.assertRaises(ValueError):
            resumir([])


class LogTest(unittest.TestCase):
    def analisar(self, registros):
        with TemporaryDirectory() as diretorio:
            arquivo = Path(diretorio) / "sonda.log"
            arquivo.write_text("\n".join(json.dumps(registro) for registro in registros),
                               encoding="utf-8")
            return subprocess.run([sys.executable, "-m", "laboratorio.metricas", str(arquivo)],
                                  capture_output=True, text=True, check=False)

    def test_log_interrompido_nao_produz_taxa_de_erros(self):
        resultado = self.analisar([
            {"servico": "sonda", "evento": "inicio", "amostras": 2},
            {"servico": "sonda", "evento": "sondagem", "amostra": 0, "t_ms": 0, "status": 200},
        ])

        self.assertEqual(resultado.returncode, 1)
        self.assertEqual(resultado.stdout, "")

    def test_log_completo_recalcula_percentual_pelas_amostras(self):
        resultado = self.analisar([
            {"servico": "sonda", "evento": "inicio", "amostras": 2},
            {"servico": "sonda", "evento": "sondagem", "amostra": 0, "t_ms": 10, "status": 200},
            {"servico": "sonda", "evento": "sondagem", "amostra": 1, "t_ms": 20, "status": 500},
            {"servico": "sonda", "evento": "resumo", "requisicoes": 2, "erros": 1,
             "percentual_erros": 50.0, "primeiro_erro_ms": 20, "primeiro_retorno_ms": None,
             "recuperacao_estavel_ms": None, "intervalo_ate_recuperacao_ms": None,
             "amostras_finais_ok": 0},
        ])

        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(json.loads(resultado.stdout)["percentual_erros"], 50.0)
