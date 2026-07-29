#!/usr/bin/env python3
"""
Gera relatório PDF de assertividade TAF vs METAR
"""

from datetime import datetime, timezone
import psycopg2
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from io import BytesIO
import os

from database import get_db_connection
from main import read_airports_from_file
from assertividade import compare_source, ConfusionMatrix

def get_airport_id(conn, iata_code):
    """Busca ID do aeroporto"""
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM airports WHERE iata_code = %s', (iata_code,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

def aggregate_metrics(matrices):
    """Agrega múltiplas matrizes em uma única"""
    agg = ConfusionMatrix()
    for m in matrices:
        agg.tp += m.tp
        agg.fp += m.fp
        agg.fn += m.fn
        agg.tn += m.tn
        for phenom, counts in m.phenomena_counts.items():
            if phenom not in agg.phenomena_counts:
                agg.phenomena_counts[phenom] = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0}
            agg.phenomena_counts[phenom]['tp'] += counts['tp']
            agg.phenomena_counts[phenom]['fp'] += counts['fp']
            agg.phenomena_counts[phenom]['fn'] += counts['fn']
            agg.phenomena_counts[phenom]['tn'] += counts['tn']
    return agg

def create_metrics_chart(tomorrow_matrix, decea_matrix):
    """Cria gráfico comparando métricas das duas fontes"""
    fig, ax = plt.subplots(figsize=(10, 6))

    metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    tomorrow_vals = [
        tomorrow_matrix.accuracy(),
        tomorrow_matrix.precision(),
        tomorrow_matrix.recall(),
        tomorrow_matrix.f1()
    ]
    decea_vals = [
        decea_matrix.accuracy(),
        decea_matrix.precision(),
        decea_matrix.recall(),
        decea_matrix.f1()
    ]

    x = range(len(metrics))
    width = 0.35

    ax.bar([i - width/2 for i in x], tomorrow_vals, width, label='Tomorrow.io', color='#4472C4')
    ax.bar([i + width/2 for i in x], decea_vals, width, label='DECEA', color='#ED7D31')

    ax.set_ylabel('Score')
    ax.set_title('Comparação de Métrica: Tomorrow.io vs DECEA')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.legend()
    ax.set_ylim(0, 1.1)
    ax.grid(axis='y', alpha=0.3)

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return buf

def create_confusion_matrix_table(matrix, title):
    """Cria tabela de matriz de confusão"""
    data = [
        ['', 'METAR Sim', 'METAR Não'],
        ['TAF Sim', str(matrix.tp), str(matrix.fp)],
        ['TAF Não', str(matrix.fn), str(matrix.tn)]
    ]

    table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    return table

