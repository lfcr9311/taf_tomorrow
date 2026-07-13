# Configuração de Variáveis de Ambiente (.env)

## Criar arquivo .env

```bash
cp .env.example .env
```

## Configurar Variáveis

### 1. Banco de Dados

#### Opção A: Para Vercel/Neon (recomendado)
```env
DATABASE_URL=postgresql://user:password@ep-xxx.neon.tech:5432/database_name?sslmode=require
```

#### Opção B: Local (desenvolvimento)
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=taf_db
DB_USER=postgres
DB_PASSWORD=sua_senha_postgres
```

### 2. Tomorrow.io API

1. Acesse: https://www.tomorrow.io/
2. Crie uma conta e obtenha a chave API
3. Configure:

```env
TOMORROW_IO_API_URL=https://api.tomorrow.io/v4/weather/forecast
TOMORROW_IO_API_KEY=sua_chave_aqui
```

### 3. REDEMET API

1. Acesse: https://www.redemet.aer.mil.br/
2. Registre-se e obtenha acesso à API
3. Configure:

```env
REDEMET_API_URL=https://api-redemet.decea.mil.br/mensagens/taf
REDEMET_API_KEY=sua_chave_aqui
```

## Exemplo Completo - Local

```env
# Banco de Dados Local
DB_HOST=localhost
DB_PORT=5432
DB_NAME=taf_db
DB_USER=postgres
DB_PASSWORD=postgres123

# Tomorrow.io
TOMORROW_IO_API_URL=https://api.tomorrow.io/v4/weather/forecast
TOMORROW_IO_API_KEY=abc123xyz

# REDEMET
REDEMET_API_URL=https://api-redemet.decea.mil.br/mensagens/taf
REDEMET_API_KEY=def456uvw

# App
ENV=development
DEBUG=true
```

## Exemplo Completo - Vercel/Production

```env
# Database Neon
DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech:5432/taf_db?sslmode=require

# Tomorrow.io
TOMORROW_IO_API_URL=https://api.tomorrow.io/v4/weather/forecast
TOMORROW_IO_API_KEY=sua_chave_produção

# REDEMET
REDEMET_API_URL=https://api-redemet.decea.mil.br/mensagens/taf
REDEMET_API_KEY=sua_chave_produção

# App
ENV=production
DEBUG=false
```

## Vercel Environment Variables

Para configurar no Vercel:

1. Vá para **Project Settings**
2. Clique em **Environment Variables**
3. Adicione cada variável:

| Nome | Valor | Escopo |
|------|-------|--------|
| `DATABASE_URL` | `postgresql://...` | Production, Preview, Development |
| `TOMORROW_IO_API_URL` | `https://api.tomorrow.io/...` | Production, Preview, Development |
| `TOMORROW_IO_API_KEY` | `sua_chave` | Production, Preview, Development |
| `REDEMET_API_URL` | `https://api-redemet.decea.mil.br/...` | Production, Preview, Development |
| `REDEMET_API_KEY` | `sua_chave` | Production, Preview, Development |

## ⚠️ Segurança

- ✅ **Nunca commit .env** - Adicione ao `.gitignore`
- ✅ **Use variáveis sensíveis** - Senhas, chaves de API
- ✅ **Diferentes valores por ambiente** - Local, staging, production
- ✅ **Rotacione chaves regularmente** - Especialmente em production

### .gitignore

Certifique-se que tem:
```
.env
.env.local
.env.*.local
```

## Teste de Configuração

Para verificar se as variáveis estão carregadas:

```python
import os
from dotenv import load_dotenv

load_dotenv()

print("DATABASE_URL:", os.getenv('DATABASE_URL'))
print("TOMORROW_IO_API_KEY:", os.getenv('TOMORROW_IO_API_KEY'))
print("REDEMET_API_KEY:", os.getenv('REDEMET_API_KEY'))
```

## Trocar entre ambientes

### Local Development
```bash
# .env aponta para localhost
DB_HOST=localhost
```

### Staging/Preview
```bash
# .env.staging aponta para staging DB
DB_HOST=staging-db.example.com
```

### Production
```bash
# Variáveis do Vercel
# DATABASE_URL=postgresql://...
```

## Erros Comuns

### "psycopg2: could not connect to server"
- Verifique `DB_HOST`, `DB_PORT`, `DB_NAME`
- Certifique-se que PostgreSQL está rodando localmente

### "REDEMET_API_KEY não configurada"
- Adicione a variável ao `.env`
- Verifique se o `.env` foi carregado: `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('REDEMET_API_KEY'))"`

### "Invalid API Key"
- Copie a chave corretamente do painel de controle
- Não adicione espaços em branco: `ABC123` não `ABC123 `

## Regenerar .env

Se precisar resetar:

```bash
# Backup da configuração atual
cp .env .env.backup

# Criar novo a partir do exemplo
cp .env.example .env

# Editar com suas credenciais
nano .env
```

## Variáveis Opcionais

```env
# Logging
LOG_LEVEL=INFO

# Cache
CACHE_TTL=3600

# Rate Limiting
RATE_LIMIT=100
```

## Deploy com Variáveis

### Vercel CLI

```bash
# Login
vercel login

# Set environment variables
vercel env add TOMORROW_IO_API_KEY
vercel env add REDEMET_API_KEY
vercel env add DATABASE_URL

# Deploy
vercel deploy --prod
```

### Git + Vercel

1. Commit `.env.example` (sem valores)
2. Configure variáveis no dashboard do Vercel
3. Push para GitHub
4. Vercel faz deploy automático com variáveis

## Referência Rápida

```bash
# Criar arquivo
cp .env.example .env

# Editar
nano .env
# ou
vim .env
# ou abrir em editor

# Verificar valores
grep -v '^#' .env | grep -v '^$'

# Testar conexão
python -c "from database import get_db_connection; c = get_db_connection(); print('✓ Conectado')"
```
