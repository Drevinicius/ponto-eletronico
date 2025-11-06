# ponto/utils.py
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from django.utils import timezone
from datetime import datetime, timedelta
import pytz
from .models import RegistroPonto


def converter_para_manaus(timestamp_utc):
    """
    Converte timestamp UTC para UTC-4 (Manaus)
    """
    try:
        utc_tz = pytz.UTC
        manaus_tz = pytz.timezone('America/Manaus')

        # Se já é timezone aware, converte diretamente
        if timezone.is_aware(timestamp_utc):
            return timestamp_utc.astimezone(manaus_tz)
        else:
            # Se é naive, assume UTC e converte
            timestamp_utc = utc_tz.localize(timestamp_utc)
            return timestamp_utc.astimezone(manaus_tz)
    except Exception as e:
        print(f"Erro na conversão de timezone: {e}")
        return timestamp_utc


def gerar_relatorio_ponto_pdf(funcionario, data_inicio, data_fim):
    """
      Gera relatório de pontos em PDF para um funcionário específico
      """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        leftMargin=10 * mm,
        rightMargin=10 * mm
    )
    elements = []

    # Estilos
    styles = getSampleStyleSheet()

    estilo_cabecalho = ParagraphStyle(
        'Cabecalho',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10,
        textColor=colors.darkblue
    )

    estilo_dados = ParagraphStyle(
        'Dados',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=6
    )

    # LEGENDA DAS OBSERVAÇÕES - ATUALIZADA
    elements.append(Spacer(1, 8 * mm))
    legenda_texto = """
    <b>LEGENDA DAS OBSERVAÇÕES:</b><br/>
    • <b>Compensado</b> = Sábado/Domingo com registro de ponto<br/>
    • <b>Falta</b> = Dia útil sem registros<br/>
    • <b>Jornada Incompleta</b> = Menos de 7:30 horas trabalhadas<br/>
    • <b>Horas Extras</b> = Mais de 7:30 horas trabalhadas<br/>
    • <b>OK</b> = Jornada completa (7:30 horas)<br/>
    • <b>Fuso Horário:</b> Todos os horários em UTC-4 (Manaus)
    """
    elements.append(Paragraph(legenda_texto, estilo_dados))
    elements.append(Spacer(1, 10 * mm))

    # Buscar registros do período
    registros = RegistroPonto.objects.filter(
        funcionario=funcionario,
        timestamp__date__gte=data_inicio,
        timestamp__date__lte=data_fim
    ).order_by('timestamp')

    # 🆕 CONVERTER TODOS OS REGISTROS PARA UTC-4
    registros_convertidos = []
    for registro in registros:
        registro.timestamp = converter_para_manaus(registro.timestamp)
        registros_convertidos.append(registro)

    # Agrupar registros por dia (já convertidos)
    registros_por_dia = {}
    for registro in registros_convertidos:
        data = registro.timestamp.date()
        if data not in registros_por_dia:
            registros_por_dia[data] = []
        registros_por_dia[data].append(registro)

    # Se não houver registros
    if not registros_por_dia:
        elements.append(Paragraph("<b>Nenhum registro de ponto encontrado no período.</b>", estilo_dados))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    # Tabela de registros
    dados_tabela = []

    # CABEÇALHO DA TABELA
    cabecalho = ['Data', 'Dia', 'Entrada 1', 'Saída 1', 'Entrada 2', 'Saída 2',
                 'Entrada 3', 'Saída 3', 'Entrada 4', 'Saída 4', 'Total Horas',
                 'Horas Extras', 'Observações']
    dados_tabela.append(cabecalho)

    # Preencher dados
    for data, registros_dia in sorted(registros_por_dia.items()):
        # DIA DA SEMANA
        dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        dia_semana = dias_semana[data.weekday()]

        linha = [
            data.strftime('%d/%m/%Y'),
            dia_semana
        ]

        # Inicializar horários
        horarios = ['-', '-', '-', '-', '-', '-', '-', '-']

        # Preencher horários na ordem correta (entrada/saída) - JÁ CONVERTIDOS
        entrada_count = 0
        saida_count = 0

        for registro in registros_dia:
            hora_manaus = registro.timestamp.strftime('%H:%M')
            if registro.tipo == 'E' and entrada_count < 4:
                horarios[entrada_count * 2] = hora_manaus
                entrada_count += 1
            elif registro.tipo == 'S' and saida_count < 4:
                horarios[saida_count * 2 + 1] = hora_manaus
                saida_count += 1

        linha.extend(horarios)

        # Calcular totais COM HORÁRIOS CONVERTIDOS
        total_horas = calcular_total_horas(registros_dia)
        horas_extras = calcular_horas_extras(total_horas)

        linha.append(total_horas)
        linha.append(horas_extras)

        # COLUNA OBSERVAÇÕES
        observacao = gerar_observacao(data, registros_dia, total_horas)
        linha.append(observacao)

        dados_tabela.append(linha)

    # Criar tabela
    tabela = Table(dados_tabela, repeatRows=1)
    estilo_tabela = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
    ])
    tabela.setStyle(estilo_tabela)

    elements.append(tabela)

    # LEGENDA DAS OBSERVAÇÕES
    elements.append(Spacer(1, 8 * mm))
    legenda_texto = """
    <b>LEGENDA DAS OBSERVAÇÕES:</b><br/>
    • <b>Compensado</b> = Sábado/Domingo com registro de ponto<br/>
    • <b>Falta</b> = Dia útil sem registros<br/>
    • <b>Jornada Incompleta</b> = Menos de 8 horas trabalhadas<br/>
    • <b>Horas Extras</b> = Mais de 8 horas trabalhadas<br/>
    • <b>OK</b> = Jornada completa (8 horas)<br/>
    • <b>Fuso Horário:</b> Todos os horários em UTC-4 (Manaus)
    """
    elements.append(Paragraph(legenda_texto, estilo_dados))

    # Rodapé com totais - ATUALIZADO
    elements.append(Spacer(1, 8 * mm))
    total_registros = len(registros_convertidos)
    total_dias = len(registros_por_dia)

    rodape_texto = f"""
       <b>RESUMO DO PERÍODO:</b><br/>
       • Total de registros: {total_registros}<br/>
       • Total de dias com registro: {total_dias}<br/>
       • Jornada padrão: 7:30 horas diárias<br/>
       • Fuso horário aplicado: UTC-4 (Manaus)
       """
    elements.append(Paragraph(rodape_texto, estilo_dados))

    # Gerar PDF
    doc.build(elements)

    buffer.seek(0)
    return buffer