def generate_pdf_report(tomorrow_matrices, decea_matrices):
    """
    Gera relatório PDF
    """
    # Agregar métricas por fonte
    tomorrow_total = aggregate_metrics(tomorrow_matrices.values())
    decea_total = aggregate_metrics(decea_matrices.values())

    # Criar PDF
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    pdf_filename = f'report_assertividade_{timestamp}.pdf'

    doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1F4E78'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph('Relatório de Assertividade TAF vs METAR', title_style))
    story.append(Spacer(1, 0.3*inch))

    # Timestamp
    timestamp_text = f"Gerado em: {datetime.now(timezone.utc).isoformat()}"
    story.append(Paragraph(timestamp_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    # Sumário executivo
    story.append(Paragraph('1. Sumário Executivo', styles['Heading2']))

    summary_text = f"""
    <b>Fonte mais assertiva:</b> {'Tomorrow.io' if tomorrow_total.accuracy() > decea_total.accuracy() else 'DECEA'}<br/>
    <b>Acurácia Tomorrow.io:</b> {tomorrow_total.accuracy():.2%}<br/>
    <b>Acurácia DECEA:</b> {decea_total.accuracy():.2%}<br/>
    <b>Período analisado:</b> 20 dias de dados<br/>
    <b>Aeroportos:</b> {len(tomorrow_matrices)} com dados
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    # Métricas agregadas
    story.append(Paragraph('2. Métricas Agregadas', styles['Heading2']))

    metrics_data = [
        ['Métrica', 'Tomorrow.io', 'DECEA'],
        ['Accuracy', f"{tomorrow_total.accuracy():.2%}", f"{decea_total.accuracy():.2%}"],
        ['Precision', f"{tomorrow_total.precision():.2%}", f"{decea_total.precision():.2%}"],
        ['Recall', f"{tomorrow_total.recall():.2%}", f"{decea_total.recall():.2%}"],
        ['F1-Score', f"{tomorrow_total.f1():.2%}", f"{decea_total.f1():.2%}"]
    ]

    metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.3*inch))

    # Matrizes de confusão
    story.append(Paragraph('3. Matrizes de Confusão', styles['Heading2']))

    story.append(Paragraph('Tomorrow.io', styles['Heading3']))
    story.append(create_confusion_matrix_table(tomorrow_total, 'Tomorrow.io'))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph('DECEA', styles['Heading3']))
    story.append(create_confusion_matrix_table(decea_total, 'DECEA'))
    story.append(Spacer(1, 0.3*inch))

    # Gráfico comparativo
    story.append(PageBreak())
    story.append(Paragraph('4. Comparação Gráfica', styles['Heading2']))

    chart_buf = create_metrics_chart(tomorrow_total, decea_total)
    story.append(Image(chart_buf, width=5.5*inch, height=3.3*inch))
    story.append(Spacer(1, 0.3*inch))

    # Metodologia
    story.append(PageBreak())
    story.append(Paragraph('5. Metodologia', styles['Heading2']))

    methodology_text = """
    <b>Fenômenos analisados:</b><br/>
    Foram selecionados fenômenos significativos para operações aéreas:
    FZDZ, +FZDZ, -FZDZ, -FZRA, FZRA, +FZRA, FZFG, TS, +TS, +RA, +SHRA, +SN, +SHSN, +TSRA, TSRA<br/>
    <br/>
    <b>Critério de comparação:</b><br/>
    Para cada hora prevista por um TAF, foi encontrado o METAR observado daquela hora e comparado:
    <br/>
    • <b>Acerto (TP):</b> TAF previu fenômeno E METAR confirmou<br/>
    • <b>Falso alarme (FP):</b> TAF previu fenômeno E METAR NÃO confirmou<br/>
    • <b>Evento perdido (FN):</b> TAF NÃO previu fenômeno E METAR confirmou<br/>
    • <b>Acerto (TN):</b> TAF NÃO previu E METAR também NÃO teve<br/>
    <br/>
    <b>Match por código:</b><br/>
    Comparação exata (não por família) — "TS" só bate com "TS", não com "+TS" ou "TSRA".<br/>
    <br/>
    <b>Período e dados:</b><br/>
    Análise de 20 dias de dados TAF histórico contra METAR observado do REDEMET.
    """
    story.append(Paragraph(methodology_text, styles['Normal']))

    # Ficha técnica
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph('6. Ficha Técnica', styles['Heading2']))

    tech_data = [
        ['Métrica', 'Tomorrow.io', 'DECEA'],
        ['TP', str(tomorrow_total.tp), str(decea_total.tp)],
        ['FP', str(tomorrow_total.fp), str(decea_total.fp)],
        ['FN', str(tomorrow_total.fn), str(decea_total.fn)],
        ['TN', str(tomorrow_total.tn), str(decea_total.tn)],
    ]

    tech_table = Table(tech_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(tech_table)

    # Gerar PDF
    doc.build(story)
    print(f"✓ Relatório gerado: {pdf_filename}")
    return pdf_filename

def main():
    """
    Executa análise completa
    """
    print("\n" + "="*60)
    print("Gerando Relatório de Assertividade TAF vs METAR")
    print("="*60 + "\n")

    # Conectar ao banco
    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"✗ Erro ao conectar no banco: {e}")
        return

    # Ler aeroportos
    airports = read_airports_from_file('aiports.txt')
    print(f"Analisando {len(airports)} aeroportos...\n")

    tomorrow_matrices = {}
    decea_matrices = {}

    # Analisar cada aeroporto
    for airport_code in airports:
        airport_id = get_airport_id(conn, airport_code)
        if not airport_id:
            continue

        try:
            tomorrow_matrix = compare_source(airport_id, 'taf_tomorrow', conn)
            decea_matrix = compare_source(airport_id, 'taf_redemet', conn)

            tomorrow_matrices[airport_code] = tomorrow_matrix
            decea_matrices[airport_code] = decea_matrix

            status_tm = "✓" if tomorrow_matrix.tp + tomorrow_matrix.fp + tomorrow_matrix.fn + tomorrow_matrix.tn > 0 else "○"
            status_dec = "✓" if decea_matrix.tp + decea_matrix.fp + decea_matrix.fn + decea_matrix.tn > 0 else "○"
            print(f"{status_tm} {status_dec} {airport_code}: Tomorrow acc={tomorrow_matrix.accuracy():.1%}, DECEA acc={decea_matrix.accuracy():.1%}")

        except Exception as e:
            print(f"✗ Erro ao processar {airport_code}: {e}")
            continue

    conn.close()

    if not tomorrow_matrices or not decea_matrices:
        print("✗ Nenhum dado para gerar relatório")
        return

    # Gerar PDF
    generate_pdf_report(tomorrow_matrices, decea_matrices)

if __name__ == '__main__':
    main()
