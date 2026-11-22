import os
from http.client import HTTPException
from time import perf_counter, sleep

from laboratorio.http_local import registrar, requisitar
from laboratorio.metricas import resumir


TOTAL_AMOSTRAS = 110
INTERVALO = 0.1
PUBLICACOES = {
    20: "duplicada",
    40: "intermediaria",
    60: "duplicada-final",
    90: "restaurada",
}


def executar():
    inicio = perf_counter()
    registrar("sonda", "inicio", modo=os.environ.get("MODO", "sem-mitigacao"),
              amostras=TOTAL_AMOSTRAS, intervalo_ms=round(INTERVALO * 1000))
    sondagens = []
    for amostra in range(TOTAL_AMOSTRAS):
        atraso = inicio + amostra * INTERVALO - perf_counter()
        if atraso > 0:
            sleep(atraso)

        if amostra in PUBLICACOES:
            versao = PUBLICACOES[amostra]
            status, artefato = requisitar("publicador", f"/publicar/{versao}", metodo="POST")
            if status != 200 or artefato["versao"] != versao:
                raise ValueError(f"Publicação de {versao} não confirmada")
            registrar("sonda", "publicacao_confirmada", amostra=amostra,
                      t_ms=round((perf_counter() - inicio) * 1000), versao=versao,
                      features=len(artefato["features"]))

        try:
            status, corpo = requisitar("proxy", "/")
        except (OSError, HTTPException, ValueError) as erro:
            status, corpo = 0, {"versao": None, "erro": str(erro)}
        registro = {"amostra": amostra, "t_ms": round((perf_counter() - inicio) * 1000),
                    "status": status, "versao": corpo["versao"]}
        if "erro" in corpo:
            registro["erro"] = corpo["erro"]
        sondagens.append(registro)
        registrar("sonda", "sondagem", **registro)

    registrar("sonda", "resumo", **resumir(sondagens))


def main():
    try:
        executar()
    except (OSError, HTTPException, KeyError, ValueError) as erro:
        registrar("sonda", "experimento_interrompido", erro=str(erro))
        raise SystemExit(1) from erro


if __name__ == "__main__":
    main()