def calcular_total_horas(registros_dia):
    """
    Calcula o total de horas trabalhadas no dia COM HORÁRIOS CONVERTIDOS
    """
    if len(registros_dia) < 2:
        return "0:00"

    # Ordenar por timestamp (já convertido para Manaus)
    registros_ordenados = sorted(registros_dia, key=lambda x: x.timestamp)

    total_segundos = 0
    i = 0

    while i < len(registros_ordenados) - 1:
        # Procura por um par entrada-saída
        if registros_ordenados[i].tipo == 'E' and registros_ordenados[i + 1].tipo == 'S':
            entrada = registros_ordenados[i].timestamp
            saida = registros_ordenados[i + 1].timestamp

            # Calcular diferença em segundos (já em UTC-4)
            diferenca = saida - entrada
            total_segundos += diferenca.total_seconds()

            i += 2  # Pular para o próximo par
        else:
            i += 1  # Avançar se não for um par válido

    horas = int(total_segundos // 3600)
    minutos = int((total_segundos % 3600) // 60)

    return f"{horas}:{minutos:02d}"


def calcular_horas_extras(total_horas):
    """
    Calcula horas extras (considerando jornada de 7 horas e 30 minutos)
    """
    try:
        if total_horas == "0:00":
            return "0:00"

        horas, minutos = map(int, total_horas.split(':'))
        total_minutos = horas * 60 + minutos

        jornada_normal = 7 * 60 + 30  # 🆕 7 horas e 30 minutos = 450 minutos

        if total_minutos > jornada_normal:
            extras_minutos = total_minutos - jornada_normal
            extras_horas = extras_minutos // 60
            extras_minutos = extras_minutos % 60
            return f"+{extras_horas}:{extras_minutos:02d}"
        else:
            deficit_minutos = jornada_normal - total_minutos
            deficit_horas = deficit_minutos // 60
            deficit_minutos = deficit_minutos % 60
            return f"-{deficit_horas}:{deficit_minutos:02d}" if deficit_minutos > 0 else "0:00"
    except:
        return "0:00"


def gerar_observacao(data, registros_dia, total_horas):
    """
    Gera observações automáticas baseadas no dia e registros
    """
    # Verificar se é final de semana
    if data.weekday() >= 5:  # 5 = Sábado, 6 = Domingo
        return "Compensado"

    # Verificar se há falta
    if len(registros_dia) == 0:
        return "Falta"

    # Verificar jornada incompleta
    try:
        if total_horas != "0:00":
            horas, minutos = map(int, total_horas.split(':'))
            total_minutos = horas * 60 + minutos

            # 🆕 AGORA COMPARA COM 450 MINUTOS (7h30)
            if total_minutos < 450:  # 7h30 = 450 minutos
                return "Jornada Incompleta"
            elif total_minutos > 450:
                return "Horas Extras"
            else:
                return "OK"
    except:
        pass

    return "OK"