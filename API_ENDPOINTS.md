# API Endpoints - TAF Service

Referência completa dos endpoints disponíveis na API.

## Base URL
```
https://seu-dominio.vercel.app
```

## Endpoints

### Health Check

#### GET `/`
Status geral da API

**Resposta:**
```json
{
  "status": "ok",
  "message": "TAF API - Vercel Cron Active"
}
```

#### GET `/health`
Verificação de saúde detalhada

**Resposta:**
```json
{
  "status": "healthy",
  "service": "taf-service"
}
```

---

### TAF - Consultas Simples

#### GET `/taf/single`
Busca TAF do aeroporto padrão (SBRJ) na Tomorrow.io

**Resposta (Sucesso):**
```json
{
  "success": true,
  "message": "TAF obtido com sucesso",
  "data": {
    "timestamp": "2024-07-13T10:30:45.123456+00:00",
    "status": "sucesso",
    "location": "SBRJ",
    "status_code": 200,
    "data": {...},
    "database_id": 1
  }
}
```

#### GET `/taf/history`
Lista os últimos TAFs salvos no banco de dados

**Parâmetros:**
- `limit` (opcional): quantidade de registros (padrão: 10)

**Exemplo:**
```
GET /taf/history?limit=5
```

**Resposta:**
```json
{
  "success": true,
  "count": 5,
  "data": [
    {
      "id": 5,
      "timestamp": "2024-07-13T07:11:34Z",
      "taf_data": "TAF SBRJ ...",
      "created_at": "2024-07-13T07:12:00Z"
    }
  ]
}
```

---

### TAF - Provedores

#### GET `/taf/providers/tomorrow`
Busca TAF de 30 aeroportos da API Tomorrow.io

**Resposta:**
```json
{
  "success": true,
  "provider": "tomorrow.io",
  "total_airports": 30,
  "success": 28,
  "error": 2,
  "results": [...]
}
```

#### GET `/taf/providers/redemet`
Busca TAF de 30 aeroportos da API REDEMET

**Resposta:**
```json
{
  "success": true,
  "provider": "redemet",
  "total_airports": 30,
  "success": 28,
  "error": 2,
  "results": [...]
}
```

---

### TAF - Batch Processing

#### GET `/taf/batch`
Busca TAF de ambas as APIs (Tomorrow.io + REDEMET) para 30 aeroportos

**Resposta:**
```json
{
  "success": true,
  "message": "Busca concluída em ambas as APIs",
  "total_airports": 60,
  "providers": {
    "tomorrow": {
      "success": 28,
      "error": 2
    },
    "redemet": {
      "success": 29,
      "error": 1
    }
  },
  "results": {
    "tomorrow": [...],
    "redemet": [...]
  }
}
```

---

### TAF - De Arquivo

#### GET `/taf/file`
Busca TAF de aeroportos listados em um arquivo .txt

**Parâmetros:**
- `file_path` (obrigatório): caminho do arquivo .txt

**Exemplo:**
```
GET /taf/file?file_path=aeroportos.txt
```

**Resposta:**
```json
{
  "success": true,
  "message": "Busca concluída para 30 aeroportos",
  "data": {
    "airports_count": 30,
    "tomorrow": {
      "success": 28,
      "error": 2,
      "results": [...]
    },
    "redemet": {
      "success": 29,
      "error": 1,
      "results": [...]
    },
    "summary": {
      "total_requests": 60,
      "total_success": 57,
      "total_error": 3,
      "success_rate": "95.0%"
    }
  }
}
```

---

### TAF - Cron Job

#### GET `/taf/cron/fetch`
Endpoint para execução automática via Vercel Cron
Procura automaticamente por `aeroportos.txt` na raiz do projeto

**Nota:** Este endpoint é chamado automaticamente pelo Vercel Cron conforme configurado em `vercel.json`

**Resposta:**
```json
{
  "success": true,
  "message": "Cron execution completed for 30 airports",
  "summary": {
    "total_requests": 60,
    "total_success": 57,
    "total_error": 3,
    "success_rate": "95.0%"
  },
  "providers": {
    "tomorrow": {
      "success": 28,
      "error": 2
    },
    "redemet": {
      "success": 29,
      "error": 1
    }
  }
}
```

