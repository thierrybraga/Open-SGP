"""
Arquivo: app/modules/fiscal/service.py

Responsabilidade:
Regras de negócio para emissão fiscal, sem simular assinatura ou autorização.
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from ...core.config import settings
from ...shared.money import money
from .models import Invoice, ServicePlanDetail, TVTelephonyGateway
from .schemas import (
    BatchInvoiceCreate,
    BatchInvoiceResult,
    DebitNoteCreate,
    DebitNoteOut,
    ICMS115Out,
    ICMS115Request,
    InvoiceCancel,
    InvoiceCreate,
    InvoiceIssue,
    ReportNF2122Out,
    ReportNF2122Request,
    ServicePlanDetailCreate,
    ServicePlanDetailUpdate,
    TVTelephonyGatewayCreate,
    TVTelephonyGatewayUpdate,
)
from .sefaz_client import SefazClient, SefazEnvironment
from .xml_generator import NFeXMLGenerator


FISCAL_STORAGE_DIR = Path("storage/fiscal")


def create_invoice(db: Session, data: InvoiceCreate) -> Invoice:
    inv = Invoice(**data.dict())
    inv.total_amount = float(money(inv.total_amount))
    if inv.status not in ("draft", "ready_to_send", "signed", "emitted", "canceled", "rejected"):
        raise ValueError("Invalid invoice status")
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


create_invoice_record = create_invoice


def issue_invoice(db: Session, invoice: Invoice, data: InvoiceIssue) -> Invoice:
    """
    Prepara XML fiscal para assinatura. A nota só vira `emitted` após retorno
    autorizado da SEFAZ em `send_to_sefaz`.
    """
    if invoice.status == "canceled":
        raise ValueError("Canceled invoice cannot be issued")
    xml = _build_invoice_xml(invoice)
    xml_path = _write_fiscal_file("unsigned", invoice, xml)
    invoice.xml_path = str(xml_path)
    invoice.issue_date = invoice.issue_date or date.today()
    invoice.status = "ready_to_send"
    return invoice


emit_invoice = issue_invoice


def cancel_invoice(db: Session, invoice: Invoice, data: InvoiceCancel) -> Invoice:
    if len(data.reason.strip()) < 15:
        raise ValueError("Cancel reason must have at least 15 characters")
    if invoice.status not in ("emitted", "rejected", "ready_to_send", "signed"):
        raise ValueError("Invoice status does not allow cancellation")
    invoice.status = "canceled"
    invoice.cancel_date = date.today()
    invoice.debit_reason = data.reason
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def sign_invoice_a1(invoice: Invoice) -> Invoice:
    if not invoice.xml_path:
        raise ValueError("Invoice XML must be generated before signing")
    if not settings.a1_cert_pfx_path or not settings.a1_cert_password:
        raise ValueError("A1_CERT_PFX_PATH and A1_CERT_PASSWORD are required for fiscal homologation")

    try:
        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, pkcs12
        from signxml import XMLSigner, methods
        from lxml import etree
    except ImportError as exc:
        raise RuntimeError("Fiscal signing requires cryptography, lxml and signxml installed") from exc

    pfx_path = Path(settings.a1_cert_pfx_path)
    if not pfx_path.exists():
        raise ValueError(f"A1 certificate file not found: {pfx_path}")

    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        pfx_path.read_bytes(),
        settings.a1_cert_password.encode("utf-8"),
    )
    if not private_key or not certificate:
        raise ValueError("A1 certificate did not contain private key and certificate")

    xml_path = Path(invoice.xml_path)
    root = etree.fromstring(xml_path.read_bytes())
    signed = XMLSigner(method=methods.enveloped, digest_algorithm="sha256").sign(
        root,
        key=private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()),
        cert=certificate.public_bytes(Encoding.PEM),
    )
    signed_xml = etree.tostring(signed, encoding="utf-8", xml_declaration=True, pretty_print=True).decode("utf-8")
    signed_path = _write_fiscal_file("signed", invoice, signed_xml)
    invoice.xml_path = str(signed_path)
    invoice.status = "signed"
    return invoice


def send_to_sefaz(invoice: Invoice, force: bool = False) -> Invoice:
    if invoice.status != "signed" and not force:
        raise ValueError("Invoice must be signed before sending to SEFAZ")
    if not invoice.xml_path:
        raise ValueError("Invoice XML not found")
    if not settings.a1_cert_pfx_path or not settings.a1_cert_password:
        raise ValueError("A1_CERT_PFX_PATH and A1_CERT_PASSWORD are required for SEFAZ transmission")

    environment = (
        SefazEnvironment.PRODUCAO if settings.sefaz_environment == "producao" else SefazEnvironment.HOMOLOGACAO
    )
    client = SefazClient(
        certificate_path=settings.a1_cert_pfx_path,
        certificate_password=settings.a1_cert_password,
        environment=environment,
        uf=settings.sefaz_uf,
    )
    result = client.enviar_nfe(Path(invoice.xml_path).read_text(encoding="utf-8"), lote=invoice.id)
    status_code = str(result.get("status_code") or "")
    if status_code in ("100", "104"):
        invoice.status = "emitted"
        invoice.pdf_url = invoice.pdf_url or f"/api/fiscal/invoices/{invoice.id}/danfe"
    else:
        invoice.status = "rejected"
        invoice.debit_reason = result.get("status_message")
    return invoice


def create_invoices_batch(db: Session, data: BatchInvoiceCreate) -> BatchInvoiceResult:
    details = []
    success = 0
    for contract_id in data.contract_ids:
        try:
            inv = Invoice(
                contract_id=contract_id,
                number=f"{contract_id}-{data.issue_date:%Y%m}",
                series="1",
                status="draft",
                issue_date=data.issue_date,
                total_amount=0,
                service_description="Serviço de telecomunicações",
                municipality_code="0000000",
                taxation_code="0000",
            )
            db.add(inv)
            success += 1
            details.append(f"Invoice draft created for contract {contract_id}")
        except Exception as exc:
            details.append(f"Contract {contract_id}: {exc}")
    db.commit()
    return BatchInvoiceResult(total=len(data.contract_ids), success=success, errors=len(data.contract_ids) - success, details=details)


def generate_icms115(db: Session, data: ICMS115Request) -> ICMS115Out:
    invoices = (
        db.query(Invoice)
        .filter(Invoice.invoice_type.in_(("telecom_21", "telecom_22")))
        .filter(Invoice.status == "emitted")
        .all()
    )
    lines = ["# ICMS 115 - arquivo fiscal operacional", f"REFERENCIA;{data.year:04d}-{data.month:02d}"]
    for inv in invoices:
        if inv.issue_date and inv.issue_date.year == data.year and inv.issue_date.month == data.month:
            lines.append(f"{inv.number};{inv.series};{inv.contract_id};{money(inv.total_amount)}")
    content = "\r\n".join(lines) + "\r\n"
    path = FISCAL_STORAGE_DIR / "reports" / f"icms115_{data.year}_{data.month:02d}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    import hashlib

    return ICMS115Out(file_path=str(path), hash_md5=hashlib.md5(content.encode("utf-8")).hexdigest())


def create_debit_note(db: Session, data: DebitNoteCreate) -> DebitNoteOut:
    inv = Invoice(
        contract_id=data.contract_id,
        number=f"DN-{data.contract_id}-{datetime.utcnow():%Y%m%d%H%M%S}",
        series="DN",
        status="draft",
        issue_date=date.today(),
        total_amount=float(money(data.amount)),
        service_description=data.description,
        municipality_code="0000000",
        taxation_code="0000",
        invoice_type="debit_note",
        debit_reason=data.description,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return DebitNoteOut(id=inv.id, contract_id=inv.contract_id, amount=inv.total_amount, description=inv.service_description, created_at=inv.created_at)


def create_service_plan_detail(db: Session, data: ServicePlanDetailCreate) -> ServicePlanDetail:
    obj = ServicePlanDetail(**data.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_service_plan_detail(db: Session, obj: ServicePlanDetail, data: ServicePlanDetailUpdate) -> ServicePlanDetail:
    for key, value in data.dict(exclude_unset=True).items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def get_plan_fiscal_config(db: Session, plan_id: int) -> Optional[ServicePlanDetail]:
    return db.query(ServicePlanDetail).filter(ServicePlanDetail.plan_id == plan_id).first()


def create_tv_telephony_gateway(db: Session, data: TVTelephonyGatewayCreate) -> TVTelephonyGateway:
    obj = TVTelephonyGateway(name=data.name, provider="generic", gateway_type="tv", api_url=data.url, api_key=data.username, api_secret=data.password)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_tv_telephony_gateway(db: Session, obj: TVTelephonyGateway, data: TVTelephonyGatewayUpdate) -> TVTelephonyGateway:
    values = data.dict(exclude_unset=True)
    if "url" in values:
        obj.api_url = values.pop("url")
    if "username" in values:
        obj.api_key = values.pop("username")
    if "password" in values:
        obj.api_secret = values.pop("password")
    for key, value in values.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def test_tv_telephony_gateway(db: Session, gateway_id: int) -> dict:
    gateway = db.query(TVTelephonyGateway).filter(TVTelephonyGateway.id == gateway_id).first()
    if not gateway:
        raise ValueError("Gateway not found")
    if not gateway.api_url.startswith(("https://", "http://")):
        raise ValueError("Gateway URL must be HTTP(S)")
    gateway.last_test_at = datetime.utcnow().isoformat()
    gateway.last_test_success = True
    gateway.last_test_message = "Configuration format validated; external provider homologation must be executed with provider credentials."
    db.add(gateway)
    db.commit()
    return {"success": True, "message": gateway.last_test_message}


def generate_report_nf_2122(db: Session, data: ReportNF2122Request) -> ReportNF2122Out:
    path = FISCAL_STORAGE_DIR / "reports" / f"nf2122_{data.year}_{data.month:02d}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"NF21/22;{data.year:04d}-{data.month:02d}\r\n", encoding="utf-8")
    return ReportNF2122Out(report_url=str(path))


def _build_invoice_xml(invoice: Invoice) -> str:
    contract = invoice.contract
    if not contract or not contract.client:
        raise ValueError("Invoice contract/client data is required")
    client = contract.client
    primary_address = next((addr for addr in client.addresses if addr.is_primary), None) or (client.addresses[0] if client.addresses else None)
    if not primary_address:
        raise ValueError("Client primary address is required for fiscal XML")

    emitente = {
        "cnpj": "00000000000000",
        "razao_social": "EMITENTE NAO CONFIGURADO",
        "endereco": "NAO CONFIGURADO",
        "bairro": "NAO CONFIGURADO",
        "cidade": "NAO CONFIGURADO",
        "uf": primary_address.state,
        "cep": "00000000",
        "inscricao_estadual": "ISENTO",
    }
    destinatario = {
        "nome": client.name,
        "cpf": client.document if len("".join(filter(str.isdigit, client.document or ""))) == 11 else None,
        "cnpj": client.document if len("".join(filter(str.isdigit, client.document or ""))) != 11 else None,
        "endereco": primary_address.street,
        "numero": primary_address.number,
        "bairro": primary_address.neighborhood,
        "cidade": primary_address.city,
        "uf": primary_address.state,
        "cep": primary_address.zipcode,
    }
    total = money(invoice.total_amount)
    produto = {
        "codigo": invoice.taxation_code or "0000",
        "descricao": invoice.service_description,
        "quantidade": Decimal("1"),
        "valor_unitario": total,
        "valor_total": total,
        "ncm": "00000000",
        "cfop": "5102",
        "unidade": "UN",
    }
    totais = {
        "valor_produtos": total,
        "valor_total": total,
        "base_calculo": total,
        "valor_icms": Decimal("0.00"),
        "valor_pis": Decimal("0.00"),
        "valor_cofins": Decimal("0.00"),
    }
    return NFeXMLGenerator().gerar_nfe(
        emitente=emitente,
        destinatario=destinatario,
        produtos=[produto],
        totais=totais,
        numero_nota=int("".join(filter(str.isdigit, invoice.number)) or invoice.id),
        serie=int("".join(filter(str.isdigit, invoice.series)) or 1),
        data_emissao=datetime.combine(invoice.issue_date or date.today(), datetime.min.time()),
        ambiente=1 if settings.sefaz_environment == "producao" else 2,
    )


def _write_fiscal_file(stage: str, invoice: Invoice, content: str) -> Path:
    path = FISCAL_STORAGE_DIR / stage / f"invoice_{invoice.id}_{invoice.number}.xml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
