# Guia: Comparação de Assertividade TAF vs METAR

## Scripts e Ordem de Execução

### 1. **run_migration.py** (criar tabelas)
```bash
python3 run_migration.py
```
Cria a tabela `metar_redemet` no banco de dados.

### 2. **backfill_metar.py** (preencher histórico de METAR)
```bash
python3 backfill_metar.py
```
- Lê os 122 aeroportos de `aiports.txt`
- Para cada aeroporto, busca o período de TAF já coletado
- Requisita o METAR histórico da REDEMET para aquele período
- Salva os METARs no banco

**Tempo estimado:** 5-15 minutos (depende da conexão e da API REDEMET)

### 3. **generate_report.py** (gerar PDF)
```bash
python3 generate_report.py
```
- Lê TAFs e METARs do banco
- Para cada aeroporto, calcula assertividade por fonte (Tomorrow.io vs DECEA)
- Gera relatório PDF com:
  - Sumário executivo (qual fonte é melhor)
  - Matrizes de confusão
  - Gráficos comparativos
  - Breakdown por aeroporto e fenômeno
  - Metodologia e premissas

**Saída:** `report_assertividade_YYYYMMDD_HHMMSS.pdf`

---

## Estrutura de Código

### database.py (extensões)
- `save_metar_redemet()` — salva METAR no banco
- `get_taf_time_range()` — obtém período de TAFs coletados

### main.py (novas funções)
- `fetch_metar_redemet(location, data_ini, data_fim)` — busca METAR da REDEMET

### assertividade.py (novo módulo)
- `parse_taf_header()` — extrai validade do TAF
- `extract_phenomena()` — lista fenômenos encontrados em texto
- `hourly_taf_phenomena()` — série hora a hora dos fenômenos previstos
- `metar_phenomena()` — fenômenos observados no METAR
- `compare_source()` — calcula TP/FP/FN/TN para uma fonte
- `ConfusionMatrix` — classe para métricas

### Tabela de Fenômenos Analisados
```
FZDZ, +FZDZ, -FZDZ,
-FZRA, FZRA, +FZRA,
FZFG, TS, +TS,
+RA, +SHRA, +SN,
+SHSN, +TSRA, TSRA
```

---

## Critério de Comparação

Para cada hora prevista por um TAF vs METAR observado:

| TAF | METAR | Resultado |
|---|---|---|
| Fenômeno previsto | Fenômeno observado | **Acerto (TP)** |
| Fenômeno previsto | Sem fenômeno | **Falso alarme (FP)** |
| Sem fenômeno | Fenômeno observado | **Evento perdido (FN)** |
| Sem fenômeno | Sem fenômeno | **Acerto (TN)** |

**Match:** Código idêntico (ex: "TS" só bate com "TS", não com "+TS")

---

## Resultados Esperados

Relatório PDF com:
- **Acurácia** (TP+TN) / Total
- **Precisão** TP / (TP+FP)
- **Recall** TP / (TP+FN)
- **F1-Score** 2×(Precisão×Recall) / (Precisão+Recall)

Comparação direto: Tomorrow.io vs DECEA (REDEMET)

---

## Ambiente

- Python 3.13+
- Dependências: `requests`, `python-dotenv`, `psycopg2-binary`, `matplotlib`, `reportlab`
- BD: PostgreSQL (Neon via `DATABASE_URL` do `.env`)
- API: REDEMET com chave em `REDEMET_API_KEY`

---

## Troubleshooting

### Tabela metar_redemet não existe
```bash
python3 run_migration.py
```

### ModuleNotFoundError
```bash
pip install -r requirements.txt
```

### Conexão banco falha
Verificar `DATABASE_URL` e `REDEMET_API_KEY` no `.env`
