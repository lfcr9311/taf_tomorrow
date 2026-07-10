from fastapi import FastAPI
from fastapi.responses import JSONResponse
from main import fetch_taf
from database import init_db, get_latest_tafs

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Inicializa banco de dados no startup"""
    try:
        init_db()
    except Exception as e:
        print(f"Aviso: Não foi possível inicializar o banco: {e}")

@app.get("/api/taf")
async def get_taf():
    """
    Endpoint que faz GET da API Tomorrow.io TAF
    Pode ser chamado manualmente ou pelo cron job
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

@app.get("/api/tafs")
async def list_tafs(limit: int = 10):
    """
    Lista os últimos TAFs salvos no banco de dados
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

@app.get("/")
async def root():
    """Health check"""
    return {'status': 'ok', 'message': 'API Tomorrow.io TAF - Vercel Cron'}

