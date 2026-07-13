import subprocess
import os

DATABASE_URLS = [
    # Original
    "postgresql://neondb_owner:npg_9vbUn6SiuYco@ep-orange-tree-ats6qzdg-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
    # Sem channel_binding
    "postgresql://neondb_owner:npg_9vbUn6SiuYco@ep-orange-tree-ats6qzdg-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require",
    # Com sslmode=prefer
    "postgresql://neondb_owner:npg_9vbUn6SiuYco@ep-orange-tree-ats6qzdg-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=prefer",
]

print("Testando diferentes variações de connection string...\n")

for i, url in enumerate(DATABASE_URLS, 1):
    print(f"Tentativa {i}: ", end="")
    # Tira a senha para exibir
    display_url = url.replace("npg_9vbUn6SiuYco", "****")
    print(display_url[:80] + "...")
    
    try:
        # Tenta com psql
        result = subprocess.run(
            ["psql", url, "-c", "SELECT 1;"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("  ✓ SUCESSO!\n")
        else:
            error = result.stderr[:150]
            print(f"  ✗ FALHOU: {error}\n")
    except FileNotFoundError:
        print("  ⚠ psql não encontrado, pulando...\n")
    except subprocess.TimeoutExpired:
        print("  ✗ TIMEOUT\n")
    except Exception as e:
        print(f"  ✗ ERRO: {e}\n")
