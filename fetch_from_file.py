import asyncio
import json
import sys
from main import fetch_airports_from_file_both_apis
from database import init_db

async def main():
    """
    Busca TAF de aeroportos listados em um arquivo .txt
    Uso: python fetch_from_file.py <caminho_do_arquivo.txt>
    """

    if len(sys.argv) < 2:
        print("Uso: python fetch_from_file.py <caminho_do_arquivo.txt>")
        print("\nExemplo:")
        print("  python fetch_from_file.py aeroportos.txt")
        print("\nO arquivo deve conter um código ICAO por linha:")
        print("  SBRJ")
        print("  SBSP")
        print("  SBCT")
        sys.exit(1)

    filepath = sys.argv[1]

    print("=" * 60)
    print("Coleta de TAFs - Arquivo de Aeroportos")
    print("=" * 60)

    # Inicializa banco de dados
    init_db()

    # Busca TAFs de ambas as APIs
    try:
        results = await fetch_airports_from_file_both_apis(filepath)

        # Relatório final
        print("\n" + "=" * 60)
        print("RELATÓRIO FINAL")
        print("=" * 60)

        print(f"\nTotal de aeroportos processados: {results['airports_count']}")
        print(f"Total de requisições: {results['summary']['total_requests']}")

        print(f"\nTomorrow.io:")
        print(f"  ✓ Sucesso: {results['tomorrow']['success']}")
        print(f"  ✗ Erro: {results['tomorrow']['error']}")

        print(f"\nREDEMET:")
        print(f"  ✓ Sucesso: {results['redemet']['success']}")
        print(f"  ✗ Erro: {results['redemet']['error']}")

        print(f"\nResumo Geral:")
        print(f"  Total de sucesso: {results['summary']['total_success']}/{results['summary']['total_requests']}")
        print(f"  Taxa de sucesso: {results['summary']['success_rate']}")

        # Salva relatório detalhado
        output_file = filepath.replace('.txt', '_results.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n✓ Relatório salvo em: {output_file}")

    except FileNotFoundError as e:
        print(f"\n✗ Erro: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
