import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time
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
    Cria as tabelas TAF e aeroportos se não existirem
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS airports (
                id SERIAL PRIMARY KEY,
                iata_code VARCHAR(10) UNIQUE NOT NULL,
                city VARCHAR(100),
                state VARCHAR(50),
                country VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tafs (
                id SERIAL PRIMARY KEY,
                airport_id INTEGER,
                timestamp TIMESTAMP NOT NULL,
                taf_data TEXT NOT NULL,
                source VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (airport_id) REFERENCES airports(id)
            )
        ''')

        conn.commit()
        cursor.close()
        conn.close()
        print("Tabelas inicializadas com sucesso")
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")
        raise

def add_airport(iata_code: str, city: str = None, state: str = None, country: str = "Brasil"):
    """
    Adiciona um aeroporto ao banco de dados

    Args:
        iata_code: código IATA do aeroporto
        city: cidade
        state: estado/região
        country: país

    Returns:
        ID do aeroporto ou None se já existe
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO airports (iata_code, city, state, country)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (iata_code) DO NOTHING
            RETURNING id
            ''',
            (iata_code, city, state, country)
        )

        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        if result:
            airport_id = result[0]
            print(f"Aeroporto {iata_code} adicionado com sucesso. ID: {airport_id}")
            return airport_id
        else:
            print(f"Aeroporto {iata_code} já existe no banco de dados")
            return get_airport_id(iata_code)
    except Exception as e:
        print(f"Erro ao adicionar aeroporto: {e}")
        raise

def get_airport_id(iata_code: str):
    """
    Obtém o ID de um aeroporto pelo código IATA
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            'SELECT id FROM airports WHERE iata_code = %s',
            (iata_code,)
        )

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        return result[0] if result else None
    except Exception as e:
        print(f"Erro ao buscar aeroporto: {e}")
        raise

def save_taf_tomorrow(timestamp_str: str, taf_data: str, airport_id: int = None):
    """
    Salva TAF da Tomorrow.io no banco de dados

    Args:
        timestamp_str: timestamp em ISO format
        taf_data: conteúdo do TAF
        airport_id: ID do aeroporto

    Returns:
        ID do registro inserido
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO taf_tomorrow (airport_id, timestamp, taf_data)
            VALUES (%s, %s, %s)
            RETURNING id
            ''',
            (airport_id, timestamp_str, taf_data)
        )

        record_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()

        print(f"✓ TAF Tomorrow salvo. ID: {record_id}")
        return record_id
    except Exception as e:
        print(f"✗ Erro ao salvar TAF Tomorrow: {e}")
        raise

def save_taf_redemet(timestamp_str: str, taf_data: str, airport_id: int = None,
                     validade_inicial: str = None, validade_final: str = None, recebimento: str = None):
    """
    Salva TAF da REDEMET no banco de dados

    Args:
        timestamp_str: timestamp em ISO format
        taf_data: conteúdo do TAF
        airport_id: ID do aeroporto
        validade_inicial: data/hora de validade inicial
        validade_final: data/hora de validade final
        recebimento: data/hora de recebimento

    Returns:
        ID do registro inserido
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO taf_redemet (airport_id, timestamp, taf_data, validade_inicial, validade_final, recebimento)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            ''',
            (airport_id, timestamp_str, taf_data, validade_inicial, validade_final, recebimento)
        )

        record_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()

        print(f"✓ TAF REDEMET salvo. ID: {record_id}")
        return record_id
    except Exception as e:
        print(f"✗ Erro ao salvar TAF REDEMET: {e}")
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

def save_metar_redemet(timestamp_str: str, metar_data: str, airport_id: int = None,
                       observacao: str = None, recebimento: str = None):
    """
    Salva METAR da REDEMET no banco de dados (single)

    Args:
        timestamp_str: timestamp de captura em ISO format
        metar_data: conteúdo do METAR
        airport_id: ID do aeroporto
        observacao: timestamp da observação (validade_inicial da REDEMET)
        recebimento: timestamp de recebimento

    Returns:
        ID do registro inserido
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            INSERT INTO metar_redemet (airport_id, timestamp, metar_data, observacao, recebimento)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            ''',
            (airport_id, timestamp_str, metar_data, observacao, recebimento)
        )

        record_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()

        return record_id
    except Exception as e:
        print(f"✗ Erro ao salvar METAR REDEMET: {e}")
        raise

def save_metar_batch(metar_records: list):
    """
    Salva múltiplos METARs em uma única operação (muito mais rápido)

    Args:
        metar_records: Lista de dicts com {timestamp, metar_data, airport_id, observacao, recebimento}

    Returns:
        Número de registros inseridos
    """
    if not metar_records:
        return 0

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Preparar valores para batch insert
        values = []
        for rec in metar_records:
            values.append((
                rec['airport_id'],
                rec['timestamp'],
                rec['metar_data'],
                rec['observacao'],
                rec['recebimento']
            ))

        # Executar batch insert
        cursor.executemany(
            '''
            INSERT INTO metar_redemet (airport_id, timestamp, metar_data, observacao, recebimento)
            VALUES (%s, %s, %s, %s, %s)
            ''',
            values
        )

        conn.commit()
        count = cursor.rowcount
        cursor.close()
        conn.close()

        return count
    except Exception as e:
        print(f"✗ Erro ao salvar METAR em batch: {e}")
        raise

def get_taf_time_range(airport_id: int):
    """
    Obtém intervalo de tempo (MIN/MAX) dos TAFs coletados de um aeroporto

    Args:
        airport_id: ID do aeroporto

    Returns:
        Tupla (min_timestamp, max_timestamp) ou (None, None) se não há TAFs
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            '''
            SELECT MIN(timestamp), MAX(timestamp)
            FROM (
                SELECT timestamp FROM taf_tomorrow WHERE airport_id = %s
                UNION ALL
                SELECT timestamp FROM taf_redemet WHERE airport_id = %s
            ) tafs
            ''',
            (airport_id, airport_id)
        )

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        return result if result and result[0] else (None, None)
    except Exception as e:
        print(f"Erro ao buscar intervalo de TAFs: {e}")
        return (None, None)

def wake_up_database(max_retries: int = 3, retry_delay: int = 2):
    """
    Acorda o banco Neon se estiver em autosuspend
    Tenta conectar múltiplas vezes com delay entre tentativas

    Args:
        max_retries: número de tentativas
        retry_delay: segundos entre tentativas

    Returns:
        dict com status da operação
    """
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[{attempt}/{max_retries}] Acordando banco de dados...")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            print("✓ Banco de dados acordado com sucesso!")
            return {
                'success': True,
                'message': 'Database is now awake',
                'attempts': attempt
            }
        except psycopg2.OperationalError as e:
            if attempt < max_retries:
                print(f"  ⏳ Banco ainda está dormindo... aguardando {retry_delay}s")
                time.sleep(retry_delay)
            else:
                print(f"✗ Falha ao acordar banco após {max_retries} tentativas: {e}")
                return {
                    'success': False,
                    'message': f'Failed to wake database after {max_retries} attempts',
                    'error': str(e),
                    'attempts': attempt
                }
        except Exception as e:
            print(f"✗ Erro inesperado: {e}")
            return {
                'success': False,
                'message': 'Unexpected error',
                'error': str(e),
                'attempts': attempt
            }

    return {
        'success': False,
        'message': 'Max retries exceeded',
        'attempts': max_retries
    }
