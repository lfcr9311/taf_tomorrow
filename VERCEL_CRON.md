# Configuração de Cron no Vercel

O sistema está configurado para executar automaticamente no Vercel usando cron jobs.

## Configuração Atual

### Arquivo: `vercel.json`

```json
{
  "crons": [
    {
      "path": "/api/taf",
      "schedule": "30 3 * * *"
    },
    {
      "path": "/api/taf",
      "schedule": "30 9 * * *"
    },
    {
      "path": "/api/taf",
      "schedule": "30 15 * * *"
    },
    {
      "path": "/api/taf",
      "schedule": "30 21 * * *"
    },
    {
      "path": "/api/fetch-from-file-cron",
      "schedule": "0 0 * * *"
    },
    {
      "path": "/api/fetch-from-file-cron",
      "schedule": "0 6 * * *"
    },
    {
      "path": "/api/fetch-from-file-cron",
      "schedule": "0 12 * * *"
    },
    {
      "path": "/api/fetch-from-file-cron",
      "schedule": "0 18 * * *"
    }
  ]
}
```

## Cron Jobs Ativos

### 1. `/api/taf` (TAF do aeroporto padrão SBRJ)
- **03:30 UTC** - 30 3 * * *
- **09:30 UTC** - 30 9 * * *
- **15:30 UTC** - 30 15 * * *
- **21:30 UTC** - 30 21 * * *

### 2. `/api/fetch-from-file-cron` (TAFs dos aeroportos do arquivo)
- **00:00 UTC** - 0 0 * * * (Meia-noite)
- **06:00 UTC** - 0 6 * * * (6 da manhã)
- **12:00 UTC** - 0 12 * * * (Meio-dia)
- **18:00 UTC** - 0 18 * * * (6 da tarde)

## Como Funciona

### Pré-requisitos

1. **Arquivo `aeroportos.txt`** deve existir na raiz do projeto com os códigos ICAO:
```
SBRJ
SBSP
SBCT
...
```

2. **Variáveis de ambiente** configuradas no Vercel:
   - `TOMORROW_IO_API_URL`
   - `TOMORROW_IO_API_KEY`
   - `REDEMET_API_URL`
   - `REDEMET_API_KEY`
   - `DATABASE_URL` (Neon, Supabase, etc.)

### Fluxo de Execução

```
Cron dispara (a cada 6 horas)
    ↓
GET /api/fetch-from-file-cron
    ↓
Lê aeroportos.txt
    ↓
Para cada aeroporto:
    ├─ Busca TAF na Tomorrow.io
    └─ Busca TAF na REDEMET
    ↓
Salva no banco de dados
    ↓
Retorna relatório JSON
```

## Formato Cron (Vercel)

```
┌───────────── minuto (0 - 59)
│ ┌───────────── hora (0 - 23)
│ │ ┌───────────── dia do mês (1 - 31)
│ │ │ ┌───────────── mês (1 - 12)
│ │ │ │ ┌───────────── dia da semana (0 - 6, onde 0 = domingo)
│ │ │ │ │
│ │ │ │ │
0 0 * * *  → Meia-noite todos os dias

0 6 * * *  → 6 AM todos os dias

30 3 * * * → 3:30 AM todos os dias
```

## Como Modificar

Para alterar os horários, edite `vercel.json`:

**Exemplo: Executar a cada 4 horas**

```json
{
  "crons": [
    {
      "path": "/api/fetch-from-file-cron",
      "schedule": "0 0 * * *"
    },
    {
      "path": "/api/fetch-from-file-cron",
      "schedule": "0 4 * * *"
    },
    {
      "path": "/api/fetch-from-file-cron",
      "schedule": "0 8 * * *"
    },
    {
      "path": "/api/fetch-from-file-cron",
      "schedule": "0 12 * * *"
    },
    {
      "path": "/api/fetch-from-file-cron",
      "schedule": "0 16 * * *"
    },
    {
      "path": "/api/fetch-from-file-cron",
      "schedule": "0 20 * * *"
    }
  ]
}
```

## Monitorar Execução

No Vercel Dashboard:

1. Acesse seu projeto
2. Vá para **Functions** ou **Crons**
3. Veja histórico de execuções
4. Verifique logs de erro

## Resposta do Cron

```json
{
  "success": true,
  "message": "Busca concluída para 30 aeroportos",
  "summary": {
    "total_requests": 60,
    "total_success": 58,
    "total_error": 2,
    "success_rate": "96.7%"
  },
  "tomorrow": {
    "success": 29,
    "error": 1
  },
  "redemet": {
    "success": 29,
    "error": 1
  }
}
```

## Solução de Problemas

### Erro: "Arquivo não encontrado"

**Causa:** `aeroportos.txt` não está na raiz do projeto
**Solução:** 
1. Crie o arquivo `aeroportos.txt`
2. Faça commit e push para o GitHub
3. Vercel fará deploy automático

### Erro: "REDEMET_API_KEY não configurada"

**Causa:** Variável de ambiente não está definida no Vercel
**Solução:**
1. Vá para Project Settings > Environment Variables
2. Adicione: `REDEMET_API_KEY=sua_chave`
3. Redeploy

### Cron não está executando

**Verificar:**
1. Deploy foi bem-sucedido?
2. Todas as variáveis de ambiente estão configuradas?
3. O arquivo `vercel.json` está correto?
4. Há erros nos logs do Vercel?

## Deploy

Para ativar os crons:

```bash
git add vercel.json
git commit -m "Configure vercel crons for TAF fetching"
git push origin main
```

Vercel fará deploy automático e os crons começarão a executar nos horários configurados.

## Custos

- Vercel Cron é gratuito no plano Free (até 50 invocações/mês)
- Plano Pro: até 8.640 invocações/mês
- Verifique uso em: **Usage** no dashboard do Vercel

## Exemplos de Agendamentos

| Frequência | Schedule |
|-----------|----------|
| A cada hora | `0 * * * *` |
| A cada 6 horas | `0 0,6,12,18 * * *` |
| A cada 12 horas | `0 0,12 * * *` |
| Diariamente à meia-noite | `0 0 * * *` |
| Duas vezes ao dia | `0 0,12 * * *` |
| Segunda a sexta às 8 AM | `0 8 * * 1-5` |
| Mensalmente no 1º dia | `0 0 1 * *` |

## Monitoramento com Webhook

Para integrar com Slack, Discord, etc.:

```javascript
// Ao final do fetch, envie uma notificação
await fetch(process.env.WEBHOOK_URL, {
  method: 'POST',
  body: JSON.stringify({
    success: results.summary.success_rate,
    message: `TAF fetched for ${results.airports_count} airports`
  })
})
```
