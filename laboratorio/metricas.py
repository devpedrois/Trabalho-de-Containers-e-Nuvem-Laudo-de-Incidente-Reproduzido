import argparse
import json
from pathlib import Path


def resumir(sondagens):
    if not sondagens:
        raise ValueError("Nenhuma sondagem encontrada")

    erros = [indice for indice, sonda in enumerate(sondagens) if sonda["status"] != 200]
    total = len(sondagens)
    primeiro_erro = primeiro_retorno = recuperacao = duracao = None
    finais_ok = total
    if erros:
        primeiro_erro = sondagens[erros[0]]["t_ms"]
        primeiro_retorno = next((sonda["t_ms"] for sonda in sondagens[erros[0] + 1:]
                                if sonda["status"] == 200), None)
        finais_ok = total - erros[-1] - 1
        if finais_ok:
            recuperacao = sondagens[erros[-1] + 1]["t_ms"]
            duracao = recuperacao - primeiro_erro

    return {
        "requisicoes": total,
        "erros": len(erros),
        "percentual_erros": round(100 * len(erros) / total, 2),
        "primeiro_erro_ms": primeiro_erro,
        "primeiro_retorno_ms": primeiro_retorno,
        "recuperacao_estavel_ms": recuperacao,
        "intervalo_ate_recuperacao_ms": duracao,
        "amostras_finais_ok": finais_ok,
    }


def conferir_execucao(registros):
    eventos = [registro for registro in registros if registro["servico"] == "sonda"]
    inicios = [evento for evento in eventos if evento["evento"] == "inicio"]
    resumos = [evento for evento in eventos if evento["evento"] == "resumo"]
    sondagens = [evento for evento in eventos if evento["evento"] == "sondagem"]
    if len(inicios) != 1 or len(resumos) != 1:
        raise ValueError("Esperado um único início e um único resumo da sonda")
    if inicios[0]["amostras"] != len(sondagens) or any(
        indice != amostra["amostra"] for indice, amostra in enumerate(sondagens)
    ):
        raise ValueError("Sequência de amostras incompleta ou duplicada")

    instante_anterior = -1
    for amostra in sondagens:
        instante = amostra["t_ms"]
        status = amostra["status"]
        if type(instante) is not int or instante < instante_anterior or instante < 0:
            raise ValueError("Timestamps inválidos ou fora de ordem")
        if type(status) is not int or (status != 0 and not 100 <= status <= 599):
            raise ValueError("Status de sondagem inválido")
        instante_anterior = instante

    resultado = resumir(sondagens)
    if any(resumos[0][campo] != valor for campo, valor in resultado.items()):
        raise ValueError("Resumo diverge das amostras registradas")
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Recalcula as métricas dos logs do Compose.")
    parser.add_argument("logs", type=Path, nargs="+")
    argumentos = parser.parse_args()
    for arquivo in argumentos.logs:
        try:
            with arquivo.open(encoding="utf-8-sig") as log:
                registros = [json.loads(linha) for linha in log if linha.strip()]
            print(json.dumps({"arquivo": str(arquivo), **conferir_execucao(registros)}))
        except (OSError, KeyError, TypeError, ValueError) as erro:
            parser.exit(1, f"{arquivo}: {erro}\n")


if __name__ == "__main__":
    main()
