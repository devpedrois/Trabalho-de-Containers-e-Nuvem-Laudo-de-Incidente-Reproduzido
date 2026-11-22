# Registro de uso de IA

A equipe definiu o escopo e revisou a documentação. Usamos o Codex para apoiar a leitura do artigo. Ele também auxiliou no código, nos testes e no laudo. A equipe comparou a documentação com a rubrica do Classroom. Também pedimos a conferência das medições e das citações.

### 1. Fazer a atividade em um projeto independente

Pedido inicial:

> Temosuma atividade de FCCPD sobre Containers e Nuvem. Preciso de um laboratório independente do projeto de origem.

Mantivemos o laboratório independente, como solicitado. Adotamos Python pela simplicidade da biblioteca padrão. A Parte D avalia o próprio laboratório.

### 2. Escolher o incidente e reproduzir a falha

Orientação do enunciado sobre o mecanismo da falha.

> Use os prints do Classroom para ter contexto e o link dou Cloudflare enviado. Auxilie na montagem(nao faça tudo) do Docker Compose. Queremos ajuda para enxergar o mecanismo da falha durante a execução.

Adotamos o caso da Cloudflare. Usamos listas sintéticas para representar as entradas duplicadas. A miniatura começa na publicação do arquivo de configuração.

### 3. Medir o impacto e testar a mitigação

Orientação das partes C e D do enunciado.

> Execute a miniatura com e sem mitigação. Meça o tempo até a falha e até a recuperação e refaça os testes. Registre a taxa de erro em cada execução. Use os logs brutos para sustentar os números do laudo.

Adotamos a mesma sequência nos dois cenários. Na mitigação, preservamos a última configuração válida. Descartamos o primeiro retorno como marco da recuperação estável.

## Erros encontrados ao executar e correções

As falhas abaixo apareceram durante a validação no Docker. O Codex auxiliou na correção e na verificação. A equipe revisou o registro dos problemas.

### Configuração corrigida com a mesma versão

O proxy comparava apenas o identificador da versão. Um teste corrigiu o conteúdo mantendo o mesmo identificador. A resposta continuou em HTTP 500. A comparação passou a incluir a versão e o conteúdo. O teste confirmou o retorno para HTTP 200. [Falha observada](logs/regressoes-antes.log#L25) · [Teste após a correção](logs/regressoes-depois.log#L11)

### Coleta incompleta tratada como válida

O analisador retornava sucesso ao ler um log interrompido. Agora exige início, todas as amostras e um resumo coerente. O teste confirmou a rejeição do arquivo incompleto. [Falha observada](logs/regressoes-antes.log#L17) · [Teste após a correção](logs/regressoes-depois.log#L2)

### Encerramento forçado dos serviços

Os servidores Python rodavam como PID 1. O encerramento inicial registrou código `137` nos dois servidores. Configuramos `init: true` para encaminhar o sinal de término. A rodada seguinte registrou código `143`, correspondente ao SIGTERM. [Encerramento inicial](logs/encerramento-inicial.log) · [Encerramento após a correção](logs/encerramento-corrigido.log)

## Conferência das evidências

Os números experimentais vieram das duas execuções finais. A linha 127 de cada log registra o resumo. Os tempos em segundos foram convertidos dos registros em milissegundos. [Sem mitigação](logs/sem-mitigacao.log#L127) · [Com mitigação](logs/com-mitigacao.log#L127)

Conferimos o mecanismo e os horários no artigo oficial. A abertura registra falhas de rede às 11:20 UTC. A cronologia aponta erros HTTP de clientes às 11:28 UTC. A seção *Memory preallocation* registra o limite de 200 features. [Post-mortem da Cloudflare](https://blog.cloudflare.com/18-november-2025-outage/)
