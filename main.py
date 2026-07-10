import requests
from datetime import datetime, timezone
import json
import os
from dotenv import load_dotenv
from database import init_db, save_taf

load_dotenv()

async def fetch_taf():
    """
    Faz GET da API Tomorrow.io TAF
    Salva no banco de dados e retorna os dados ou erro
    """
    try:
        api_url = os.getenv('TOMORROW_IO_API_URL')

        params = {
            'location': 'SBRJ',
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
        if taf_text:
            db_id = save_taf(timestamp, taf_text)

        result = {
            'timestamp': timestamp,
            'status': 'sucesso',
            'location': 'SBRJ',
            'status_code': response.status_code,
            'data': data,
            'database_id': db_id if taf_text else None
        }

        print(json.dumps(result))
        return result

    except requests.exceptions.RequestException as error:
        result = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'erro',
            'error': str(error)
        }

        print(json.dumps(result))
        return result
