import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """
    Cria conexão com PostgreSQL
    Suporta DATABASE_URL (Neon) ou variáveis individuais
    """
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

def init_db():
    """
    Cria a tabela TAF se não existir
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tafs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                taf_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        cursor.close()
        conn.close()
        print("Tabela TAF inicializada com sucesso")
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")
        raise

def save_taf(timestamp_str: str, taf_data: str):
    """
    Salva timestamp e TAF no banco de dados

    Args:
        timestamp_str: timestamp em ISO format
        taf_data: conteúdo do TAF

    Returns:
        ID do registro inserido
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO tafs (timestamp, taf_data)
            VALUES (%s, %s)
            RETURNING id
            ''',
            (timestamp_str, taf_data)
        )

        record_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()

        print(f"TAF salvo com sucesso. ID: {record_id}")
        return record_id
    except Exception as e:
        print(f"Erro ao salvar TAF: {e}")
        raise

def get_latest_tafs(limit: int = 10):
    """
    Retorna os últimos TAFs salvos
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            '''
            SELECT id, timestamp, taf_data, created_at
            FROM tafs
            ORDER BY created_at DESC
            LIMIT %s
            ''',
            (limit,)
        )

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return results
    except Exception as e:
        print(f"Erro ao buscar TAFs: {e}")
        raise
