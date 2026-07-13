# Como Usar o Sistema com Arquivo .txt de Aeroportos

## Preparação

### 1. Criar arquivo .txt com os aeroportos

Crie um arquivo `.txt` com um código ICAO por linha:

**Exemplo: `meus_aeroportos.txt`**
```
SBRJ
SBSP
SBCT
SBRF
SBSG
```

### 2. Configurar variáveis de ambiente

Certifique-se de que seu arquivo `.env` tem:

```env
# Tomorrow.io
TOMORROW_IO_API_URL=https://api.tomorrow.io/v4/weather/forecast
TOMORROW_IO_API_KEY=sua_chave_tomorrow_io

# REDEMET (obrigatório para usar a API REDEMET)
REDEMET_API_URL=https://api-redemet.decea.mil.br/mensagens/taf
REDEMET_API_KEY=sua_chave_redemet

# Banco de dados
DATABASE_URL=postgresql://user:password@localhost/taf_db
# ou
DB_HOST=localhost
DB_PORT=5432
DB_NAME=taf_db
DB_USER=postgres
DB_PASSWORD=sua_senha
```

## Como Usar

### Opção 1: Via Script Python (Recomendado)

```bash
python fetch_from_file.py meus_aeroportos.txt
```

**Saída esperada:**
```
============================================================
Coleta de TAFs - Arquivo de Aeroportos
============================================================

✓ 5 aeroportos lidos do arquivo: meus_aeroportos.txt

============================================================
Buscando TAFs de 5 aeroportos
============================================================

--- Tomorrow.io ---
✓ SBRJ: sucesso
✓ SBSP: sucesso
✓ SBCT: sucesso
✓ SBRF: sucesso
✓ SBSG: sucesso

--- REDEMET ---
✓ SBRJ: sucesso (2 registros)
✓ SBSP: sucesso (1 registro)
✓ SBCT: sucesso (2 registros)
✓ SBRF: sucesso (1 registro)
✓ SBSG: sucesso (3 registros)

============================================================
RELATÓRIO FINAL
============================================================

Total de aeroportos processados: 5
Total de requisições: 10

Tomorrow.io:
  ✓ Sucesso: 5
  ✗ Erro: 0

REDEMET:
  ✓ Sucesso: 5
  ✗ Erro: 0

Resumo Geral:
  Total de sucesso: 10/10
  Taxa de sucesso: 100.0%

✓ Relatório salvo em: meus_aeroportos_results.json
```

### Opção 2: Via API HTTP

**Requisição:**
```bash
curl "http://localhost:8000/api/fetch-file?file_path=meus_aeroportos.txt"
```

**Resposta:**
```json
{
  "success": true,
  "message": "Busca concluída para 5 aeroportos",
  "data": {
    "airports_count": 5,
    "tomorrow": {
      "success": 5,
      "error": 0,
      "results": [...]
    },
    "redemet": {
      "success": 5,
      "error": 0,
      "results": [...]
    },
    "summary": {
      "total_requests": 10,
      "total_success": 10,
      "total_error": 0,
      "success_rate": "100.0%"
    }
  }
}
```

## Arquivos Gerados

Após executar o script, serão criados:

1. **`{seu_arquivo}_results.json`** - Relatório detalhado com todos os resultados
2. **Banco de dados PostgreSQL** - Dados salvos nas tabelas:
   - `airports` - Lista de aeroportos
   - `tafs` - TAFs de cada aeroporto com timestamp e fonte

## Formato dos Códigos ICAO

Os códigos devem ser válidos para ICAO (4 letras). Exemplos:

| Aeroporto | Código |
|-----------|--------|
| Rio de Janeiro (Galeão) | SBRJ |
| São Paulo (Guarulhos) | SBGR |
| São Paulo (Congonhas) | SBSP |
| Curitiba | SBCT |
| Recife | SBRF |
| Salvador | SBSG |
| Brasília | SBBR |
| Fortaleza | SBFZ |
| Manaus | SBMA |
| Porto Alegre | SBPA |

## Formato do Arquivo de Saída (JSON)

```json
{
  "airports_count": 5,
  "tomorrow": {
    "success": 5,
    "error": 0,
    "results": [
      {
        "timestamp": "2024-07-13T10:30:45.123456+00:00",
        "status": "sucesso",
        "location": "SBRJ",
        "status_code": 200,
        "data": {...},
        "database_id": 1
      }
    ]
  },
  "redemet": {
    "success": 5,
    "error": 0,
    "results": [
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
    ]
  },
  "summary": {
    "total_requests": 10,
    "total_success": 10,
    "total_error": 0,
    "success_rate": "100.0%"
  }
}
```

## Solução de Problemas

### Erro: "REDEMET_API_KEY não configurada"

**Solução:** Adicione a chave REDEMET ao arquivo `.env`:
```
REDEMET_API_KEY=sua_chave_aqui
```

### Erro: "Arquivo não encontrado"

**Solução:** Verifique se o caminho está correto:
```bash
# Caminho relativo (a partir da pasta do projeto)
python fetch_from_file.py meus_aeroportos.txt

# Caminho absoluto
python fetch_from_file.py /home/usuario/meus_aeroportos.txt
```

### Erro de conexão com banco de dados

**Solução:** Verifique as variáveis de ambiente:
```bash
# Teste a conexão
psql -h localhost -U postgres -d taf_db
```

## Exemplo de Arquivo .txt

Veja o arquivo `exemplo_aeroportos.txt` para um exemplo com 30 aeroportos.

## Integração com Cron/Agendador

Para executar automaticamente a cada dia às 00:00:

```bash
# Adicione ao crontab
0 0 * * * cd /home/usuario/taf_tomorrow && python fetch_from_file.py meus_aeroportos.txt
```
