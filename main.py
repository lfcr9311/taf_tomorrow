import requests
from datetime import datetime, timezone
import json
import os
from dotenv import load_dotenv
from database import init_db, save_taf_tomorrow, save_taf_redemet, add_airport, get_airport_id

load_dotenv()

BRAZILIAN_AIRPORTS = [
    ("SBRJ", "Rio de Janeiro", "RJ"),
    ("SBSP", "São Paulo", "SP"),
    ("SBGR", "Guarulhos", "SP"),
    ("SBCT", "Curitiba", "PR"),
    ("SBCF", "Confins", "MG"),
    ("SBRF", "Recife", "PE"),
    ("SBSG", "Salvador", "BA"),
    ("SBAR", "Aracaju", "SE"),
    ("SBPA", "Porto Alegre", "RS"),
    ("SBMG", "Belo Horizonte", "MG"),
    ("SBFZ", "Fortaleza", "CE"),
    ("SBNT", "Natal", "RN"),
    ("SBMA", "Manaus", "AM"),
    ("SBEG", "Eduardo Gomes", "AM"),
    ("SBVT", "Vitória", "ES"),
    ("SBIL", "Ilhéus", "BA"),
    ("SBIN", "Ilhéus", "BA"),
    ("SBMK", "Macapá", "AP"),
    ("SBPV", "Petrolina", "PE"),
    ("SBTE", "Teresina", "PI"),
    ("SBMO", "Mossoró", "RN"),
    ("SBME", "Maceió", "AL"),
    ("SBCA", "Campinas", "SP"),
    ("SBKP", "Cuiabá", "MT"),
    ("SBGO", "Goiânia", "GO"),
    ("SBCO", "Corumbá", "MS"),
    ("SBCY", "Campo Grande", "MS"),
    ("SBUA", "Uberaba", "MG"),
    ("SBPP", "Poços de Caldas", "MG"),
    ("SBST", "Santa Maria", "RS"),
]

def init_airports():
    """
    Inicializa a lista de 30 aeroportos no banco de dados
    """
    print("Inicializando 30 aeroportos brasileiros...")
    for iata, city, state in BRAZILIAN_AIRPORTS[:30]:
        add_airport(iata, city, state)

async def fetch_taf_tomorrow(location: str):
    """
    Busca TAF da API Tomorrow.io e salva em taf_tomorrow
    """
    try:
        api_url = os.getenv('TOMORROW_IO_API_URL')

        params = {
            'location': location,
            'source': 'model',
            'apikey': os.getenv('TOMORROW_IO_API_KEY')
        }

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.get(api_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        timestamp = datetime.now(timezone.utc).isoformat()

        taf_text = data.get('TAF', '')
        airport_id = get_airport_id(location)

        db_id = None
        if taf_text and airport_id:
            db_id = save_taf_tomorrow(timestamp, taf_text, airport_id)

        return {
            'timestamp': timestamp,
            'status': 'sucesso',
            'location': location,
            'status_code': response.status_code,
            'database_id': db_id
        }

    except requests.exceptions.RequestException as error:
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'erro',
            'location': location,
            'error': str(error)
        }

async def fetch_taf_redemet(location: str, data_ini: str = None, data_fim: str = None):
    """
    Busca TAF da API REDEMET e salva em taf_redemet

    Args:
        location: código ICAO do aeroporto (ex: SBBR, SBGL)
        data_ini: data inicial no formato YYYYMMDDHH (opcional)
        data_fim: data final no formato YYYYMMDDHH (opcional)
    """
    try:
        api_url = os.getenv('REDEMET_API_URL', 'https://api-redemet.decea.mil.br/mensagens/taf')
        api_key = os.getenv('REDEMET_API_KEY')

        if not api_key:
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'erro',
                'location': location,
                'error': 'REDEMET_API_KEY não configurada no .env'
            }

        url = f"{api_url}/{location}"

        params = {
            'api_key': api_key,
            'fim_linha': 'texto'
        }

        if data_ini:
            params['data_ini'] = data_ini
        if data_fim:
            params['data_fim'] = data_fim

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Processar resposta da REDEMET
        if data.get('status') and data.get('data') and data.get('data').get('data'):
            tafs_list = data.get('data').get('data')
            results = []
            airport_id = get_airport_id(location)

            for taf_record in tafs_list:
                taf_text = taf_record.get('mens', '')

                db_id = None
                if taf_text and airport_id:
                    db_id = save_taf_redemet(
                        timestamp,
                        taf_text,
                        airport_id,
                        taf_record.get('validade_inicial'),
                        taf_record.get('validade_final'),
                        taf_record.get('recebimento')
                    )

                results.append({
                    'taf_data': taf_text,
                    'validade_inicial': taf_record.get('validade_inicial'),
                    'validade_final': taf_record.get('validade_final'),
                    'recebimento': taf_record.get('recebimento'),
                    'database_id': db_id
                })

            return {
                'timestamp': timestamp,
                'status': 'sucesso',
                'location': location,
                'total_records': len(tafs_list),
                'data': results
            }
        else:
            return {
                'timestamp': timestamp,
                'status': 'sucesso',
                'location': location,
                'message': 'Nenhum TAF encontrado',
                'data': []
            }

    except requests.exceptions.RequestException as error:
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'erro',
            'location': location,
            'error': str(error)
        }

