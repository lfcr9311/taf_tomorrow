import asyncio
import json
from main import fetch_all_airports_tomorrow, fetch_all_airports_redemet, init_airports
from database import init_db

async def main():
    """
    Executa a coleta de 30 aeroportos de ambas as APIs
    """
    print("=" * 60)
    print("Coleta de TAFs - 30 Aeroportos")
    print("=" * 60)

    # Inicializa banco de dados
    init_db()

    # Inicializa aeroportos no banco
    init_airports()

    # Busca TAFs da Tomorrow.io
    print("\n--- Buscando dados da Tomorrow.io ---")
    tomorrow_results = await fetch_all_airports_tomorrow()

    # Busca TAFs da REDEMET
    print("\n--- Buscando dados da REDEMET ---")
    redemet_results = await fetch_all_airports_redemet()

    # Contabiliza resultados
    tomorrow_success = sum(1 for r in tomorrow_results if r.get('status') == 'sucesso')
    tomorrow_error = sum(1 for r in tomorrow_results if r.get('status') == 'erro')

    redemet_success = sum(1 for r in redemet_results if r.get('status') == 'sucesso')
    redemet_error = sum(1 for r in redemet_results if r.get('status') == 'erro')

    # Relatório final
    print("\n" + "=" * 60)
    print("RELATÓRIO FINAL")
    print("=" * 60)
    print(f"\nTomorrow.io:")
    print(f"  ✓ Sucesso: {tomorrow_success}/30")
    print(f"  ✗ Erro: {tomorrow_error}/30")

    print(f"\nREDEMET:")
    print(f"  ✓ Sucesso: {redemet_success}/30")
    print(f"  ✗ Erro: {redemet_error}/30")

    print(f"\nTotal de aeroportos processados: 60 (30 Tomorrow + 30 REDEMET)")
    print(f"Taxa de sucesso combinada: {((tomorrow_success + redemet_success) / 60) * 100:.1f}%")

    # Salva relatório detalhado
    with open('aeroportos_results.json', 'w') as f:
        json.dump({
            'tomorrow_results': tomorrow_results,
            'redemet_results': redemet_results,
            'summary': {
                'tomorrow_success': tomorrow_success,
                'tomorrow_error': tomorrow_error,
                'redemet_success': redemet_success,
                'redemet_error': redemet_error
            }
        }, f, indent=2, default=str)

    print("\nRelatório salvo em: aeroportos_results.json")

if __name__ == '__main__':
    asyncio.run(main())
