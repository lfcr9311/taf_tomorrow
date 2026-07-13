# Sistema de Busca de 30 Aeroportos

Este documento descreve como buscar dados TAF de 30 aeroportos brasileiros de duas APIs diferentes: **Tomorrow.io** e **REDEMET**.

## Aeroportos Suportados

O sistema suporta os seguintes 30 aeroportos brasileiros:

1. SBRJ - Rio de Janeiro (RJ)
2. SBSP - São Paulo (SP)
3. SBGR - Guarulhos (SP)
4. SBCT - Curitiba (PR)
5. SBCF - Confins (MG)
6. SBRF - Recife (PE)
7. SBSG - Salvador (BA)
8. SBAR - Aracaju (SE)
9. SBPA - Porto Alegre (RS)
10. SBMG - Belo Horizonte (MG)
11. SBFZ - Fortaleza (CE)
12. SBNT - Natal (RN)
13. SBMA - Manaus (AM)
14. SBEG - Eduardo Gomes (AM)
15. SBVT - Vitória (ES)
16. SBIL - Ilhéus (BA)
17. SBIN - Ilhéus (BA)
18. SBMK - Macapá (AP)
19. SBPV - Petrolina (PE)
20. SBTE - Teresina (PI)
21. SBMO - Mossoró (RN)
22. SBME - Maceió (AL)
23. SBCA - Campinas (SP)
24. SBKP - Cuiabá (MT)
25. SBGO - Goiânia (GO)
26. SBCO - Corumbá (MS)
27. SBCY - Campo Grande (MS)
28. SBUA - Uberaba (MG)
29. SBPP - Poços de Caldas (MG)
30. SBST - Santa Maria (RS)

## Como Usar

### Via Script Python

```bash
python fetch_airports.py
```

Este script irá:
1. Inicializar o banco de dados
2. Popular a tabela de aeroportos
3. Buscar TAFs de 30 aeroportos da Tomorrow.io
4. Buscar TAFs de 30 aeroportos da REDEMET
5. Gerar um relatório em JSON (`aeroportos_results.json`)

### Via API

#### 1. Buscar 30 aeroportos da Tomorrow.io

```bash
curl http://localhost:8000/api/fetch-all-tomorrow
```

**Resposta:**
```json
{
  "success": true,
  "message": "Busca concluída - X sucesso, Y erro",
  "source": "tomorrow",
  "total_airports": 30,
  "success_count": X,
  "error_count": Y,
  "results": [...]
}
```

#### 2. Buscar 30 aeroportos da REDEMET

```bash
curl http://localhost:8000/api/fetch-all-redemet
```

**Resposta:**
```json
{
  "success": true,
  "message": "Busca concluída - X sucesso, Y erro",
  "source": "redemet",
  "total_airports": 30,
  "success_count": X,
  "error_count": Y,
  "results": [...]
}
```

#### 3. Buscar 30 aeroportos de ambas as APIs

```bash
curl http://localhost:8000/api/fetch-all-both
```

**Resposta:**
```json
{
  "success": true,
  "message": "Busca concluída em ambas as APIs",
  "total_airports": 60,
  "tomorrow": {
    "success": X,
    "error": Y,
    "results": [...]
  },
  "redemet": {
    "success": X,
    "error": Y,
    "results": [...]
  }
}
```

## Estrutura do Banco de Dados

### Tabela `airports`
```sql
CREATE TABLE airports (
  id SERIAL PRIMARY KEY,
  iata_code VARCHAR(10) UNIQUE NOT NULL,
  city VARCHAR(100),
  state VARCHAR(50),
  country VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Tabela `tafs`
```sql
CREATE TABLE tafs (
  id SERIAL PRIMARY KEY,
  airport_id INTEGER,
  timestamp TIMESTAMP NOT NULL,
  taf_data TEXT NOT NULL,
  source VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (airport_id) REFERENCES airports(id)
)
```

## Variáveis de Ambiente

Certifique-se de que seu arquivo `.env` contenha:

```
# Tomorrow.io
TOMORROW_IO_API_URL=https://api.tomorrow.io/v4/weather/forecast
TOMORROW_IO_API_KEY=sua_chave_api

# REDEMET (opcional - usará padrão se não definido)
REDEMET_API_URL=https://www.redemet.aer.mil.br/api/v1/tafs

# Banco de Dados
DATABASE_URL=seu_url_do_banco
# ou
DB_HOST=localhost
DB_PORT=5432
DB_NAME=taf_db
DB_USER=postgres
DB_PASSWORD=sua_senha
```

## Estrutura de Resposta dos Resultados

Cada resultado contém:

```json
{
  "timestamp": "2024-07-13T10:30:45.123456+00:00",
  "status": "sucesso",
  "location": "SBRJ",
  "source": "tomorrow ou redemet",
  "status_code": 200,
  "data": { ... dados brutos da API ... },
  "database_id": 1
}
```

Ou em caso de erro:

```json
{
  "timestamp": "2024-07-13T10:30:45.123456+00:00",
  "status": "erro",
  "location": "SBRJ",
  "source": "tomorrow ou redemet",
  "error": "mensagem de erro"
}
```

## Exemplo de Uso Completo

```python
import asyncio
from main import fetch_all_airports_tomorrow, fetch_all_airports_redemet, init_airports
from database import init_db

async def main():
    # Inicializa banco de dados
    init_db()
    
    # Inicializa 30 aeroportos
    init_airports()
    
    # Busca da Tomorrow.io
    tomorrow_results = await fetch_all_airports_tomorrow()
    print(f"Tomorrow.io: {len([r for r in tomorrow_results if r['status'] == 'sucesso'])} sucesso")
    
    # Busca da REDEMET
    redemet_results = await fetch_all_airports_redemet()
    print(f"REDEMET: {len([r for r in redemet_results if r['status'] == 'sucesso'])} sucesso")

asyncio.run(main())
```

## Notas

- Ambas as APIs têm rate limits. Ajuste conforme necessário.
- A REDEMET pode não estar disponível em todos os momentos.
- Os dados são armazenados com timestamp de coleta e fonte de origem para rastreabilidade.
- Você pode consultar os dados salvos usando os endpoints `/api/tafs` (com filtro opcional por `limit`).