async def fetch_all_airports_tomorrow():
    """
    Busca TAF de 30 aeroportos da API Tomorrow.io
    """
    print("Buscando TAFs dos 30 aeroportos na Tomorrow.io...")
    results = []

    for iata, _, _ in BRAZILIAN_AIRPORTS[:30]:
        result = await fetch_taf_tomorrow(iata)
        results.append(result)
        print(f"Tomorrow - {iata}: {result.get('status', 'erro')}")

    return results

async def fetch_all_airports_redemet():
    """
    Busca TAF de 30 aeroportos da API REDEMET
    """
    print("Buscando TAFs dos 30 aeroportos na REDEMET...")
    results = []

    for iata, _, _ in BRAZILIAN_AIRPORTS[:30]:
        result = await fetch_taf_redemet(iata)
        results.append(result)
        print(f"REDEMET - {iata}: {result.get('status', 'erro')}")

    return results

def read_airports_from_file(filepath: str):
    """
    Lê lista de aeroportos de um arquivo .txt
    Formato esperado: um código ICAO por linha

    Args:
        filepath: caminho do arquivo .txt

    Returns:
        Lista de códigos ICAO
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            airports = [line.strip().upper() for line in f if line.strip()]
        print(f"✓ {len(airports)} aeroportos lidos do arquivo: {filepath}")
        return airports
    except FileNotFoundError:
        print(f"✗ Arquivo não encontrado: {filepath}")
        raise
    except Exception as e:
        print(f"✗ Erro ao ler arquivo: {e}")
        raise

async def fetch_airports_from_file_both_apis(filepath: str):
    """
    Busca TAF de todos os aeroportos de um arquivo .txt de ambas as APIs

    Args:
        filepath: caminho do arquivo .txt com códigos ICAO

    Returns:
        Dicionário com resultados de ambas as APIs
    """
    airports = read_airports_from_file(filepath)
    tomorrow_results = []
    redemet_results = []

    print(f"\n{'='*60}")
    print(f"Buscando TAFs de {len(airports)} aeroportos")
    print(f"{'='*60}\n")

    # Inicializar aeroportos no banco de dados
    for airport_code in airports:
        add_airport(airport_code)

    # Buscar da Tomorrow.io
    print("--- Tomorrow.io ---")
    for airport_code in airports:
        result = await fetch_taf_tomorrow(airport_code)
        status = "✓" if result.get('status') == 'sucesso' else "✗"
        print(f"{status} {airport_code}: {result.get('status')}")
        tomorrow_results.append(result)

    # Buscar da REDEMET
    print("\n--- REDEMET ---")
    for airport_code in airports:
        result = await fetch_taf_redemet(airport_code)
        status = "✓" if result.get('status') == 'sucesso' else "✗"
        total = result.get('total_records', 0)
        print(f"{status} {airport_code}: {result.get('status')} ({total} registros)")
        redemet_results.append(result)

    # Contabilizar resultados
    tomorrow_success = sum(1 for r in tomorrow_results if r.get('status') == 'sucesso')
    tomorrow_error = len(tomorrow_results) - tomorrow_success

    redemet_success = sum(1 for r in redemet_results if r.get('status') == 'sucesso')
    redemet_error = len(redemet_results) - redemet_success

    return {
        'airports_count': len(airports),
        'tomorrow': {
            'success': tomorrow_success,
            'error': tomorrow_error,
            'results': tomorrow_results
        },
        'redemet': {
            'success': redemet_success,
            'error': redemet_error,
            'results': redemet_results
        },
        'summary': {
            'total_requests': len(airports) * 2,
            'total_success': tomorrow_success + redemet_success,
            'total_error': tomorrow_error + redemet_error,
            'success_rate': f"{((tomorrow_success + redemet_success) / (len(airports) * 2)) * 100:.1f}%"
        }
    }

async def fetch_taf():
    """
    Faz GET da API Tomorrow.io TAF (mantém compatibilidade com código antigo)
    """
    return await fetch_taf_tomorrow('SBRJ')
