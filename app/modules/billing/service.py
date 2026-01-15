"""
Arquivo: app/modules/billing/service.py

Responsabilidade:
Regras de negócio para financeiro: criar títulos, gerar boleto, registrar
pagamentos, gerar remessas CNAB e processar retornos, criar promessas.

Integrações:
- modules.billing.models
- modules.contracts.models
"""

from datetime import datetime, date
from sqlalchemy.orm import Session

from .models import Title, Payment, Remittance, RemittanceItem, ReturnFile, ReturnItem, PaymentPromise, TitleAdjustment
from .schemas import TitleCreate, TitleUpdate, RemittanceCreate, ReturnCreate, PaymentPromiseCreate, CarneCreate, CarneOut, AdjustmentCreate, BatchTitleCreate, BatchTitleOut, BatchCarneCreate, BatchCarneOut, BatchBoletoGenerate, BatchBoletoOut
from ..administration.finance.models import FinancialParameter, Carrier
from ..contracts.models import Contract
from ..plans.models import Plan
from ...shared.boleto import BoletoGenerator, BoletoData
from ...shared.cnab import CNAB240Generator, CNAB400Generator


def create_title(db: Session, data: TitleCreate) -> Title:
    contract = db.query(Contract).filter(Contract.id == data.contract_id).first()
    if not contract:
        raise ValueError("Contract not found")
    title = Title(**data.dict())
    db.add(title)
    db.commit()
    db.refresh(title)
    return title


def update_title(db: Session, title: Title, data: TitleUpdate) -> Title:
    for field, value in data.dict(exclude_none=True).items():
        setattr(title, field, value)
    db.add(title)
    db.commit()
    db.refresh(title)
    return title


def generate_boleto(db: Session, title: Title) -> Title:
    """
    Gera boleto com código de barras e linha digitável reais,
    seguindo padrão Febraban.
    """
    # Busca dados do contrato e empresa
    contract = db.query(Contract).filter(Contract.id == title.contract_id).first()
    if not contract:
        raise ValueError("Contract not found")

    # Busca parâmetros financeiros para dados da empresa
    fp = db.query(FinancialParameter).filter(FinancialParameter.company_id.isnot(None)).first()
    carrier = None
    if fp and fp.default_carrier_id:
        carrier = db.query(Carrier).filter(Carrier.id == fp.default_carrier_id).first()

    # Define dados bancários (usa carrier ou padrões)
    banco_codigo = carrier.bank_code if carrier else title.bank_code or "341"
    agencia = carrier.agency if carrier else "0001"
    conta = carrier.account if carrier else "00000001"
    conta_dv = "0"
    carteira = carrier.wallet if carrier else "09"

    # Gera campo livre genérico (em produção, usar layout específico do banco)
    campo_livre = BoletoGenerator.gerar_campo_livre_generico(
        agencia=agencia,
        conta=conta,
        carteira=carteira,
        nosso_numero=title.our_number or str(title.id).zfill(11)
    )

    # Gera código de barras com padrão Febraban
    codigo_barras = BoletoGenerator.gerar_codigo_barras(
        banco=banco_codigo,
        moeda="9",  # Real
        vencimento=title.due_date,
        valor=float(title.amount),
        campo_livre=campo_livre
    )

    # Gera linha digitável
    linha_digitavel = BoletoGenerator.gerar_linha_digitavel(codigo_barras)

    # Atualiza título com dados do boleto
    title.bar_code = codigo_barras
    title.digitable_line = linha_digitavel  # Certifique-se que este campo existe no modelo

    # URL do boleto (pode integrar com serviço de geração de PDF)
    title.payment_slip_url = f"https://boleto.example.com/view/{title.id}/{codigo_barras}"

    db.add(title)
    db.commit()
    db.refresh(title)
    return title


def register_payment(db: Session, title: Title, amount: float, method: str) -> Title:
    payment = Payment(title_id=title.id, payment_date=datetime.utcnow().date(), amount=amount, method=method)
    db.add(payment)
    title.status = "paid"
    title.paid_date = datetime.utcnow().date()
    db.add(title)
    db.commit()
    db.refresh(title)
    return title


def create_remittance(db: Session, data: RemittanceCreate) -> Remittance:
    q = db.query(Title).filter(Title.status == "open")
    if data.due_from:
        q = q.filter(Title.due_date >= data.due_from)
    if data.due_to:
        q = q.filter(Title.due_date <= data.due_to)
    titles = q.all()
    rem = Remittance(file_name=data.file_name, total_titles=len(titles))
    db.add(rem)
    db.commit()
    db.refresh(rem)
    for t in titles:
        db.add(RemittanceItem(remittance_id=rem.id, title_id=t.id, value=t.amount))
    db.commit()
    return rem


