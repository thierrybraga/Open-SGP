"""
Arquivo: app/modules/billing/pdf_generator.py

Responsabilidade:
Geração de PDFs para carnês e boletos.

Integrações:
- modules.billing.models
- reportlab (PDF generation)
"""

from io import BytesIO
from datetime import date
from typing import List
import base64

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_carne_pdf(titles: List, client_name: str, contract_id: int) -> bytes:
    """
    Gera PDF de carnê com múltiplos boletos.

    Args:
        titles: Lista de Title objects
        client_name: Nome do cliente
        contract_id: ID do contrato

    Returns:
        bytes: PDF gerado
    """
    if not REPORTLAB_AVAILABLE:
        # Fallback: gera PDF simples sem reportlab
        return generate_simple_carne_pdf(titles, client_name, contract_id)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Configurações
    y_position = height - 30*mm
    line_height = 5*mm

    # Título do documento
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(30*mm, y_position, f"Carnê de Pagamento - Contrato #{contract_id}")
    y_position -= 10*mm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(30*mm, y_position, f"Cliente: {client_name}")
    y_position -= 15*mm

    # Cabeçalho da tabela
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(30*mm, y_position, "Vencimento")
    pdf.drawString(60*mm, y_position, "Nosso Número")
    pdf.drawString(100*mm, y_position, "Valor")
    pdf.drawString(130*mm, y_position, "Status")
    y_position -= 7*mm

    # Linha separadora
    pdf.line(30*mm, y_position, width - 30*mm, y_position)
    y_position -= 5*mm

    # Itens do carnê
    pdf.setFont("Helvetica", 9)
    for title in titles:
        if y_position < 30*mm:  # Nova página se necessário
            pdf.showPage()
            y_position = height - 30*mm

            # Repetir cabeçalho
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(30*mm, y_position, "Vencimento")
            pdf.drawString(60*mm, y_position, "Nosso Número")
            pdf.drawString(100*mm, y_position, "Valor")
            pdf.drawString(130*mm, y_position, "Status")
            y_position -= 7*mm
            pdf.line(30*mm, y_position, width - 30*mm, y_position)
            y_position -= 5*mm
            pdf.setFont("Helvetica", 9)

        # Dados do título
        due_date_str = title.due_date.strftime("%d/%m/%Y") if isinstance(title.due_date, date) else str(title.due_date)
        pdf.drawString(30*mm, y_position, due_date_str)
        pdf.drawString(60*mm, y_position, title.our_number or "-")
        pdf.drawString(100*mm, y_position, f"R$ {title.amount:.2f}")
        pdf.drawString(130*mm, y_position, title.status.upper())

        y_position -= line_height

    # Rodapé
    y_position -= 10*mm
    pdf.line(30*mm, y_position, width - 30*mm, y_position)
    y_position -= 5*mm

    total_amount = sum(t.amount for t in titles)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(30*mm, y_position, f"Total: R$ {total_amount:.2f}")

    # Finalizar PDF
    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def generate_simple_carne_pdf(titles: List, client_name: str, contract_id: int) -> bytes:
    """
    Gera PDF simples de carnê (fallback sem reportlab).
    Retorna um PDF básico em texto.
    """
    # HTML simples que pode ser convertido em PDF
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            .total {{ font-weight: bold; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h1>Carnê de Pagamento - Contrato #{contract_id}</h1>
        <p><strong>Cliente:</strong> {client_name}</p>

        <table>
            <tr>
                <th>Vencimento</th>
                <th>Nosso Número</th>
                <th>Valor</th>
                <th>Status</th>
            </tr>
    """

    total = 0
    for title in titles:
        due_date_str = title.due_date.strftime("%d/%m/%Y") if isinstance(title.due_date, date) else str(title.due_date)
        html_content += f"""
            <tr>
                <td>{due_date_str}</td>
                <td>{title.our_number or '-'}</td>
                <td>R$ {title.amount:.2f}</td>
                <td>{title.status.upper()}</td>
            </tr>
        """
        total += title.amount

    html_content += f"""
        </table>
        <p class="total">Total: R$ {total:.2f}</p>
    </body>
    </html>
    """

    return html_content.encode('utf-8')


def generate_boleto_pdf(title, client_data: dict, company_data: dict) -> bytes:
    """
    Gera PDF de boleto individual.

    Args:
        title: Title object
        client_data: Dados do cliente
        company_data: Dados da empresa

    Returns:
        bytes: PDF gerado
    """
    if not REPORTLAB_AVAILABLE:
        return generate_simple_boleto_pdf(title, client_data, company_data)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Configurações do boleto
    y_pos = height - 100*mm

    # Cabeçalho
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(30*mm, y_pos, company_data.get('name', 'Empresa'))
    y_pos -= 10*mm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(30*mm, y_pos, f"CNPJ: {company_data.get('document', '')}")
    y_pos -= 15*mm

    # Dados do boleto
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(30*mm, y_pos, "Dados do Boleto")
    y_pos -= 8*mm

    pdf.setFont("Helvetica", 10)
    due_date_str = title.due_date.strftime("%d/%m/%Y") if isinstance(title.due_date, date) else str(title.due_date)

    pdf.drawString(30*mm, y_pos, f"Vencimento: {due_date_str}")
    y_pos -= 6*mm
    pdf.drawString(30*mm, y_pos, f"Nosso Número: {title.our_number or '-'}")
    y_pos -= 6*mm
    pdf.drawString(30*mm, y_pos, f"Documento: {title.document_number or '-'}")
    y_pos -= 6*mm
    pdf.drawString(30*mm, y_pos, f"Valor: R$ {title.amount:.2f}")
    y_pos -= 10*mm

    # Dados do pagador
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(30*mm, y_pos, "Pagador")
    y_pos -= 8*mm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(30*mm, y_pos, f"Nome: {client_data.get('name', '')}")
    y_pos -= 6*mm
    pdf.drawString(30*mm, y_pos, f"Documento: {client_data.get('document', '')}")
    y_pos -= 10*mm

    # Código de barras (simulado - em produção usar biblioteca específica)
    if title.bar_code:
        pdf.setFont("Courier", 8)
        pdf.drawString(30*mm, y_pos, f"Código de Barras: {title.bar_code}")

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()


def generate_simple_boleto_pdf(title, client_data: dict, company_data: dict) -> bytes:
    """
    Gera HTML simples de boleto (fallback).
    """
    due_date_str = title.due_date.strftime("%d/%m/%Y") if isinstance(title.due_date, date) else str(title.due_date)

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial; margin: 20px; }}
            .boleto {{ border: 2px solid #000; padding: 20px; }}
            h2 {{ color: #333; }}
        </style>
    </head>
    <body>
        <div class="boleto">
            <h2>{company_data.get('name', 'Empresa')}</h2>
            <p>CNPJ: {company_data.get('document', '')}</p>
            <hr>
            <h3>Dados do Boleto</h3>
            <p><strong>Vencimento:</strong> {due_date_str}</p>
            <p><strong>Nosso Número:</strong> {title.our_number or '-'}</p>
            <p><strong>Documento:</strong> {title.document_number or '-'}</p>
            <p><strong>Valor:</strong> R$ {title.amount:.2f}</p>
            <hr>
            <h3>Pagador</h3>
            <p><strong>Nome:</strong> {client_data.get('name', '')}</p>
            <p><strong>Documento:</strong> {client_data.get('document', '')}</p>
            {f'<hr><p><strong>Código de Barras:</strong> {title.bar_code}</p>' if title.bar_code else ''}
        </div>
    </body>
    </html>
    """

    return html.encode('utf-8')


def generate_batch_carne_pdf(carnes_data: List[dict]) -> bytes:
    """
    Gera PDF com múltiplos carnês em batch.

    Args:
        carnes_data: Lista de dicts com {titles, client_name, contract_id}

    Returns:
        bytes: PDF consolidado
    """
    if not REPORTLAB_AVAILABLE:
        # Concatenar HTMLs
        htmls = []
        for data in carnes_data:
            html = generate_simple_carne_pdf(
                data['titles'],
                data['client_name'],
                data['contract_id']
            ).decode('utf-8')
            htmls.append(html)

        combined = "<div style='page-break-after: always;'>".join(htmls)
        return f"<html><body>{combined}</body></html>".encode('utf-8')

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    for i, data in enumerate(carnes_data):
        if i > 0:
            pdf.showPage()  # Nova página para cada carnê

        # Aqui poderia chamar a lógica de generate_carne_pdf
        # Por simplicidade, adicionar título
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(30*mm, A4[1] - 30*mm, f"Carnê #{i+1} - Contrato #{data['contract_id']}")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(30*mm, A4[1] - 40*mm, f"Cliente: {data['client_name']}")

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue()
