from fastapi import FastAPI
from fastapi.responses import JSONResponse
from main import fetch_taf
from database import init_db, get_latest_tafs, wake_up_database

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Inicializa banco de dados, executa migrations e backfill de METAR no startup"""
    import asyncio
    import os
    import sys

    print("\n" + "="*60)
    print("🚀 Iniciando API - TAF Service")
    print("="*60)

    # Inicializar banco de dados (não-fatal)
    print("[1/3] Inicializando banco de dados...")
    try:
        init_db()
        print("✓ Banco de dados inicializado")

        # Executar migrations
        print("[2/3] Executando migrations...")
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from manage_migrations import migrate
        if migrate():
            print("✓ Migrations executadas")
        else:
            print("⚠ Algumas migrations falharam (continuando)")
    except Exception as e:
        print(f"⚠ Aviso ao inicializar banco de dados: {e}")
        print("  A API continuará funcionando, mas algumas funcionalidades podem não estar disponíveis")

    # Backfill de METAR
    print("[3/3] Iniciando backfill de METAR...")
    try:
        from main import read_airports_from_file, fetch_metar_redemet
        from database import add_airport, get_airport_id, get_taf_time_range

        file_path = 'aiports.txt'
        if os.path.exists(file_path):
            airports = read_airports_from_file(file_path)
            backfill_count = 0

            # Semáforo para limitar concorrência
            semaphore = asyncio.Semaphore(16)

            async def backfill_single(airport_code):
                async with semaphore:
                    try:
                        airport_id = get_airport_id(airport_code)
                        if not airport_id:
                            airport_id = add_airport(airport_code)

                        min_ts, max_ts = get_taf_time_range(airport_id)
                        if not min_ts or not max_ts:
                            return 0

                        data_ini = min_ts.strftime('%Y%m%d%H')
                        data_fim = max_ts.strftime('%Y%m%d%H')

                        result = await fetch_metar_redemet(airport_code, data_ini, data_fim)
                        if result.get('status') == 'sucesso':
                            return result.get('total_records', 0)
                    except Exception as e:
                        print(f"  ⚠ Erro em {airport_code}: {str(e)[:50]}")
                    return 0

            # Executar backfill para todos os aeroportos
            results = await asyncio.gather(
                *[backfill_single(airport) for airport in airports],
                return_exceptions=True
            )

            backfill_count = sum(r for r in results if isinstance(r, int))
            print(f"✓ Backfill METAR concluído: {backfill_count} METARs salvos")
        else:
            print(f"⚠ Arquivo {file_path} não encontrado, pulando backfill")

    except Exception as e:
        print(f"⚠ Erro ao fazer backfill de METAR: {e}")
        print("  A API continuará funcionando normalmente")

    print("="*60)
    print("✓ API pronta para receber requisições!")
    print("="*60 + "\n")

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
    import asyncio
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

        # Buscar de Tomorrow.io em paralelo
        results = await asyncio.gather(
            *[fetch_taf_tomorrow(airport_code) for airport_code in airports],
            return_exceptions=True
        )

        # Filtrar exceções
        results = [r for r in results if not isinstance(r, Exception)]

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
    import asyncio
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

        # Buscar de REDEMET em paralelo
        results = await asyncio.gather(
            *[fetch_taf_redemet(airport_code) for airport_code in airports],
            return_exceptions=True
        )

        # Filtrar exceções
        results = [r for r in results if not isinstance(r, Exception)]

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
    import asyncio
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

        # Buscar de ambas as APIs em paralelo
        tomorrow_results = await asyncio.gather(
            *[fetch_taf_tomorrow(airport_code) for airport_code in airports],
            return_exceptions=True
        )
        redemet_results = await asyncio.gather(
            *[fetch_taf_redemet(airport_code) for airport_code in airports],
            return_exceptions=True
        )

        # Filtrar exceções
        tomorrow_results = [r for r in tomorrow_results if not isinstance(r, Exception)]
        redemet_results = [r for r in redemet_results if not isinstance(r, Exception)]

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
                        'error': len(tomorrow_results) - tomorrow_success
                    },
                    'redemet': {
                        'success': redemet_success,
                        'error': len(redemet_results) - redemet_success
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

@app.get("/api/metar/backfill")
async def metar_backfill():
    """
    Busca histórico de METAR dos últimos 20 dias para todos os aeroportos
    Executa em chunks de 150 por página
    """
    import asyncio
    import os
    from main import read_airports_from_file, fetch_metar_redemet
    from database import add_airport, get_airport_id, get_taf_time_range

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
        results = []
        total_metars = 0

        # Processar cada aeroporto
        for airport_code in airports:
            try:
                airport_id = get_airport_id(airport_code)
                if not airport_id:
                    airport_id = add_airport(airport_code)

                # Obter intervalo de tempo dos TAFs
                min_ts, max_ts = get_taf_time_range(airport_id)

                if not min_ts or not max_ts:
                    continue

                # Converter para formato REDEMET
                data_ini = min_ts.strftime('%Y%m%d%H')
                data_fim = max_ts.strftime('%Y%m%d%H')

                # Buscar METARs
                result = await fetch_metar_redemet(airport_code, data_ini, data_fim)

                if result.get('status') == 'sucesso':
                    count = result.get('total_records', 0)
                    total_metars += count
                    results.append({
                        'airport': airport_code,
                        'metar_count': count,
                        'pages': result.get('pages', 1),
                        'status': 'ok'
                    })

            except Exception as e:
                results.append({
                    'airport': airport_code,
                    'error': str(e),
                    'status': 'erro'
                })

        return JSONResponse(
            status_code=200,
            content={
                'success': True,
                'message': 'Backfill METAR concluído',
                'airports_processed': len(results),
                'total_metars': total_metars,
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

@app.get("/api/metar/report")
async def generate_metar_report():
    """
    Gera relatório PDF de assertividade TAF vs METAR
    Retorna URL do arquivo gerado
    """
    import os
    import subprocess
    from datetime import datetime, timezone

    try:
        # Executar script de geração de relatório
        result = subprocess.run(
            ['/usr/bin/python3', 'generate_report.py'],
            cwd='/home/luisrossi/Documents/Azul/taf_tomorrow',
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'error': 'Erro ao gerar relatório',
                    'details': result.stderr
                }
            )

        # Procurar arquivo PDF gerado
        cwd = '/home/luisrossi/Documents/Azul/taf_tomorrow'
        pdf_files = [f for f in os.listdir(cwd) if f.startswith('report_assertividade_') and f.endswith('.pdf')]

        if pdf_files:
            latest_pdf = max(pdf_files, key=lambda f: os.path.getctime(os.path.join(cwd, f)))
            return JSONResponse(
                status_code=200,
                content={
                    'success': True,
                    'message': 'Relatório gerado com sucesso',
                    'file': latest_pdf,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    'success': False,
                    'error': 'Nenhum PDF foi gerado',
                    'output': result.stdout
                }
            )

    except subprocess.TimeoutExpired:
        return JSONResponse(
            status_code=504,
            content={
                'success': False,
                'error': 'Timeout ao gerar relatório (> 5 min)'
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
