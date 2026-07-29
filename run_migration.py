#!/usr/bin/env python3
"""
Script para rodar as migrations manualmente
"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    else:
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', 5432),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )

def run_migrations():
    """Executa todas as migrations em ordem"""
    migration_dir = 'migrations'
    migration_files = sorted([f for f in os.listdir(migration_dir) if f.endswith('.sql')])

    conn = get_db_connection()
    cursor = conn.cursor()

    for migration_file in migration_files:
        filepath = os.path.join(migration_dir, migration_file)
        print(f"\nExecutando: {migration_file}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sql = f.read()

            cursor.execute(sql)
            conn.commit()
            print(f"✓ {migration_file} OK")

        except Exception as e:
            conn.rollback()
            print(f"✗ Erro em {migration_file}: {e}")

    cursor.close()
    conn.close()
    print("\n✓ Migrations concluídas!")

if __name__ == '__main__':
    print("="*60)
    print("EXECUTANDO MIGRATIONS")
    print("="*60)
    run_migrations()
