# Database Migrations

Sistema de migrations para gerenciar o schema do banco de dados PostgreSQL.

## Como Funciona

- Cada migration é um arquivo SQL na pasta `migrations/`
- Nomeadas com prefixo numérico: `001_`, `002_`, etc.
- Após executada, a migration é registrada na tabela `migrations`
- Migrations nunca são re-executadas

## Usar

### 1. Verificar Status

```bash
python manage_migrations.py status
```

**Saída:**
```
============================================================
Migration Status
============================================================

Total de migrations: 1
Executadas: 0
Pendentes: 1

⏳ Pendentes:
  • 001_create_tables.sql
```

### 2. Executar Migrations

```bash
python manage_migrations.py migrate
```

**Saída:**
```
============================================================
Database Migrations
============================================================

✓ Tabela de migrations criada
✓ Migrations executadas: 0

⏳ Executando 1 migration(s) pendente(s):

✓ Migration executada: 001_create_tables.sql

============================================================
✓ Todas as migrations foram executadas com sucesso!
============================================================
```

### 3. Desfazer Última Migration

```bash
python manage_migrations.py rollback
```

## Estrutura

```
migrations/
├── 001_create_tables.sql
├── 002_add_columns.sql
└── ...
```

## Criando Nova Migration

1. Crie arquivo SQL em `migrations/`:

```bash
touch migrations/002_add_columns.sql
```

2. Escreva o SQL:

```sql
-- Migration: 002_add_columns.sql
-- Description: Add new columns
-- Created: 2024-07-13

ALTER TABLE tafs ADD COLUMN IF NOT EXISTS status VARCHAR(50);
ALTER TABLE tafs ADD COLUMN IF NOT EXISTS error_message TEXT;
```

3. Execute:

```bash
python manage_migrations.py migrate
```

## Exemplo - Migration Atual

**Arquivo:** `migrations/001_create_tables.sql`

Cria:
- Tabela `airports` com campos: id, iata_code, city, state, country, created_at
- Tabela `tafs` com campos: id, airport_id, timestamp, taf_data, source, created_at
- Índices para otimização de queries
- Relacionamento foreign key entre tafs e airports

## Rastreamento

A tabela `migrations` armazena:

```sql
SELECT * FROM migrations;
```

Exemplo de resultado:
```
 id |         name         |        executed_at
----+----------------------+------------------------
  1 | 001_create_tables.sql | 2024-07-13 10:30:45
```

## Boas Práticas

1. **Nomes descritivos:**
   ```
   001_create_tables.sql          ✓
   002_add_index_airports.sql     ✓
   003_add_column_status.sql      ✓
   
   fix.sql                        ✗
   update.sql                     ✗
   ```

2. **Usar IF NOT EXISTS/IF EXISTS:**
   ```sql
   CREATE TABLE IF NOT EXISTS airports (...)  ✓
   ALTER TABLE IF EXISTS tafs ADD COLUMN ...  ✓
   DROP TABLE IF EXISTS old_table             ✓
   ```

3. **Incluir comentário na migration:**
   ```sql
   -- Migration: 001_create_tables.sql
   -- Description: Cria tabelas principais do sistema
   -- Created: 2024-07-13
   ```

4. **Testar localmente antes de fazer commit:**
   ```bash
   python manage_migrations.py status
   python manage_migrations.py migrate
   python manage_migrations.py rollback
   python manage_migrations.py migrate
   ```

## Workflow

### Desenvolvimento Local

```bash
# 1. Ver status
python manage_migrations.py status

# 2. Executar migrations
python manage_migrations.py migrate

# 3. Testar mudanças
# ... faça testes ...

# 4. Se precisar desfazer
python manage_migrations.py rollback

# 5. Refine e execute novamente
python manage_migrations.py migrate
```

### Production (Vercel/Neon)

1. Commit migrations no git:
```bash
git add migrations/
git commit -m "Add migration 002_add_columns"
git push origin main
```

2. Vercel faz deploy automático

3. Execute na production:
```bash
# Acesse a função serverless e execute
python manage_migrations.py migrate
```

Ou adicione ao startup em `api/index.py`:
```python
@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        # Opcionalmente: executar migrations
    except Exception as e:
        print(f"Aviso: {e}")
```

## Troubleshooting

### Erro: "Tabela já existe"

Use `IF NOT EXISTS` na migration:
```sql
CREATE TABLE IF NOT EXISTS airports (...)
```

### Erro: "Column já existe"

Use `IF NOT EXISTS`:
```sql
ALTER TABLE tafs ADD COLUMN IF NOT EXISTS status VARCHAR(50);
```

### Rollback Manual

Se precisar reverter manualmente:

```bash
# Ver migrations executadas
python manage_migrations.py status

# Remover do rastreamento
DELETE FROM migrations WHERE name = '001_create_tables.sql';

# Desfazer manualmente (cuidado!)
DROP TABLE tafs;
DROP TABLE airports;
```

## Segurança

- ✅ Use `ON DELETE CASCADE` para foreign keys
- ✅ Sempre tenha backup antes de migrations em production
- ✅ Teste em dev/staging antes de production
- ✅ Migrations são imutáveis (nunca modifique arquivos já executados)

Se precisar corrigir um erro:
1. Crie nova migration para desfazer
2. Crie migration para aplicar a solução correta

Exemplo:
```
001_create_tables.sql           # ✓ Execução original
002_fix_column_type.sql         # ✓ Correção do erro
```

## Referência Rápida

```bash
# Ver status
python manage_migrations.py status

# Executar
python manage_migrations.py migrate

# Desfazer última
python manage_migrations.py rollback

# Criar nova
touch migrations/00X_description.sql
```

## Próximas Migrations (Exemplos)

Se precisar de outras mudanças:

```sql
-- 002_add_taf_validation.sql
ALTER TABLE tafs ADD COLUMN IF NOT EXISTS is_valid BOOLEAN DEFAULT TRUE;
ALTER TABLE tafs ADD COLUMN IF NOT EXISTS validation_error TEXT;

-- 003_add_airport_metadata.sql
ALTER TABLE airports ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8);
ALTER TABLE airports ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8);
ALTER TABLE airports ADD COLUMN IF NOT EXISTS timezone VARCHAR(50);

-- 004_add_performance_indexes.sql
CREATE INDEX IF NOT EXISTS idx_tafs_airport_date ON tafs(airport_id, created_at DESC);
```

## Integração com CI/CD

No arquivo de deployment (Vercel, GitHub Actions, etc.):

```bash
#!/bin/bash
# Deploy script
python manage_migrations.py status
python manage_migrations.py migrate
python -m pytest
```
