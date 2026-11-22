from http.server import ThreadingHTTPServer
from threading import Lock

from laboratorio.http_local import HandlerJSON, PORTA, registrar


SINAIS = tuple(f"sinal-{numero}" for numero in range(1, 7))
VERSOES = {
    "inicial": SINAIS,
    "duplicada": SINAIS * 2,
    "intermediaria": SINAIS,
    "duplicada-final": SINAIS * 2,
    "restaurada": SINAIS,
}


class Publicador:
    def __init__(self):
        self._versao = "inicial"
        self._mudanca = Lock()

    def atual(self):
        versao = self._versao
        return {"versao": versao, "features": list(VERSOES[versao])}

    def publicar(self, versao):
        with self._mudanca:
            features = list(VERSOES[versao])
            self._versao = versao
            return {"versao": versao, "features": features}


def registrar_publicacao(artefato):
    registrar("publicador", "publicacao", versao=artefato["versao"],
              features=len(artefato["features"]))


def main():
    publicador = Publicador()

    class Handler(HandlerJSON):
        def do_GET(self):
            if self.path != "/config":
                self.responder(404, {"erro": "rota desconhecida"})
                return
            self.responder(200, publicador.atual())

        def do_POST(self):
            prefixo, _, versao = self.path.rpartition("/")
            if prefixo != "/publicar" or versao not in VERSOES:
                self.responder(404, {"erro": "versão desconhecida"})
                return
            artefato = publicador.publicar(versao)
            registrar_publicacao(artefato)
            self.responder(200, artefato)

    with ThreadingHTTPServer(("0.0.0.0", PORTA), Handler) as servidor:
        registrar_publicacao(publicador.atual())
        servidor.serve_forever()


if __name__ == "__main__":
    main()