def process_return(db: Session, data: ReturnCreate) -> ReturnFile:
    rf = ReturnFile(file_name=data.file_name, processed_at=datetime.utcnow(), total_items=len(data.items))
    db.add(rf)
    db.commit()
    db.refresh(rf)
    for item in data.items:
        title_id = item.get("title_id")
        status = item.get("status")
        value = float(item.get("value", 0))
        occurred_date = item.get("occurred_at")
        db.add(ReturnItem(return_file_id=rf.id, title_id=title_id, status=status, value=value, occurred_at=occurred_date))
        if title_id:
            t = db.query(Title).filter(Title.id == title_id).first()
            if t:
                if status == "paid" and abs(value - t.amount) < 0.01:
                    t.status = "paid"
                    t.paid_date = datetime.utcnow().date()
                    db.add(Payment(title_id=t.id, payment_date=datetime.utcnow().date(), amount=value, method="boleto"))
                elif status in ("paid", "partial") and value > 0 and value < t.amount:
                    t.status = "partial"
                    db.add(Payment(title_id=t.id, payment_date=datetime.utcnow().date(), amount=value, method="boleto"))
                    db.add(t)
                elif status == "canceled":
                    t.status = "canceled"
                    db.add(t)
    db.commit()
    return rf


def _calc_cnab_values(db: Session, title: Title) -> dict:
    fp = (
        db.query(FinancialParameter)
        .join(Carrier, FinancialParameter.default_carrier_id == Carrier.id, isouter=True)
        .filter(FinancialParameter.company_id.isnot(None))
        .first()
    )
    fine = (fp.fine_percent if fp else title.fine_percent) / 100.0
    interest = (fp.interest_percent if fp else title.interest_percent) / 100.0
    return {
        "amount_cents": int(round(title.amount * 100)),
        "fine_cents": int(round(title.amount * fine * 100)),
        "daily_interest_cents": int(round(title.amount * interest / 30.0 * 100)),
    }


def generate_cnab_layout(bank_code: str, layout: str, titles: list[Title], values: list[dict], *, carrier: Carrier | None = None) -> str:
    """
    Gera arquivo CNAB 240 ou 400 real seguindo padrão Febraban.

    Args:
        bank_code: Código do banco (3 dígitos)
        layout: "240" ou "400"
        titles: Lista de títulos para incluir na remessa
        values: Lista de valores calculados (juros, multa, etc)
        carrier: Portador com dados bancários

    Returns:
        Conteúdo do arquivo CNAB completo
    """
    layout = (layout or "400").strip()

    # Dados da empresa (obtém do carrier ou usa padrão)
    empresa_dados = {
        "tipo_inscricao": "2",  # 2=CNPJ
        "numero_inscricao": carrier.company_document if carrier else "00000000000000",
        "nome": carrier.company_name if carrier else "EMPRESA LTDA",
        "agencia": carrier.agency if carrier else "0001",
        "conta": carrier.account if carrier else "00000001",
        "conta_dv": carrier.account_dv if carrier else "0"
    }

    if layout == "240":
        # Prepara títulos no formato esperado pelo gerador CNAB 240
        titulos_cnab = []
        for idx, title in enumerate(titles):
            # Busca dados do sacado (cliente) do contrato
            contract = title.contract
            sacado_dados = {
                "tipo_inscricao": "1" if len(contract.client.cpf_cnpj or "") == 11 else "2",
                "numero_inscricao": (contract.client.cpf_cnpj or "").replace(".", "").replace("-", "").replace("/", ""),
                "nome": contract.client.name or "CLIENTE",
                "endereco": contract.client.address or "",
                "bairro": contract.client.neighborhood or "",
                "cep": (contract.client.zip_code or "").replace("-", ""),
                "cidade": contract.client.city or "",
                "uf": contract.client.state or "SP"
            }

            titulo_dict = {
                "nosso_numero": title.our_number or str(title.id).zfill(11),
                "carteira": carrier.wallet if carrier else "09",
                "documento_numero": title.document_number or str(title.id),
                "vencimento": title.due_date,
                "valor": float(title.amount),
                "especie": "02",  # 02=Duplicata Mercantil
                "aceite": "N",
                "data_emissao": title.issue_date or date.today(),
                "codigo_juros": "1" if values[idx].get("daily_interest_cents", 0) > 0 else "0",
                "valor_juros": values[idx].get("daily_interest_cents", 0) / 100.0,
                "codigo_desconto": "0",
                "valor_desconto": 0.0,
                "valor_iof": 0.0,
                "valor_abatimento": 0.0,
                "codigo_protesto": "0",
                "prazo_protesto": 0,
                "codigo_baixa": "0",
                "prazo_baixa": 0,
                "sacado": sacado_dados
            }
            titulos_cnab.append(titulo_dict)

        # Gera CNAB 240 completo
        return CNAB240Generator.gerar_remessa_completa(
            banco_codigo=bank_code,
            empresa_dados=empresa_dados,
            titulos=titulos_cnab,
            sequencial_arquivo=1
        )
    else:
        # CNAB 400
        titulos_cnab = []
        for title in titles:
            contract = title.contract
            titulo_dict = {
                "nosso_numero": title.our_number or str(title.id).zfill(11),
                "documento_numero": title.document_number or str(title.id),
                "vencimento": title.due_date,
                "valor": float(title.amount)
            }
            titulos_cnab.append(titulo_dict)

        # Gera CNAB 400
        return CNAB400Generator.gerar_remessa_simples(
            banco_codigo=bank_code,
            empresa_dados=empresa_dados,
            titulos=titulos_cnab
        )


