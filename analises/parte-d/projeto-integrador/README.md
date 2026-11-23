# Parte D · Projeto Integrador

O parecer usa a versão publicada do marketplace Origem. A revisão analisada é `a767863`. [Commit no GitHub](https://github.com/devpedrois/Projeto-Integrador/commit/a7678633f085db3d9acf820b73267438aea34ea0)

## Risco na inicialização da API

**Sim. Uma configuração interna fora do limite pode impedir a inicialização.** A variável `RECOMENDACAO_TIMEOUT_MS` configura o tempo limite da recomendação. Ela faz parte do esquema de toda a API. O limite superior é 5.000 ms. [Esquema de configuração](https://github.com/devpedrois/Projeto-Integrador/blob/a7678633f085db3d9acf820b73267438aea34ea0/backend/src/config/environment.ts#L34-L39)

```ts
RECOMENDACAO_TIMEOUT_MS: z.coerce
  .number()
  .int()
  .min(100)
  .max(5000)
  .default(800),
```

`parseEnvironment` lança um erro quando a configuração é inválida. `startServer` chama essa validação antes de `app.listen`. A instância candidata, portanto, pode falhar antes de servir HTTP. O ponto de acoplamento é a inicialização compartilhada da API. [Validação](https://github.com/devpedrois/Projeto-Integrador/blob/a7678633f085db3d9acf820b73267438aea34ea0/backend/src/config/environment.ts#L124-L138) · [Validação antes da escuta HTTP](https://github.com/devpedrois/Projeto-Integrador/blob/a7678633f085db3d9acf820b73267438aea34ea0/backend/src/server.ts#L17-L49) · [Tratamento da falha de inicialização](https://github.com/devpedrois/Projeto-Integrador/blob/a7678633f085db3d9acf820b73267438aea34ea0/backend/src/server.ts#L68-L80)

Na Cloudflare, o limite foi excedido durante o atendimento. No Origem, esse trecho atua na inicialização da instância. Ambos ligam a disponibilidade a uma configuração interna. [Post-mortem da Cloudflare](https://blog.cloudflare.com/18-november-2025-outage/)

## Proteção durante o atendimento

O cliente de recomendações valida até oito identificadores por resposta. Uma resposta acima do limite é rejeitada. O serviço trata esse erro com o fallback local. A recuperação depende de o fallback obter seus dados. [Limite da resposta](https://github.com/devpedrois/Projeto-Integrador/blob/a7678633f085db3d9acf820b73267438aea34ea0/backend/src/integrations/recommendation/http-recomendacao.client.ts#L11-L14) · [Rejeição da resposta](https://github.com/devpedrois/Projeto-Integrador/blob/a7678633f085db3d9acf820b73267438aea34ea0/backend/src/integrations/recommendation/http-recomendacao.client.ts#L55-L71) · [Fallback no serviço](https://github.com/devpedrois/Projeto-Integrador/blob/a7678633f085db3d9acf820b73267438aea34ea0/backend/src/services/recomendacao.service.ts#L27-L45)

## Decisão para a diretoria

Valide a configuração antes de promover uma versão. Preserve a versão em serviço durante a validação. O parecer sobre o Origem vem do código publicado. A medição antes e depois foi feita no laboratório. [Resultados da miniatura](../laboratorio/README.md#mitigação-medida)
