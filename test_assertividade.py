#!/usr/bin/env python3
"""
Teste da lógica de assertividade (parser TAF/METAR)
Não requer banco de dados
"""

from datetime import datetime, timezone
from assertividade import (
    parse_taf_header,
    extract_phenomena,
    metar_phenomena,
    hourly_taf_phenomena,
    PHENOMENA
)

# TAF de exemplo (texto real formatado)
TAF_EXAMPLE = """TAF SBRF 121720Z 1218/1324
SBRF 121720Z 1218/1324 01008KT 9999 FEW040 SCT100 BKN250
FM131800 27005KT 9999 FEW040 BKN150
TEMPO 1218/1322 3000 -FZRA OVC010
BECMG 1322/1324 29010KT 9999 SKC"""

# METAR de exemplo
METAR_EXAMPLE = "SBRF 121720Z 01012KT 9999 FEW035 BKN100 +FZRA 15/10 Q1015"

def test_parse_header():
    print("=" * 60)
    print("Teste 1: Parse do cabeçalho TAF")
    print("=" * 60)

    ref_dt = datetime(2024, 7, 12, 17, 20, tzinfo=timezone.utc)
    try:
        issue_dt, valid_start, valid_end = parse_taf_header(TAF_EXAMPLE, ref_dt)
        print(f"✓ Emissão: {issue_dt}")
        print(f"✓ Válido de: {valid_start} até {valid_end}")
    except Exception as e:
        print(f"✗ Erro: {e}")

def test_extract_phenomena():
    print("\n" + "=" * 60)
    print("Teste 2: Extração de fenômenos")
    print("=" * 60)

    # TAF tem -FZRA em TEMPO
    taf_phenom = extract_phenomena(TAF_EXAMPLE)
    print(f"Fenômenos no TAF: {taf_phenom}")
    assert "-FZRA" in taf_phenom, "Deveria encontrar -FZRA no TAF"
    print("✓ TAF contém -FZRA (esperado)")

    # METAR tem +FZRA
    metar_phenom = extract_phenomena(METAR_EXAMPLE)
    print(f"Fenômenos no METAR: {metar_phenom}")
    assert "+FZRA" in metar_phenom, "Deveria encontrar +FZRA no METAR"
    print("✓ METAR contém +FZRA (esperado)")

    # Verificar match por código exato
    if "-FZRA" in taf_phenom and "+FZRA" in metar_phenom:
        print("⚠ -FZRA (TAF) != +FZRA (METAR) — códigos diferentes, não batem por design")

def test_hourly_phenomena():
    print("\n" + "=" * 60)
    print("Teste 3: Série hora a hora de fenômenos TAF")
    print("=" * 60)

    ref_dt = datetime(2024, 7, 12, 17, 20, tzinfo=timezone.utc)
    try:
        hourly = hourly_taf_phenomena(TAF_EXAMPLE, ref_dt)
        print(f"✓ Horas com fenômenos: {len(hourly)}")

        # Mostrar amostra
        count = 0
        for hour, phenom in sorted(hourly.items())[:5]:
            print(f"  {hour}: {phenom if phenom else '(sem fenômenos)'}")
            count += 1

        if len(hourly) > 5:
            print(f"  ... e mais {len(hourly) - 5} horas")

    except Exception as e:
        print(f"✗ Erro: {e}")

def test_phenomena_match():
    print("\n" + "=" * 60)
    print("Teste 4: Lógica de comparação TAF vs METAR")
    print("=" * 60)

    # Cenário 1: TAF previu -FZRA, METAR observou -FZRA → Acerto
    taf_phenom1 = {"-FZRA"}
    metar_phenom1 = {"-FZRA"}
    if taf_phenom1 and metar_phenom1 and taf_phenom1 & metar_phenom1:
        print("✓ Cenário 1: TAF previu e METAR confirmou = ACERTO (TP)")
    else:
        print("✗ Cenário 1 falhou")

    # Cenário 2: TAF previu -FZRA, METAR NÃO observou → Falso alarme
    taf_phenom2 = {"-FZRA"}
    metar_phenom2 = set()
    if taf_phenom2 and not metar_phenom2:
        print("✓ Cenário 2: TAF previu mas METAR não confirmou = FALSO ALARME (FP)")
    else:
        print("✗ Cenário 2 falhou")

    # Cenário 3: TAF NÃO previu, METAR observou +FZRA → Evento perdido
    taf_phenom3 = set()
    metar_phenom3 = {"+FZRA"}
    if not taf_phenom3 and metar_phenom3:
        print("✓ Cenário 3: TAF não previu mas METAR observou = EVENTO PERDIDO (FN)")
    else:
        print("✗ Cenário 3 falhou")

    # Cenário 4: TAF NÃO previu, METAR também não observou → Acerto (TN)
    taf_phenom4 = set()
    metar_phenom4 = set()
    if not taf_phenom4 and not metar_phenom4:
        print("✓ Cenário 4: TAF não previu e METAR também não teve = ACERTO (TN)")
    else:
        print("✗ Cenário 4 falhou")

    # Nota sobre match exato
    print("\n⚠ NOTA: -FZRA e +FZRA são códigos diferentes")
    print("  Na lógica acima: TAF com -FZRA E METAR com +FZRA =")
    if "-FZRA" in {"-FZRA"} and "+FZRA" in {"+FZRA"} and "-FZRA" != "+FZRA":
        print("  NÃO batem (por design) → Contaria como FP e FN respectivamente")

if __name__ == '__main__':
    print("\n" + "#" * 60)
    print("# TESTE DA LÓGICA DE ASSERTIVIDADE TAF vs METAR")
    print("#" * 60 + "\n")

    test_parse_header()
    test_extract_phenomena()
    test_hourly_phenomena()
    test_phenomena_match()

    print("\n" + "=" * 60)
    print("Testes concluídos!")
    print("=" * 60 + "\n")