def generate_remittance_file(db: Session, bank_code: str, due_from: date | None, due_to: date | None, layout: str | None = None) -> str:
    q = db.query(Title).filter(Title.status == "open", Title.bank_code == bank_code)
    if due_from:
        q = q.filter(Title.due_date >= due_from)
    if due_to:
        q = q.filter(Title.due_date <= due_to)
    titles = q.order_by(Title.due_date.asc()).all()
    values = [_calc_cnab_values(db, t) for t in titles]
    return generate_cnab_layout(bank_code, layout or "400", titles, values)


def generate_remittance_file_for_default_carrier(db: Session, due_from: date | None, due_to: date | None) -> str:
    fp = db.query(FinancialParameter).filter(FinancialParameter.company_id.isnot(None)).first()
    carrier: Carrier | None = None
    if fp and fp.default_carrier_id:
        carrier = db.query(Carrier).filter(Carrier.id == fp.default_carrier_id).first()
    bank_code = (carrier.bank_code if carrier else "341")
    layout = (carrier.cnab_layout if carrier else "400")
    q = db.query(Title).filter(Title.status == "open", Title.bank_code == bank_code)
    if due_from:
        q = q.filter(Title.due_date >= due_from)
    if due_to:
        q = q.filter(Title.due_date <= due_to)
    titles = q.order_by(Title.due_date.asc()).all()
    values = [_calc_cnab_values(db, t) for t in titles]
    return generate_cnab_layout(bank_code, layout, titles, values, carrier=carrier)


def create_promise(db: Session, data: PaymentPromiseCreate) -> PaymentPromise:
    promise = PaymentPromise(**data.dict())
    db.add(promise)
    db.commit()
    db.refresh(promise)
    return promise


