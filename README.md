# FCCPD · Incidente da Cloudflare

Laboratório independente em Python e Docker Compose. Reproduz o efeito de um arquivo de configuração duplicado. O proxy fica indisponível quando excede seu limite. A mitigação rejeita o arquivo e preserva a versão válida. [Post-mortem da Cloudflare](https://blog.cloudflare.com/18-november-2025-outage/)

[Laudo em PDF](output/pdf/Laudo-FCCPD-Cloudflare.pdf) · [Registro de uso de IA](IA.md)

## Reproduzir

Use o Docker com o plugin Compose e containers Linux. Execute os comandos a partir da raiz deste repositório. A imagem usa a biblioteca padrão do Python. Os três serviços se comunicam em redes internas.

### PowerShell

```powershell
docker compose build publicador

$env:MODO = 'sem-mitigacao'
docker compose -p fccpd-sem up --no-build --exit-code-from sonda
docker compose -p fccpd-sem logs --no-color --no-log-prefix |
    Out-File -Encoding utf8 -NoClobber logs/reexecucao-sem.log
docker compose -p fccpd-sem down

$env:MODO = 'com-mitigacao'
docker compose -p fccpd-com up --no-build --exit-code-from sonda
docker compose -p fccpd-com logs --no-color --no-log-prefix |
    Out-File -Encoding utf8 -NoClobber logs/reexecucao-com.log
docker compose -p fccpd-com down
```

### Bash, Zsh ou WSL

```bash
docker compose build publicador

MODO=sem-mitigacao docker compose -p fccpd-sem up --no-build --exit-code-from sonda
docker compose -p fccpd-sem logs --no-color --no-log-prefix > logs/reexecucao-sem.log
docker compose -p fccpd-sem down

MODO=com-mitigacao docker compose -p fccpd-com up --no-build --exit-code-from sonda
docker compose -p fccpd-com logs --no-color --no-log-prefix > logs/reexecucao-com.log
docker compose -p fccpd-com down
```

Cada execução termina quando a sonda conclui a coleta. Salve os logs antes de executar `down`. Use nomes de arquivos novos ao repetir os comandos. Uma sonda encerrada com código diferente de zero indica execução incompleta.

## Ler os resultados

| Log bruto citado | Conteúdo esperado |
| --- | --- |
| [`logs/sem-mitigacao.log`](logs/sem-mitigacao.log) | Sequência HTTP 200, 500, 200, 500 e 200. |
| [`logs/com-mitigacao.log`](logs/com-mitigacao.log) | Duas atualizações rejeitadas e todas as respostas HTTP 200. |

Cada log contém publicações, decisões do proxy e respostas observadas. O campo `t_ms` mede o tempo desde o início da sonda até a resposta. O evento `resumo` agrega apenas as requisições à rota `/`. As verificações de saúde e publicações ficam fora do denominador.

- **Falha** é a primeira resposta diferente de HTTP 200. O status `0` identifica falha de comunicação ou leitura da resposta.
- **Recuperação estável** é o primeiro sucesso após o último erro, confirmado até o fim da janela. O primeiro sucesso intermediário é registrado separadamente.
- **Taxa de erro** é o número de erros dividido pelas requisições da janela. `null` indica um marco ausente.

Com Python instalado, confira os totais pelos registros individuais. O comando recusa logs incompletos ou com resumo divergente.

```text
python -m laboratorio.metricas logs/sem-mitigacao.log logs/com-mitigacao.log
python -m unittest discover -s tests -v
```

O intervalo entre consultas pode alterar o instante observado. Use os logs da sua execução para obter os números.
