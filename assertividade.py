"""
Parser e cálculo de assertividade de TAF vs METAR
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Dict, Set, Tuple, List

PHENOMENA = [
    "FZDZ", "+FZDZ", "-FZDZ",
    "-FZRA", "FZRA", "+FZRA",
    "FZFG", "TS", "+TS",
    "+RA", "+SHRA", "+SN",
    "+SHSN", "+TSRA", "TSRA"
]

class TafSegment:
    def __init__(self, seg_type: str, start_time=None, end_time=None, phenomena=None):
        self.type = seg_type  # 'base', 'FM', 'BECMG', 'TEMPO', 'PROB'
        self.start_time = start_time
        self.end_time = end_time
        self.phenomena = phenomena if phenomena else set()

def parse_taf_header(taf_text: str, reference_dt: datetime) -> Tuple[datetime, datetime, datetime]:
    """
    Extrai data/hora de emissão e validade do TAF

    Args:
        taf_text: texto do TAF
        reference_dt: timestamp de referência para resolver o mês/ano

    Returns:
        (issue_dt, valid_start, valid_end) como datetime UTC
    """
    # Formato esperado: "TAF SBRF 121720Z 1218/1324 ..."
    # DDHHMMZ = dia/hora/minuto/Z da emissão
    # DDHH/DDHH = dia/hora de validade inicial e final

    # Extrair DDHHMMZ
    match_header = re.search(r'TAF\s+[A-Z]{4}\s+(\d{2})(\d{2})(\d{2})Z', taf_text)
    if not match_header:
        raise ValueError("Não foi possível extrair cabeçalho TAF")

    issue_day, issue_hour, issue_min = int(match_header.group(1)), int(match_header.group(2)), int(match_header.group(3))

    # Extrair validade DDHH/DDHH
    match_valid = re.search(r'(\d{2})(\d{2})/(\d{2})(\d{2})', taf_text)
    if not match_valid:
        raise ValueError("Não foi possível extrair validade do TAF")

    valid_start_day, valid_start_hour, valid_end_day, valid_end_hour = \
        int(match_valid.group(1)), int(match_valid.group(2)), \
        int(match_valid.group(3)), int(match_valid.group(4))

    # Clipping de valores inválidos
    issue_day = max(1, min(issue_day, 31))
    issue_hour = max(0, min(issue_hour, 23))
    issue_min = max(0, min(issue_min, 59))
    valid_start_day = max(1, min(valid_start_day, 31))
    valid_start_hour = max(0, min(valid_start_hour, 23))
    valid_end_day = max(1, min(valid_end_day, 31))
    valid_end_hour = max(0, min(valid_end_hour, 23))

    ref_year = reference_dt.year
    ref_month = reference_dt.month

    # Issue datetime
    try:
        issue_dt = datetime(ref_year, ref_month, issue_day, issue_hour, issue_min, 0, tzinfo=timezone.utc)
    except ValueError:
        issue_dt = datetime(ref_year, ref_month, min(issue_day, 28), issue_hour, issue_min, 0, tzinfo=timezone.utc)

    # Validade
    try:
        valid_start = datetime(ref_year, ref_month, valid_start_day, valid_start_hour, 0, 0, tzinfo=timezone.utc)
    except ValueError:
        valid_start = datetime(ref_year, ref_month, min(valid_start_day, 28), valid_start_hour, 0, 0, tzinfo=timezone.utc)

    try:
        if valid_end_day < valid_start_day:
            next_month = ref_month + 1 if ref_month < 12 else 1
            next_year = ref_year + 1 if ref_month == 12 else ref_year
            valid_end = datetime(next_year, next_month, valid_end_day, valid_end_hour, 0, 0, tzinfo=timezone.utc)
        else:
            valid_end = datetime(ref_year, ref_month, valid_end_day, valid_end_hour, 0, 0, tzinfo=timezone.utc)
    except ValueError:
        valid_end = datetime(ref_year, ref_month, min(valid_end_day, 28), valid_end_hour, 0, 0, tzinfo=timezone.utc)

    return issue_dt, valid_start, valid_end

def extract_phenomena(text: str) -> Set[str]:
    """
    Extrai todos os fenômenos da lista presente no texto
    """
    found = set()
    for phenom in PHENOMENA:
        if phenom in text:
            found.add(phenom)
    return found

def parse_taf_segments(taf_text: str) -> List[TafSegment]:
    """
    Quebra TAF em segmentos (BECMG, FM, TEMPO, PROB, base)

    Args:
        taf_text: texto do TAF

    Returns:
        Lista de TafSegment
    """
    segments = []

    # Remover cabeçalho e decomposição em linhas
    lines = taf_text.split()

    # Encontrar start da validade
    i = 0
    while i < len(lines):
        if re.match(r'\d{2}\d{2}/\d{2}\d{2}', lines[i]):
            i += 1
            break
        i += 1

    # Agrupar tokens até próxima palavra-chave
    current_group = []

    while i < len(lines):
        token = lines[i]

        # Detectar mudança de segmento
        if token.startswith('FM') or token.startswith('BECMG') or token.startswith('TEMPO') or token.startswith('PROB'):
            # Processar grupo anterior
            if current_group:
                phenomena = extract_phenomena(' '.join(current_group))
                segments.append(TafSegment('base', phenomena=phenomena))
                current_group = []

            # Processar novo segmento
            if token.startswith('FM'):
                # FM + DDHHMM
                m = re.match(r'FM(\d{2})(\d{2})(\d{2})', token)
                if m:
                    day, hour, minute = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    # Será resolvido em context com validade depois
                    seg_type = 'FM'
                    seg_time = (day, hour, minute)
                    i += 1
                    temp_group = []
                    while i < len(lines) and not re.match(r'^(FM|BECMG|TEMPO|PROB)', lines[i]):
                        temp_group.append(lines[i])
                        i += 1
                    phenomena = extract_phenomena(' '.join(temp_group))
                    # Armazenar para resolução depois
                    current_group = temp_group
                    segments.append(TafSegment(seg_type, phenomena=phenomena))
                    continue

            elif token.startswith('BECMG'):
                # BECMG + DDHH/DDHH
                m = re.search(r'BECMG\s*(\d{2})(\d{2})/(\d{2})(\d{2})', ' '.join(lines[i:i+2]))
                if m:
                    start_day, start_hour, end_day, end_hour = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
                    i += 1
                    temp_group = []
                    while i < len(lines) and not re.match(r'^(FM|BECMG|TEMPO|PROB)', lines[i]):
                        temp_group.append(lines[i])
                        i += 1
                    phenomena = extract_phenomena(' '.join(temp_group))
                    segments.append(TafSegment('BECMG', phenomena=phenomena))
                    continue

            elif token.startswith('TEMPO'):
                # TEMPO + DDHH/DDHH
                m = re.search(r'TEMPO\s*(\d{2})(\d{2})/(\d{2})(\d{2})', ' '.join(lines[i:i+2]))
                if m:
                    start_day, start_hour, end_day, end_hour = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
                    i += 1
                    temp_group = []
                    while i < len(lines) and not re.match(r'^(FM|BECMG|TEMPO|PROB)', lines[i]):
                        temp_group.append(lines[i])
                        i += 1
                    phenomena = extract_phenomena(' '.join(temp_group))
                    segments.append(TafSegment('TEMPO', phenomena=phenomena))
                    continue

            elif token.startswith('PROB'):
                # PROB + NN + TEMPO
                m = re.match(r'PROB(\d{2})', token)
                if m:
                    i += 1
                    temp_group = []
                    while i < len(lines) and not re.match(r'^(FM|BECMG|TEMPO|PROB)', lines[i]):
                        temp_group.append(lines[i])
                        i += 1
                    phenomena = extract_phenomena(' '.join(temp_group))
                    segments.append(TafSegment('PROB', phenomena=phenomena))
                    continue
        else:
            current_group.append(token)
            i += 1

    # Adicionar último grupo
    if current_group:
        phenomena = extract_phenomena(' '.join(current_group))
        segments.append(TafSegment('base', phenomena=phenomena))

    return segments

def hourly_taf_phenomena(taf_text: str, reference_dt: datetime) -> Dict[datetime, Set[str]]:
    """
    Monta série hora a hora dos fenômenos previstos no TAF

    Args:
        taf_text: texto do TAF
        reference_dt: timestamp de referência (timestamp de coleta)

    Returns:
        Dicionário mapeando datetime -> set de fenômenos
    """
    try:
        issue_dt, valid_start, valid_end = parse_taf_header(taf_text, reference_dt)
    except ValueError:
        return {}

    segments = parse_taf_segments(taf_text)

    # Montar série hora a hora
    hourly = {}
    current_hour = valid_start
    current_phenomena = set()

    # Processar segmentos base e FM como substituição
    base_phenomena = set()
    for seg in segments:
        if seg.type in ['base', 'FM', 'BECMG']:
            base_phenomena = seg.phenomena.copy()
            break

    current_phenomena = base_phenomena.copy()

    while current_hour <= valid_end:
        hourly[current_hour] = current_phenomena.copy()
        current_hour += timedelta(hours=1)

    # Aplicar TEMPO/PROB como sobreposição
    for seg in segments:
        if seg.type in ['TEMPO', 'PROB']:
            # TEMPO sobrepõe durante sua janela
            # Simplificação: aplicamos para toda a série (seria preciso extrair janelas exatas)
            current_phenomena.update(seg.phenomena)
            for hour in hourly:
                if seg.phenomena:
                    hourly[hour].update(seg.phenomena)

    return hourly

def metar_phenomena(metar_text: str) -> Set[str]:
    """
    Extrai fenômenos do METAR

    Args:
        metar_text: texto do METAR

    Returns:
        Set de fenômenos encontrados
    """
    return extract_phenomena(metar_text)

class ConfusionMatrix:
    def __init__(self):
        self.tp = 0  # True Positive: TAF previu, METAR confirmou
        self.fp = 0  # False Positive: TAF previu, METAR não confirmou
        self.fn = 0  # False Negative: TAF não previu, METAR confirmou
        self.tn = 0  # True Negative: TAF não previu, METAR não confirmou
        self.phenomena_counts = {}  # breakdown por fenômeno

    def add_phenomena_count(self, phenom: str, tp=0, fp=0, fn=0, tn=0):
        if phenom not in self.phenomena_counts:
            self.phenomena_counts[phenom] = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}
        self.phenomena_counts[phenom]['tp'] += tp
        self.phenomena_counts[phenom]['fp'] += fp
        self.phenomena_counts[phenom]['fn'] += fn
        self.phenomena_counts[phenom]['tn'] += tn

    def accuracy(self):
        total = self.tp + self.fp + self.fn + self.tn
        return (self.tp + self.tn) / total if total > 0 else 0

    def precision(self):
        denominator = self.tp + self.fp
        return self.tp / denominator if denominator > 0 else 0

    def recall(self):
        denominator = self.tp + self.fn
        return self.tp / denominator if denominator > 0 else 0

    def f1(self):
        p = self.precision()
        r = self.recall()
        denominator = p + r
        return 2 * (p * r) / denominator if denominator > 0 else 0

def compare_source(airport_id: int, source_table: str, conn) -> ConfusionMatrix:
    """
    Compara um TAF de uma fonte contra o METAR observado para um aeroporto

    Args:
        airport_id: ID do aeroporto
        source_table: 'taf_tomorrow' ou 'taf_redemet'
        conn: conexão do banco

    Returns:
        ConfusionMatrix com métricas
    """
    cursor = conn.cursor()

    # Buscar todos os TAFs desse aeroporto e fonte
    cursor.execute(
        f'SELECT id, timestamp, taf_data FROM {source_table} WHERE airport_id = %s ORDER BY timestamp',
        (airport_id,)
    )
    tafs = cursor.fetchall()

    # Buscar todos os METARs desse aeroporto
    cursor.execute(
        'SELECT observacao, metar_data FROM metar_redemet WHERE airport_id = %s ORDER BY observacao',
        (airport_id,)
    )
    metars = cursor.fetchall()

    matrix = ConfusionMatrix()

    # Para cada TAF, comparar hora a hora com METAR
    for taf_id, taf_timestamp, taf_text in tafs:
        try:
            hourly_taf = hourly_taf_phenomena(taf_text, taf_timestamp)
        except Exception as e:
            continue

        # Para cada hora prevista no TAF
        for taf_hour, taf_phenom in hourly_taf.items():
            # Encontrar METAR mais próximo desta hora
            metar_phenom = set()
            for metar_hour, metar_text in metars:
                if metar_hour and abs((metar_hour - taf_hour).total_seconds()) < 3600:
                    metar_phenom = metar_phenomena(metar_text)
                    break

            # Aplicar critério de comparação
            # TAF mostrou e METAR mostrou = acerto
            # TAF mostrou e METAR não mostrou = erro (falso alarme)
            # TAF não mostrou e METAR mostrou = erro (evento perdido)
            # TAF não mostrou e METAR não mostrou = acerto

            if taf_phenom and metar_phenom:
                matrix.tp += 1
                for p in PHENOMENA:
                    if p in taf_phenom and p in metar_phenom:
                        matrix.add_phenomena_count(p, tp=1)
                    elif p in taf_phenom:
                        matrix.add_phenomena_count(p, fp=1)
                    elif p in metar_phenom:
                        matrix.add_phenomena_count(p, fn=1)
                    else:
                        matrix.add_phenomena_count(p, tn=1)
            elif taf_phenom and not metar_phenom:
                matrix.fp += 1
                for p in taf_phenom:
                    matrix.add_phenomena_count(p, fp=1)
            elif not taf_phenom and metar_phenom:
                matrix.fn += 1
                for p in metar_phenom:
                    matrix.add_phenomena_count(p, fn=1)
            else:
                matrix.tn += 1

    cursor.close()
    return matrix
