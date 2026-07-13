import os
import sys
import psycopg2
from database import get_db_connection
from dotenv import load_dotenv

load_dotenv()

MIGRATIONS_DIR = 'migrations'

def create_migrations_table():
    """Cria tabela para rastrear migrations executadas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        cursor.close()
        conn.close()
        print("✓ Tabela de migrations criada")
    except Exception as e:
        print(f"✗ Erro ao criar tabela de migrations: {e}")
        raise

def get_executed_migrations():
    """Retorna lista de migrations já executadas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT name FROM migrations ORDER BY executed_at')
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return [row[0] for row in results]
    except Exception as e:
        print(f"✗ Erro ao buscar migrations: {e}")
        return []

def get_migration_files():
    """Retorna lista de arquivos de migration em ordem"""
    files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')])
    return files

def execute_migration(filename):
    """Executa uma migration SQL"""
    try:
        filepath = os.path.join(MIGRATIONS_DIR, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            sql = f.read()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Executar o SQL da migration
        cursor.execute(sql)

        # Registrar na tabela de migrations
        cursor.execute(
            'INSERT INTO migrations (name) VALUES (%s)',
            (filename,)
        )

        conn.commit()
        cursor.close()
        conn.close()

        print(f"✓ Migration executada: {filename}")
        return True
    except Exception as e:
        print(f"✗ Erro ao executar migration {filename}: {e}")
        return False

def migrate():
    """Executa todas as migrations pendentes"""
    print("=" * 60)
    print("🔄 Database Migrations")
    print("=" * 60)

    # Criar tabela de migrations se não existir
    try:
        create_migrations_table()
    except Exception as e:
        print(f"⚠ Erro ao criar tabela de migrations: {e}")
        return False

    # Obter migrations executadas
    executed = get_executed_migrations()
    print(f"\n✓ Migrations executadas: {len(executed)}")
    if executed:
        for m in executed:
            print(f"  • {m}")

    # Obter arquivos de migration
    migration_files = get_migration_files()
    print(f"✓ Arquivos de migration encontrados: {len(migration_files)}")
    if migration_files:
        for m in migration_files:
            status = "✓" if m in executed else "⏳"
            print(f"  {status} {m}")

    pending = [f for f in migration_files if f not in executed]

    if not pending:
        print("\n✓ Nenhuma migration pendente!")
        print("=" * 60 + "\n")
        return True

    # Executar migrations pendentes
    print(f"\n⏳ Executando {len(pending)} migration(s) pendente(s):")
    for i, filename in enumerate(pending, 1):
        print(f"  [{i}/{len(pending)}] {filename}")
        if not execute_migration(filename):
            print("\n" + "=" * 60)
            print("✗ Erro ao executar migrations!")
            print("=" * 60 + "\n")
            return False

    print("\n" + "=" * 60)
    print("✓ Todas as migrations foram executadas com sucesso!")
    print("=" * 60 + "\n")
    return True

def rollback():
    """Remove a última migration executada"""
    executed = get_executed_migrations()

    if not executed:
        print("✗ Nenhuma migration para remover")
        return False

    last_migration = executed[-1]
    print(f"⚠ Removendo: {last_migration}")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            'DELETE FROM migrations WHERE name = %s',
            (last_migration,)
        )

        conn.commit()
        cursor.close()
        conn.close()

        print(f"✓ Migration removida: {last_migration}")
        return True
    except Exception as e:
        print(f"✗ Erro ao remover migration: {e}")
        return False

def status():
    """Mostra status das migrations"""
    print("=" * 60)
    print("Migration Status")
    print("=" * 60)

    executed = get_executed_migrations()
    migration_files = get_migration_files()
    pending = [f for f in migration_files if f not in executed]

    print(f"\nTotal de migrations: {len(migration_files)}")
    print(f"Executadas: {len(executed)}")
    print(f"Pendentes: {len(pending)}")

    if executed:
        print("\n✓ Executadas:")
        for m in executed:
            print(f"  • {m}")

    if pending:
        print("\n⏳ Pendentes:")
        for m in pending:
            print(f"  • {m}")

    print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python manage_migrations.py <comando>")
        print("\nComandos:")
        print("  migrate    - Executar todas as migrations pendentes")
        print("  status     - Ver status das migrations")
        print("  rollback   - Remover última migration")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'migrate':
        success = migrate()
        sys.exit(0 if success else 1)
    elif command == 'status':
        status()
    elif command == 'rollback':
        rollback()
    else:
        print(f"✗ Comando desconhecido: {command}")
        sys.exit(1)
