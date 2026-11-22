import os
from http.client import HTTPException
from http.server import ThreadingHTTPServer
from threading import Thread
from time import sleep

from laboratorio.http_local import HandlerJSON, PORTA, registrar, requisitar


LIMITE_FEATURES = 10
INTERVALO_ATUALIZACAO = 0.05


class EstadoDoProxy:
    def __init__(self, mitigacao):
        self._mitigacao = mitigacao
        self._ultima_candidata = None
        self._ativa = None

    def aplicar(self, artefato):
        if not isinstance(artefato, dict):
            raise ValueError("Configuração precisa ser um objeto JSON")
        versao = artefato.get("versao")
        features = artefato.get("features")
        if not isinstance(versao, str) or not versao:
            raise ValueError("Versão ausente ou inválida")
        if not isinstance(features, list) or not features or not all(
            isinstance(feature, str) and feature for feature in features
        ):
            raise ValueError("Lista de features ausente ou inválida")
        candidata = (versao, tuple(features))
        if candidata == self._ultima_candidata:
            return None

        quantidade = len(features)
        excede_limite = quantidade > LIMITE_FEATURES
        if self._mitigacao and excede_limite:
            decisao = "rejeitada"
        else:
            self._ativa = (versao, 500 if excede_limite else 200)
            decisao = "limite_excedido" if excede_limite else "aplicada"
        self._ultima_candidata = candidata
        return {
            "candidata": versao,
            "features": quantidade,
            "limite": LIMITE_FEATURES,
            "decisao": decisao,
            "ativa": self.resposta()[1]["versao"],
        }

    def resposta(self):
        ativa = self._ativa
        if ativa is None:
            return 503, {"versao": None}
        versao, status = ativa
        return status, {"versao": versao}


def acompanhar_publicador(estado):
    while True:
        try:
            status, artefato = requisitar("publicador", "/config")
            if status != 200:
                raise ValueError(f"Publicador retornou HTTP {status}")
            decisao = estado.aplicar(artefato)
            if decisao is not None:
                registrar("proxy", "atualizacao", **decisao)
        except (OSError, HTTPException, ValueError) as erro:
            registrar("proxy", "erro_de_leitura", erro=str(erro))
        sleep(INTERVALO_ATUALIZACAO)


def main():
    modo = os.environ.get("MODO", "sem-mitigacao")
    if modo not in {"sem-mitigacao", "com-mitigacao"}:
        raise SystemExit("MODO deve ser sem-mitigacao ou com-mitigacao")
    estado = EstadoDoProxy(mitigacao=modo == "com-mitigacao")

    class Handler(HandlerJSON):
        def do_GET(self):
            if self.path == "/":
                self.responder(*estado.resposta())
            else:
                self.responder(404, {"erro": "rota desconhecida"})

    with ThreadingHTTPServer(("0.0.0.0", PORTA), Handler) as servidor:
        registrar("proxy", "inicio", modo=modo)
        Thread(target=acompanhar_publicador, args=(estado,), daemon=True).start()
        servidor.serve_forever()


if __name__ == "__main__":
    main()
