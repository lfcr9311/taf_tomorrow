from fastapi import FastAPI
from fastapi.responses import JSONResponse
from main import fetch_taf
from database import init_db, get_latest_tafs, wake_up_database

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Inicializa banco de dados e executa migrations no startup"""
    try:
        print("\n" + "="*60)
        print("🚀 Iniciando API - TAF Service")
        print("="*60)

        print("[1/2] Inicializando banco de dados...")
        init_db()
        print("✓ Banco de dados inicializado")

        # Executar migrations
        print("[2/2] Executando migrations...")
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from manage_migrations import migrate
        migrate()
        print("✓ Migrations executadas")

        print("="*60)
        print("✓ API pronta para receber requisições!")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n✗ Erro ao inicializar: {e}\n")
        raise

@app.get("/")
async def health_check():
    """Health check da API"""
    return {'status': 'ok', 'message': 'TAF API - Vercel Cron Active'}

@app.get("/health")
async def ping():
    """Verificar status da API"""
    return {'status': 'healthy', 'service': 'taf-service'}

@app.get("/api/wake-up")
async def wake_up():
    """
    Acorda o banco Neon do autosuspend
    Chamado pelo cron job antes de executar buscas
    """
    result = wake_up_database(max_retries=3, retry_delay=2)

    status_code = 200 if result['success'] else 503
    return JSONResponse(
        status_code=status_code,
        content={
            'success': result['success'],
            'message': result['message'],
            'attempts': result.get('attempts', 0)
        }
    )

@app.get("/api/taf/single")
async def get_single_taf():
    """
    Busca TAF do aeroporto padrão (SBRJ) na Tomorrow.io
    """
    result = await fetch_taf()

    if result['status'] == 'sucesso':
        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'message': 'TAF obtido com sucesso',
                'data': result
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': result['error'],
                'timestamp': result['timestamp']
            }
        )

@app.get("/api/taf/history")
async def get_taf_history(limit: int = 10):
    """
    Lista os últimos TAFs salvos no banco de dados

    Parâmetros:
    - limit: quantidade máxima de registros (padrão: 10)
    """
    try:
        tafs = get_latest_tafs(limit=limit)
        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'count': len(tafs),
                'data': tafs
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )

@app.get("/api/taf/tomorrow")
async def fetch_tomorrow_provider():
    """
    Busca TAF da API Tomorrow.io para aeroportos do arquivo aiports.txt
    """
    import os
    from main import fetch_taf_tomorrow, read_airports_from_file, add_airport, get_airport_id

    file_path = 'aiports.txt'

    if not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content={
                'success': False,
                'error': f'Arquivo não encontrado: {file_path}'
            }
        )

    try:
        airports = read_airports_from_file(file_path)

        # Inicializar aeroportos
        for airport_code in airports:
            add_airport(airport_code)

        # Buscar de Tomorrow.io
        results = []
        for airport_code in airports:
            result = await fetch_taf_tomorrow(airport_code)
            results.append(result)

        success_count = sum(1 for r in results if r.get('status') == 'sucesso')
        error_count = sum(1 for r in results if r.get('status') == 'erro')

        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'provider': 'tomorrow.io',
                'total_airports': len(airports),
                'success': success_count,
                'error': error_count,
                'results': results
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )

@app.get("/api/taf/redemet")
async def fetch_redemet_provider():
    """
    Busca TAF da API REDEMET para aeroportos do arquivo aiports.txt
    """
    import os
    from main import fetch_taf_redemet, read_airports_from_file, add_airport, get_airport_id

    file_path = 'aiports.txt'

    if not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content={
                'success': False,
                'error': f'Arquivo não encontrado: {file_path}'
            }
        )

    try:
        airports = read_airports_from_file(file_path)

        # Inicializar aeroportos
        for airport_code in airports:
            add_airport(airport_code)

        # Buscar de REDEMET
        results = []
        for airport_code in airports:
            result = await fetch_taf_redemet(airport_code)
            results.append(result)

        success_count = sum(1 for r in results if r.get('status') == 'sucesso')
        error_count = sum(1 for r in results if r.get('status') == 'erro')

        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'provider': 'redemet',
                'total_airports': len(airports),
                'success': success_count,
                'error': error_count,
                'results': results
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )

@app.get("/api/taf/batch")
async def fetch_batch():
    """
    Busca TAF de ambas as APIs (Tomorrow.io + REDEMET) para aeroportos do arquivo aiports.txt
    """
    import os
    from main import fetch_taf_tomorrow, fetch_taf_redemet, read_airports_from_file, add_airport

    file_path = 'aiports.txt'

    if not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content={
                'success': False,
                'error': f'Arquivo não encontrado: {file_path}'
            }
        )

    try:
        airports = read_airports_from_file(file_path)

        # Inicializar aeroportos
        for airport_code in airports:
            add_airport(airport_code)

        # Buscar de ambas as APIs
        tomorrow_results = []
        redemet_results = []

        for airport_code in airports:
            tomorrow_results.append(await fetch_taf_tomorrow(airport_code))
            redemet_results.append(await fetch_taf_redemet(airport_code))

        tomorrow_success = sum(1 for r in tomorrow_results if r.get('status') == 'sucesso')
        redemet_success = sum(1 for r in redemet_results if r.get('status') == 'sucesso')

        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'message': 'Busca concluída em ambas as APIs',
                'total_airports': len(airports),
                'providers': {
                    'tomorrow': {
                        'success': tomorrow_success,
                        'error': len(airports) - tomorrow_success
                    },
                    'redemet': {
                        'success': redemet_success,
                        'error': len(airports) - redemet_success
                    }
                },
                'results': {
                    'tomorrow': tomorrow_results,
                    'redemet': redemet_results
                }
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )

@app.get("/api/taf/file")
async def fetch_from_file(file_path: str = None):
    """
    Busca TAF de aeroportos listados em um arquivo .txt

    Parâmetros:
    - file_path: caminho do arquivo .txt com códigos ICAO

    Exemplo: GET /api/taf/file?file_path=aeroportos.txt
    """
    from main import fetch_airports_from_file_both_apis

    if not file_path:
        return JSONResponse(
            status_code=400,
            content={
                'success': False,
                'error': 'Parâmetro file_path é obrigatório',
                'example': '/api/taf/file?file_path=aeroportos.txt'
            }
        )

    try:
        results = await fetch_airports_from_file_both_apis(file_path)

        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'message': f'Busca concluída para {results["airports_count"]} aeroportos',
                'data': results
            }
        )
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={
                'success': False,
                'error': f'Arquivo não encontrado: {file_path}'
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )

@app.get("/api/taf/cron/fetch")
async def cron_fetch_from_file():
    """
    Endpoint de cron para buscar TAF de aeroportos (procura aiports.txt)
    Executado automaticamente pelo Vercel Cron
    """
    import os
    from main import fetch_airports_from_file_both_apis

    file_path = 'aiports.txt'

    if not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content={
                'success': False,
                'error': f'Arquivo não encontrado: {file_path}',
                'message': 'Crie um arquivo aeroportos.txt na raiz do projeto'
            }
        )

    try:
        results = await fetch_airports_from_file_both_apis(file_path)

        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'message': f'Cron execution completed for {results["airports_count"]} airports',
                'summary': results['summary'],
                'providers': {
                    'tomorrow': {
                        'success': results['tomorrow']['success'],
                        'error': results['tomorrow']['error']
                    },
                    'redemet': {
                        'success': results['redemet']['success'],
                        'error': results['redemet']['error']
                    }
                }
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': str(e)
            }
        )