def generate_carne(db: Session, data: CarneCreate) -> CarneOut:
    contract = db.query(Contract).filter(Contract.id == data.contract_id).first()
    if not contract:
        raise ValueError("Contract not found")

    titles_created = 0
    first_due: date | None = None
    last_due: date | None = None

    year = data.start_year
    month = data.start_month

    for i in range(data.months):
        due_year = year + ((month - 1) // 12)
        due_month = ((month - 1) % 12) + 1
        issue_dt = date.today()
        due_dt = date(due_year, due_month, contract.billing_day)
        if first_due is None:
            first_due = due_dt
        last_due = due_dt

        amount = data.amount if data.amount is not None else (contract.price_override or 0.0)
        if amount == 0.0 and contract.plan:
            # Fallback: if no override, attempt use plan price via attribute if exists
            try:
                amount = float(getattr(contract.plan, "price"))
            except Exception:
                amount = 0.0

        doc = f"DOC-{contract.id}-{due_year:04d}{due_month:02d}-{i+1:02d}"
        our = f"NOSSO-{contract.id}-{due_year:04d}{due_month:02d}-{i+1:02d}"

        t = Title(
            contract_id=contract.id,
            issue_date=issue_dt,
            due_date=due_dt,
            amount=amount,
            status="open",
            fine_percent=2.0,
            interest_percent=1.0,
            bank_code="341",
            document_number=doc,
            our_number=our,
        )
        db.add(t)
        titles_created += 1
        month += 1

    db.commit()
    return CarneOut(
        contract_id=contract.id,
        titles_created=titles_created,
        first_due_date=first_due or date.today(),
        last_due_date=last_due or date.today(),
    )


def create_adjustment(db: Session, title_id: int, data: AdjustmentCreate) -> TitleAdjustment:
    t = db.query(Title).filter(Title.id == title_id).first()
    if not t:
        raise ValueError("Title not found")
    if data.type not in ("increase", "discount"):
        raise ValueError("Invalid adjustment type")
    adj = TitleAdjustment(title_id=title_id, type=data.type, amount=float(data.amount), reason=data.reason)
    db.add(adj)
    db.commit()
    db.refresh(adj)
    return adj


def calculate_title_effective_amount(db: Session, title_id: int) -> float:
    t = db.query(Title).filter(Title.id == title_id).first()
    if not t:
        raise ValueError("Title not found")
    base = float(t.amount)
    inc = sum(float(a.amount) for a in db.query(TitleAdjustment).filter(TitleAdjustment.title_id == title_id, TitleAdjustment.type == "increase").all())
    disc = sum(float(a.amount) for a in db.query(TitleAdjustment).filter(TitleAdjustment.title_id == title_id, TitleAdjustment.type == "discount").all())
    return max(0.0, base + inc - disc)


def create_titles_batch(db: Session, data: BatchTitleCreate) -> BatchTitleOut:
    """
    Cria títulos em lote para múltiplos contratos.
    Se amount não for especificado, usa o valor do plano do contrato.
    """
    titles_created = 0
    successful_contracts = []
    errors = []

    for contract_id in data.contract_ids:
        try:
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                errors.append({"contract_id": contract_id, "error": "Contract not found"})
                continue

            # Determinar o valor do título
            title_amount = data.amount
            if title_amount is None:
                # Buscar o valor do plano
                plan = db.query(Plan).filter(Plan.id == contract.plan_id).first()
                if not plan:
                    errors.append({"contract_id": contract_id, "error": "Plan not found"})
                    continue
                title_amount = float(plan.price)

            # Gerar números de documento e nosso número
            doc_number = f"{contract_id}{data.issue_date.strftime('%Y%m%d')}"
            our_number = f"{contract_id:08d}{data.issue_date.strftime('%m%y')}"

            # Criar o título
            title = Title(
                contract_id=contract_id,
                issue_date=data.issue_date,
                due_date=data.due_date,
                amount=title_amount,
                status=data.status,
                fine_percent=data.fine_percent,
                interest_percent=data.interest_percent,
                bank_code=data.bank_code,
                document_number=doc_number,
                our_number=our_number,
            )
            db.add(title)
            titles_created += 1
            successful_contracts.append(contract_id)

        except Exception as e:
            errors.append({"contract_id": contract_id, "error": str(e)})

    db.commit()

    return BatchTitleOut(
        titles_created=titles_created,
        contract_ids=successful_contracts,
        errors=errors
    )


def generate_carnes_batch(db: Session, data: BatchCarneCreate) -> BatchCarneOut:
    """
    Gera carnês em lote para múltiplos contratos.
    """
    carnes_created = 0
    total_titles = 0
    successful_contracts = []
    errors = []

    for contract_id in data.contract_ids:
        try:
            carne_data = CarneCreate(
                contract_id=contract_id,
                start_month=data.start_month,
                start_year=data.start_year,
                months=data.months,
                amount=data.amount
            )

            result = generate_carne(db, carne_data)
            carnes_created += 1
            total_titles += result.titles_created
            successful_contracts.append(contract_id)

        except Exception as e:
            errors.append({"contract_id": contract_id, "error": str(e)})

    return BatchCarneOut(
        carnes_created=carnes_created,
        total_titles_created=total_titles,
        contract_ids=successful_contracts,
        errors=errors
    )


def generate_boletos_batch(db: Session, data: BatchBoletoGenerate) -> BatchBoletoOut:
    """
    Gera boletos em lote para múltiplos títulos.
    """
    boletos_generated = 0
    successful_titles = []
    errors = []

    for title_id in data.title_ids:
        try:
            title = db.query(Title).filter(Title.id == title_id).first()
            if not title:
                errors.append({"title_id": title_id, "error": "Title not found"})
                continue

            generate_boleto(db, title)
            boletos_generated += 1
            successful_titles.append(title_id)

        except Exception as e:
            errors.append({"title_id": title_id, "error": str(e)})

    return BatchBoletoOut(
        boletos_generated=boletos_generated,
        title_ids=successful_titles,
        errors=errors
    )
