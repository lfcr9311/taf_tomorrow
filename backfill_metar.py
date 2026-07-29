#!/usr/bin/env python3
"""
Script para preencher histórico de METAR a partir da REDEMET
Busca METARs para toda a janela de TAFs já coletados para cada aeroporto
"""

import asyncio
from datetime import datetime, timezone
import sys
from main import read_airports_from_file, fetch_metar_redemet
from database import add_airport, get_taf_time_range, get_airport_id, init_db

def format_time_for_redemet(dt):
    """Converte datetime para formato YYYYMMDDHH usado pelo REDEMET"""
    if dt is None:
        return None
    return dt.strftime('%Y%m%d%H')

async def backfill_metar_for_airport(airport_code):
    """
    Busca e salva METARs para um aeroporto

    Args:
        airport_code: código ICAO do aeroporto

    Returns:
        Dict com status e contagem
    """
    try:
        # Adicionar aeroporto se não existe
        airport_id = get_airport_id(airport_code)
        if not airport_id:
            airport_id = add_airport(airport_code)

        # Obter intervalo de tempo dos TAFs
        min_ts, max_ts = get_taf_time_range(airport_id)

        if not min_ts or not max_ts:
            return {
                'airport': airport_code,
                'status': 'sem_tafs',
                'message': 'Nenhum TAF encontrado para este aeroporto'
            }

        # Converter para formato REDEMET (YYYYMMDDHH)
        data_ini = format_time_for_redemet(min_ts)
        data_fim = format_time_for_redemet(max_ts)

        print(f"  {airport_code}: buscando METARs de {data_ini} a {data_fim}")

        # Buscar METARs
        result = await fetch_metar_redemet(airport_code, data_ini, data_fim)

        if result.get('status') == 'sucesso':
            total = result.get('total_records', 0)
            pages = result.get('pages', 1)

            # Avisar se aeroporto grande tem menos de 350
            status_icon = "✓" if total >= 350 else "⚠" if total > 0 else "○"
            msg = f"  {status_icon} {airport_code}: {total} METARs ({pages} página(s))"
            if total < 350 and total > 0:
                msg += " [menor que 350]"
            print(msg)

            return {
                'airport': airport_code,
                'status': 'sucesso',
                'metar_count': total,
                'pages': pages,
                'period': f"{data_ini} a {data_fim}"
            }
        else:
            error = result.get('error', result.get('message', 'Erro desconhecido'))
            print(f"  ✗ {airport_code}: {error}")
            return {
                'airport': airport_code,
                'status': 'erro',
                'error': error
            }

    except Exception as e:
        print(f"  ✗ {airport_code}: Exceção - {str(e)}")
        return {
            'airport': airport_code,
            'status': 'exceção',
            'error': str(e)
        }

async def backfill_all_airports():
    """
    Busca METARs para todos os aeroportos do arquivo
    """
    # Inicializar banco se necessário
    init_db()

    # Ler lista de aeroportos
    airports = read_airports_from_file('aiports.txt')

    print(f"\n{'='*60}")
    print(f"Backfill METAR: {len(airports)} aeroportos")
    print(f"{'='*60}\n")

    # Buscar METARs em paralelo com limite (não sobrecarregar a API)
    # Usando um semáforo para limitar a 16 requisições simultâneas
    semaphore = asyncio.Semaphore(16)

    async def bounded_fetch(airport):
        async with semaphore:
            return await backfill_metar_for_airport(airport)

    results = await asyncio.gather(
        *[bounded_fetch(airport) for airport in airports],
        return_exceptions=True
    )

    # Processar resultados
    summary = {
        'sucesso': 0,
        'erro': 0,
        'sem_tafs': 0,
        'exceção': 0,
        'total_metars': 0
    }

    print(f"\n{'='*60}")
    print("RESUMO")
    print(f"{'='*60}\n")

    for result in results:
        if isinstance(result, Exception):
            print(f"✗ Erro geral: {result}")
            summary['exceção'] += 1
        elif result.get('status') == 'sucesso':
            summary['sucesso'] += 1
            summary['total_metars'] += result.get('metar_count', 0)
        elif result.get('status') == 'sem_tafs':
            summary['sem_tafs'] += 1
        else:
            summary['erro'] += 1

    print(f"Sucesso: {summary['sucesso']}")
    print(f"Erro: {summary['erro']}")
    print(f"Sem TAFs: {summary['sem_tafs']}")
    print(f"Exceção: {summary['exceção']}")
    print(f"Total de METARs salvos: {summary['total_metars']}")
    print(f"\nTimestamp: {datetime.now(timezone.utc).isoformat()}")

if __name__ == '__main__':
    asyncio.run(backfill_all_airports())
