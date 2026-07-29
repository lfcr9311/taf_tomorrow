#!/usr/bin/env python3
"""
Teste de backfill de METAR para um único aeroporto
Para validar que o fluxo funciona antes de rodar em massa
"""

import asyncio
from datetime import datetime, timezone
from main import read_airports_from_file, fetch_metar_redemet
from database import add_airport, get_airport_id

async def test_single_airport():
    """
    Testa backfill para o primeiro aeroporto apenas
    """
    airports = read_airports_from_file('aiports.txt')

    if not airports:
        print("✗ Nenhum aeroporto lido")
        return

    airport_code = airports[0]
    print(f"Testando backfill para: {airport_code}\n")

    # Adicionar aeroporto
    airport_id = get_airport_id(airport_code)
    if not airport_id:
        airport_id = add_airport(airport_code)

    print(f"Airport ID: {airport_id}")

    # Buscar METARs com período grande para teste
    # Usando período fixo para teste: 2024-07-09 a 2024-07-29 (20 dias)
    data_ini = "2024070900"  # 2024-07-09 00:00
    data_fim = "2024072900"  # 2024-07-29 00:00

    print(f"Solicitando METARs de {data_ini} a {data_fim}...\n")

    result = await fetch_metar_redemet(airport_code, data_ini, data_fim)

    print("\nResultado:")
    print(f"  Status: {result.get('status')}")
    print(f"  Total de METARs: {result.get('total_records', 0)}")

    if result.get('status') == 'sucesso':
        print(f"  ✓ Backfill concluído com sucesso!")

        # Mostrar amostra dos METARs salvos
        if result.get('data'):
            print(f"\n  Amostra de dados salvos:")
            for i, metar in enumerate(result.get('data', [])[:3]):
                print(f"    [{i+1}] Observação: {metar.get('observacao')}")
                print(f"        Recebimento: {metar.get('recebimento')}")
                print(f"        ID DB: {metar.get('database_id')}")
    else:
        error = result.get('error', result.get('message', 'Erro desconhecido'))
        print(f"  ✗ Erro: {error}")

if __name__ == '__main__':
    print("="*60)
    print("TESTE DE BACKFILL DE METAR - AEROPORTO ÚNICO")
    print("="*60 + "\n")

    asyncio.run(test_single_airport())
