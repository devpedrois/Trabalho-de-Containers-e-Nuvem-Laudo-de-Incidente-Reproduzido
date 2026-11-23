# Parte D · Laboratório FCCPD

## Parecer

A falha pode ocorrer no proxy da miniatura. O publicador fornece listas com entradas duplicadas. Cada lista inválida tem 12 entradas. O proxy aceita até 10. [Arquivo de publicação](../../../laboratorio/publicador.py#L7-L14) · [Registro da primeira atualização](../../../logs/sem-mitigacao.log#L5)

## Trecho no proxy

O tamanho da configuração determina o estado da rota `GET /`. Com a mitigação desabilitada, o proxy ativa a candidata acima do limite. Esse estado devolve HTTP 500. [Validação e ativação](../../../laboratorio/proxy.py#L35-L41) · [Resposta na rota](../../../laboratorio/proxy.py#L79-L84)

```python
excede_limite = quantidade > LIMITE_FEATURES
if self._mitigacao and excede_limite:
    decisao = "rejeitada"
else:
    self._ativa = (versao, 500 if excede_limite else 200)
```

## Mitigação medida

O modo mitigado rejeita a candidata antes de ativá-la. A versão válida permanece atendendo às requisições. As duas execuções receberam a mesma sequência de publicações. [Rejeições no proxy](../../../logs/com-mitigacao.log#L6)

| Cenário | Requisições | Erros | Taxa | Evidência |
| --- | ---: | ---: | ---: | --- |
| Sem mitigação | 110 | 50 | 45,45% | [Resumo da execução](../../../logs/sem-mitigacao.log#L127) |
| Com mitigação | 110 | 0 | 0,00% | [Resumo da execução](../../../logs/com-mitigacao.log#L127) |

Sem mitigação, o primeiro erro ocorreu aos 2,101 s. A recuperação estável ocorreu aos 9,101 s. Os tempos contam desde o início da sonda. [Resumo sem mitigação](../../../logs/sem-mitigacao.log#L127)
