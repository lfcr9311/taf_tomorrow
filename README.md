# TAF Tomorrow - API de Dados Meteorológicos

Sistema para coletar dados TAF (Terminal Aerodrome Forecast) da API Tomorrow.io e salvá-los em um banco de dados PostgreSQL.

## Setup

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:
```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:
```
TOMORROW_IO_API_KEY=sua_chave_api
DB_HOST=localhost
DB_PORT=5432
DB_NAME=taf_db
DB_USER=postgres
DB_PASSWORD=sua_senha
```

### 3. Criar banco de dados PostgreSQL

```bash
# No PostgreSQL
createdb taf_db
```

### 4. Inicializar tabelas

```bash
python init_database.py
```

## Uso

### Executar localmente

```bash
uvicorn api.index:app --reload
```

A API estará disponível em `http://localhost:8000`

### Endpoints

#### GET /api/taf
Faz requisição para a API Tomorrow.io e salva os dados no banco

**Resposta de sucesso (200):**
```json
{
  "success": true,
  "message": "TAF obtido com sucesso",
  "data": {
    "timestamp": "2025-07-15T07:11:34Z",
    "status": "sucesso",
    "location": "SBRJ",
    "status_code": 200,
    "data": { ... },
    "database_id": 1
  }
}
```

#### GET /api/tafs
Lista os últimos TAFs salvos no banco

**Parâmetros:**
- `limit` (opcional): quantidade máxima de registros (padrão: 10)

**Resposta (200):**
```json
{
  "success": true,
  "count": 5,
  "data": [
    {
      "id": 5,
      "timestamp": "2025-07-15T07:11:34Z",
      "taf_data": "KJFK 150339Z 1507/1607 33003KT P6SM TS NSC...",
      "created_at": "2025-07-15T07:12:00Z"
    }
  ]
}
```

#### GET /
Health check da API

## Estrutura do Banco de Dados

### Tabela `tafs`
```sql
CREATE TABLE tafs (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP NOT NULL,
  taf_data TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

- `id`: ID único do registro
- `timestamp`: timestamp do TAF (da API)
- `taf_data`: conteúdo do TAF (sem divisão)
- `created_at`: quando foi salvo no banco

## Arquivos

- `main.py`: Função principal para buscar dados da API
- `database.py`: Funções para gerenciar banco de dados
- `api/index.py`: API FastAPI e endpoints
- `init_database.py`: Script para inicializar tabelas
- `requirements.txt`: Dependências Python
