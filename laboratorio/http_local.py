import json
from contextlib import closing
from datetime import datetime, timezone
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler
from threading import Lock


PORTA = 8080
LIMITE_RESPOSTA = 65_536
_saida = Lock()


def requisitar(host, caminho, metodo="GET"):
    with closing(HTTPConnection(host, PORTA, timeout=1)) as conexao:
        conexao.request(metodo, caminho)
        resposta = conexao.getresponse()
        corpo = resposta.read(LIMITE_RESPOSTA + 1)
        if len(corpo) > LIMITE_RESPOSTA:
            raise ValueError("Resposta maior que o limite do laboratório")
        return resposta.status, json.loads(corpo)


def registrar(servico, evento, **dados):
    registro = {
        "utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "servico": servico,
        "evento": evento,
        **dados,
    }
    with _saida:
        print(json.dumps(registro, ensure_ascii=False), flush=True)


class HandlerJSON(BaseHTTPRequestHandler):
    def responder(self, status, dados):
        corpo = json.dumps(dados).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, formato, *argumentos):
        pass