---

## Respostas de Erro

### Erro 400 - Bad Request
```json
{
  "success": false,
  "error": "Parâmetro file_path é obrigatório",
  "example": "/taf/file?file_path=aeroportos.txt"
}
```

### Erro 404 - Not Found
```json
{
  "success": false,
  "error": "Arquivo não encontrado: aeroportos.txt"
}
```

### Erro 500 - Internal Server Error
```json
{
  "success": false,
  "error": "Descrição do erro"
}
```

---

## Exemplos de Uso

### cURL

**Buscar TAF único:**
```bash
curl https://seu-dominio.vercel.app/taf/single
```

**Listar últimos 5 TAFs:**
```bash
curl https://seu-dominio.vercel.app/taf/history?limit=5
```

**Buscar de ambas as APIs:**
```bash
curl https://seu-dominio.vercel.app/taf/batch
```

**Buscar de arquivo específico:**
```bash
curl https://seu-dominio.vercel.app/taf/file?file_path=meus_aeroportos.txt
```

### JavaScript/Node.js

```javascript
async function fetchTAF() {
  const response = await fetch('https://seu-dominio.vercel.app/taf/batch');
  const data = await response.json();
  console.log(data);
}

fetchTAF();
```

### Python

```python
import requests

response = requests.get('https://seu-dominio.vercel.app/taf/batch')
data = response.json()
print(data)
```

---

## Cronograma de Execução Automática

O arquivo `vercel.json` configura execuções automáticas:

| Rota | Schedule | Horário |
|------|----------|---------|
| `/taf/single` | 30 3 * * * | 03:30 UTC |
| `/taf/single` | 30 9 * * * | 09:30 UTC |
| `/taf/single` | 30 15 * * * | 15:30 UTC |
| `/taf/single` | 30 21 * * * | 21:30 UTC |
| `/taf/cron/fetch` | 0 0 * * * | 00:00 UTC |
| `/taf/cron/fetch` | 0 6 * * * | 06:00 UTC |
| `/taf/cron/fetch` | 0 12 * * * | 12:00 UTC |
| `/taf/cron/fetch` | 0 18 * * * | 18:00 UTC |

---

## Rate Limits

- **Tomorrow.io:** Depende do plano contratado
- **REDEMET:** Sem limite específico documentado
- **Vercel Cron:** Até 50 invocações/mês (plano Free)

---

## Estrutura de Dados Retornada

### Resultado TAF - Tomorrow.io

```json
{
  "timestamp": "2024-07-13T10:30:45.123456+00:00",
  "status": "sucesso",
  "location": "SBRJ",
  "status_code": 200,
  "data": {
    "TAF": "TAF SBRJ 092200Z...",
    "metadata": {...}
  },
  "database_id": 1
}
```

### Resultado TAF - REDEMET

```json
{
  "timestamp": "2024-07-13T10:30:45.123456+00:00",
  "status": "sucesso",
  "location": "SBRJ",
  "source": "redemet",
  "status_code": 200,
  "total_records": 2,
  "data": [
    {
      "taf_data": "TAF SBRJ 092200Z...",
      "validade_inicial": "2024-07-13 00:00:00",
      "validade_final": "2024-07-14 00:00:00",
      "recebimento": "2024-07-13 22:57:33",
      "database_id": 2
    }
  ]
}
```

---

## Integração com Monitoramento

Para integrar com ferramentas de monitoramento (Sentry, DataDog, etc.):

```python
# Exemplo com Sentry
import sentry_sdk

sentry_sdk.init("sua-url-sentry")

try:
    response = await fetch_airports_from_file_both_apis('aeroportos.txt')
    if response['summary']['success_rate'] < 80:
        sentry_sdk.capture_message('TAF success rate below 80%', level='warning')
except Exception as e:
    sentry_sdk.capture_exception(e)
```

---

## Deployment

Para fazer deploy:

```bash
git add .
git commit -m "Update API endpoints"
git push origin main
```

Vercel fará deploy automático e ativará os crons configurados em `vercel.json`.
