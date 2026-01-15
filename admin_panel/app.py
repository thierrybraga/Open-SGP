"""
Arquivo: admin_panel/app.py

Responsabilidade:
Inicializa um painel administrativo Flask mínimo com uma página de dashboard.

Integrações:
- templates/index.html
"""

from flask import Flask, render_template, request, redirect, url_for, make_response, session, flash
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import create_engine, func, case
import secrets
import os

from ..app.core.config import settings
from ..app.core.database import import_all_models, SessionLocal, ensure_required_columns, Base, engine
from ..app.modules.communication.models import MessageQueue
from ..app.modules.communication.service import requeue_failed, dispatch_message
from ..app.modules.reports.service import dashboard_overview, timeseries_communication_success, timeseries_service_orders_status
from ..app.modules.service_orders.models import ServiceOrder
from ..app.modules.network.models import ContractNetworkAssignment, ContractTechHistory
from ..app.modules.network.service import (
    unblock_contract, 
    provision_contract, 
    block_contract, 
    sync_billing_blocking,
    get_radius_active_session,
    get_radius_usage_history,
    test_device_connection
)
from ..app.modules.administration.pops.models import POP
from ..app.modules.administration.nas.models import NAS
from ..app.modules.administration.variables.models import SystemVariable
from ..app.modules.administration.backups.models import BackupJob, BackupExecution
from ..app.modules.administration.backups.service import trigger_backup
from ..app.modules.network.models import NetworkDevice, VLAN, IPPool, ServiceProfile
from ..app.modules.administration.finance.models import Company, Carrier, ReceiptPoint, FinancialParameter
from ..app.modules.billing.service import (
    generate_remittance_file,
    generate_remittance_file_for_default_carrier,
    generate_boleto,
    register_payment,
)
from ..app.modules.plans.models import Plan
from ..app.modules.contracts.models import Contract
from ..app.modules.users.models import User
from ..app.modules.roles.models import Role
from ..app.modules.permissions.models import Permission
from ..app.core.security import hash_password
from ..app.modules.clients.models import Client
from ..app.modules.support.models import Ticket, TicketCategory, TicketMessage, Occurrence
from ..app.modules.support.service import (
    create_ticket, update_ticket, add_message, 
    create_category, get_categories, get_ticket_messages,
    create_occurrence, update_occurrence
)
from ..app.modules.support.schemas import (
    TicketCreate, TicketUpdate, MessageCreate, CategoryCreate,
    OccurrenceCreate, OccurrenceUpdate
)
from ..app.modules.service_orders.models import ServiceOrder, ServiceOrderItem
from ..app.modules.service_orders.schemas import ServiceOrderCreate, ServiceOrderUpdate, ServiceOrderItemCreate, AssignTechnician
from ..app.modules.service_orders.service import create_order, update_order, assign_technician, complete_order, add_item
from ..app.modules.technician_app.service import list_assigned_orders, start_order, complete_order as tech_complete_order
from ..app.modules.stock.models import StockItem, Warehouse, StockMovement
from ..app.modules.billing.models import Title
from ..app.core.security import verify_password, hash_password, create_access_token


def create_app() -> Flask:
    # Importar todos os modelos para garantir relacionamentos do SQLAlchemy
    import_all_models()
    # Garantir colunas críticas para queries do painel
    try:
        ensure_required_columns()
    except Exception:
        pass

    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    app = Flask(__name__)

    # Configure session
    app.secret_key = getattr(settings, 'SECRET_KEY', secrets.token_hex(32))
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    @app.context_processor
    def inject_user():
        return dict(
            current_user=session.get("user"),
            access_token=session.get("access_token"),
            api_base_url=os.getenv("API_PUBLIC_URL", "http://localhost:8000")
        )

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Login page and authentication handler"""
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            remember = request.form.get("remember") == "on"

            # TODO: Implement real authentication against database
            # For now, using simple validation for demo purposes
            if username and password:
                # In production, validate against User table with hashed password
                # Example: user = db.query(User).filter(User.username == username).first()
                # if user and verify_password(password, user.hashed_password):

                # Simple demo validation (REPLACE IN PRODUCTION)
                if username == "admin" and password == "admin123":
                    session["user"] = username
                    session["authenticated"] = True
                    # Generate JWT token for API access
                    # In a real scenario, we would use the user's ID
                    session["access_token"] = create_access_token(subject=username)
                    session.permanent = remember
                    flash("Login realizado com sucesso!", "success")
                    return redirect(url_for("dashboard"))
                else:
                    flash("Usuário ou senha inválidos", "error")
            else:
                flash("Por favor, preencha todos os campos", "error")

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        """Logout handler - clears session and redirects to login"""
        session.clear()
        flash("Logout realizado com sucesso", "info")
        return redirect(url_for("login"))

    @app.route("/profile")
    def profile():
        """User profile page"""
        if not session.get("authenticated"):
            flash("Por favor, faça login para acessar esta página", "warning")
            return redirect(url_for("login"))
        # TODO: Implement profile page
        return render_template("profile.html", user=session.get("user"))

    @app.route("/settings")
    def user_settings():
        """User settings page"""
        if not session.get("authenticated"):
            flash("Por favor, faça login para acessar esta página", "warning")
            return redirect(url_for("login"))
        
        username = session.get("user")
        user = None
        if username:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.username == username).first()
            finally:
                db.close()
        
        return render_template("settings.html", user=user or username)

    @app.route("/communication/queue")
    def communication_queue():
        db = SessionLocal()
        q = db.query(MessageQueue)
        status_ = request.args.get("status")
        channel = request.args.get("channel")
        contract_id = request.args.get("contract_id")
        client_id = request.args.get("client_id")
        provider = request.args.get("provider")
        if status_:
            q = q.filter(MessageQueue.status == status_)
        if channel:
            q = q.filter(MessageQueue.channel == channel)
        if contract_id:
            try:
                q = q.filter(MessageQueue.contract_id == int(contract_id))
            except ValueError:
                pass
        if client_id:
            try:
                q = q.filter(MessageQueue.client_id == int(client_id))
            except ValueError:
                pass
        if provider:
            q = q.filter(MessageQueue.provider == provider)
        items = q.order_by(MessageQueue.created_at.desc()).limit(100).all()
        db.close()
        return render_template("admin_communication_queue.html", items=items, status_=status_, channel=channel, contract_id=contract_id, client_id=client_id, provider=provider)

    @app.route("/communication/queue/requeue/<int:message_id>")
    def communication_requeue(message_id: int):
        db = SessionLocal()
        try:
            requeue_failed(db, message_id)
        finally:
            db.close()




    @app.route("/communication/queue/dispatch/<int:message_id>")
    def communication_dispatch_now(message_id: int):
        db = SessionLocal()
        try:
            msg = db.query(MessageQueue).filter(MessageQueue.id == message_id).first()
            if msg:
                dispatch_message(db, msg)
        finally:
            db.close()
        return redirect(url_for("communication_queue"))

    @app.route("/communication/history")
    def communication_history():
        db = SessionLocal()
        q = db.query(MessageQueue)
        status_ = request.args.get("status")
        channel = request.args.get("channel")
        contract_id = request.args.get("contract_id")
        client_id = request.args.get("client_id")
        provider = request.args.get("provider")
        if contract_id:
            try:
                q = q.filter(MessageQueue.contract_id == int(contract_id))
            except ValueError:
                pass
        if client_id:
            try:
                q = q.filter(MessageQueue.client_id == int(client_id))
            except ValueError:
                pass
        if provider:
            q = q.filter(MessageQueue.provider == provider)
        if status_:
            q = q.filter(MessageQueue.status == status_)
        if channel:
            q = q.filter(MessageQueue.channel == channel)
        items = q.order_by(MessageQueue.created_at.desc()).limit(200).all()
        db.close()
        return render_template("admin_communication_history.html", items=items, status_=status_, channel=channel, contract_id=contract_id, client_id=client_id, provider=provider)

    @app.route("/dashboard")
    def dashboard():
        db = SessionLocal()
        overview = dashboard_overview(db)
        comm = timeseries_communication_success(db)
        os_ts = timeseries_service_orders_status(db)
        from ..app.modules.reports.service import communication_success_by_provider, sample_onu_metrics, occurrences_summary
        providers_stats = communication_success_by_provider(db)
        onu_summary = sample_onu_metrics(db, limit=8)
        occ_summary = occurrences_summary(db, days=30)
        # build simple SVG path for communication success (0-100 scaled to height 120)
        w = 420
        h = 120
        step = w // max(1, len(comm) - 1)
        points = []
        for idx, p in enumerate(comm):
            x = idx * step
            y = h - int((p["success_rate"] / 100.0) * h)
            points.append((x, y))
        path_d = ""
        if points:
            path_d = f"M {points[0][0]},{points[0][1]} " + " ".join([f"L {x},{y}" for x, y in points[1:]])
        # build simple bar charts for ocorrências por categoria e severidade
        svg_w = 420
        svg_h = 140
        # categoria bars
        cat_items = sorted(occ_summary.get("by_category", {}).items(), key=lambda x: x[0])
        max_cat = max([c for _, c in cat_items], default=1)
        cat_bars = []
        if cat_items:
            bar_w = max(24, svg_w // (len(cat_items) * 2))
            gap = bar_w // 2
            for idx, (label, count) in enumerate(cat_items):
                x = idx * (bar_w + gap) + gap
                h_bar = int((count / max_cat) * (svg_h - 30))
                y = svg_h - h_bar - 20
                cat_bars.append({"x": x, "y": y, "w": bar_w, "h": h_bar, "label": label, "count": count})
        # severity bars
        sev_items = sorted(occ_summary.get("by_severity", {}).items(), key=lambda x: x[0])
        max_sev = max([c for _, c in sev_items], default=1)
        sev_bars = []
        if sev_items:
            bar_w2 = max(24, svg_w // (len(sev_items) * 2))
            gap2 = bar_w2 // 2
            for idx, (label, count) in enumerate(sev_items):
                x = idx * (bar_w2 + gap2) + gap2
                h_bar = int((count / max_sev) * (svg_h - 30))
                y = svg_h - h_bar - 20
                sev_bars.append({"x": x, "y": y, "w": bar_w2, "h": h_bar, "label": label, "count": count})

        db.close()
        return render_template(
            "dashboard.html",
            overview=overview,
            comm=comm,
            os_ts=os_ts,
            comm_path=path_d,
            comm_w=w,
            comm_h=h,
            providers_stats=providers_stats,
            onu_summary=onu_summary,
            occ_summary=occ_summary,
            occ_cat_bars=cat_bars,
            occ_sev_bars=sev_bars,
            occ_svg_w=svg_w,
            occ_svg_h=svg_h,
        )

    @app.route("/service-orders", methods=["GET", "POST"])
    def service_orders():
        db = SessionLocal()
        
        if request.method == "POST":
            try:
                from ..app.modules.service_orders.schemas import ServiceOrderCreate, ServiceOrderItemCreate
                from ..app.modules.service_orders.service import create_order, update_order
                from ..app.modules.service_orders.schemas import ServiceOrderUpdate
                from datetime import datetime
                
                oid = request.form.get("id")
                contract_id_raw = request.form.get("contract_id")
                scheduled_date_raw = request.form.get("scheduled_date")
                
                if oid:
                    # Update
                    o = db.query(ServiceOrder).filter(ServiceOrder.id == oid).first()
                    if o:
                        data = ServiceOrderUpdate(
                            technician_name=request.form.get("technician"),
                            type=request.form.get("type"),
                            scheduled_at=datetime.fromisoformat(scheduled_date_raw) if scheduled_date_raw else None,
                            notes=request.form.get("description"),
                        )
                        update_order(db, o, data)
                else:
                    # Create
                    data = ServiceOrderCreate(
                        contract_id=int(contract_id_raw) if contract_id_raw else None,
                        technician_name=request.form.get("technician"),
                        type=request.form.get("type") or "repair",
                        priority="medium",
                        status="open",
                        scheduled_at=datetime.fromisoformat(scheduled_date_raw) if scheduled_date_raw else None,
                        notes=request.form.get("description"),
                        items=[ServiceOrderItemCreate(description=request.form.get("description") or "Serviço", quantity=1)]
                    )
                    create_order(db, data)
            except Exception as e:
                print(f"Error creating/updating service order: {e}")
                
        q = db.query(ServiceOrder)
        status_ = request.args.get("status")
        tech = request.args.get("technician")
        if status_:
            q = q.filter(ServiceOrder.status == status_)
        if tech:
            q = q.filter(ServiceOrder.technician_name.ilike(f"%{tech}%"))
        orders = q.order_by(ServiceOrder.created_at.desc()).limit(100).all()
        items = []
        for o in orders:
            items.append({
                "id": o.id,
                "contract_id": o.contract_id,
                "ticket_id": o.ticket_id,
                "type": o.type,
                "priority": o.priority,
                "status": o.status,
                "technician_name": o.technician_name,
                "scheduled_at": o.scheduled_at.isoformat() if o.scheduled_at else None,
                "executed_at": o.executed_at.isoformat() if o.executed_at else None,
                "notes": o.notes,
                "created_at": o.created_at.isoformat() if o.created_at else None
            })
        db.close()
        return render_template("service_orders.html", items=items, status_=status_, technician=tech)

    @app.route("/admin/pops", methods=["GET", "POST"])
    def admin_pops():
        db = SessionLocal()
        if request.method == "POST":
            pid = request.form.get("id")
            if pid:
                p = db.query(POP).filter(POP.id == pid).first()
                if p:
                    p.name = request.form.get("name") or p.name
                    p.city = request.form.get("city") or p.city
                    p.address = request.form.get("address") or p.address
                    p.latitude = float(request.form.get("latitude") or 0.0)
                    p.longitude = float(request.form.get("longitude") or 0.0)
                    db.commit()
            else:
                p = POP(
                    name=request.form.get("name") or "",
                    city=request.form.get("city") or "",
                    address=request.form.get("address") or "",
                    latitude=float(request.form.get("latitude") or 0.0),
                    longitude=float(request.form.get("longitude") or 0.0),
                )
                db.add(p)
                db.commit()
        
        q = db.query(POP)
        name = request.args.get("name")
        city = request.args.get("city")
        if name:
            q = q.filter(POP.name.ilike(f"%{name}%"))
        if city:
            q = q.filter(POP.city.ilike(f"%{city}%"))
            
        items = q.order_by(POP.created_at.desc()).limit(100).all()
        db.close()
        return render_template("admin_pops.html", items=items)

    @app.route("/admin/pops/<int:pop_id>/delete", methods=["POST"])
    def admin_pops_delete(pop_id: int):
        db = SessionLocal()
        try:
            p = db.query(POP).filter(POP.id == pop_id).first()
            if p:
                db.delete(p)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "POP não encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()


    @app.route("/admin/nas", methods=["GET", "POST"])
    def admin_nas():
        db = SessionLocal()
        if request.method == "POST":
            nid = request.form.get("id")
            if nid:
                nas = db.query(NAS).filter(NAS.id == nid).first()
                if nas:
                    nas.name = request.form.get("name") or nas.name
                    nas.ip_address = request.form.get("ip_address") or nas.ip_address
                    nas.secret = request.form.get("secret") or nas.secret
                    nas.vendor = request.form.get("vendor") or nas.vendor
                    pop_id = request.form.get("pop_id")
                    nas.pop_id = int(pop_id) if pop_id else None
                    db.commit()
            else:
                nas = NAS(
                    name=request.form.get("name") or "",
                    ip_address=request.form.get("ip_address") or "",
                    secret=request.form.get("secret") or "",
                    vendor=request.form.get("vendor") or "",
                    pop_id=int(request.form.get("pop_id")) if request.form.get("pop_id") else None,
                )
                db.add(nas)
                db.commit()
        
        q = db.query(NAS)
        name = request.args.get("name")
        vendor = request.args.get("vendor")
        if name:
            q = q.filter(NAS.name.ilike(f"%{name}%"))
        if vendor:
            q = q.filter(NAS.vendor.ilike(f"%{vendor}%"))

        items = q.order_by(NAS.created_at.desc()).limit(100).all()
        pops = db.query(POP).order_by(POP.name.asc()).all()
        db.close()
        return render_template("admin_nas.html", items=items, pops=pops)

    @app.route("/admin/nas/<int:nas_id>/delete", methods=["POST"])
    def admin_nas_delete(nas_id: int):
        db = SessionLocal()
        try:
            nas = db.query(NAS).filter(NAS.id == nas_id).first()
            if nas:
                db.delete(nas)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "NAS não encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()


    @app.route("/admin/variables", methods=["GET", "POST"])
    def admin_variables():
        db = SessionLocal()
        if request.method == "POST":
            vid = request.form.get("id")
            if vid:
                var = db.query(SystemVariable).filter(SystemVariable.id == vid).first()
                if var:
                    var.key = request.form.get("key") or var.key
                    var.value = request.form.get("value") or var.value
                    var.description = request.form.get("description") or var.description
                    db.commit()
            else:
                var = SystemVariable(
                    key=request.form.get("key") or "",
                    value=request.form.get("value") or "",
                    description=request.form.get("description") or "",
                )
                db.add(var)
                db.commit()
        
        q = db.query(SystemVariable)
        key = request.args.get("key")
        description = request.args.get("description")
        if key:
            q = q.filter(SystemVariable.key.ilike(f"%{key}%"))
        if description:
            q = q.filter(SystemVariable.description.ilike(f"%{description}%"))
            
        items = q.order_by(SystemVariable.created_at.desc()).limit(100).all()
        db.close()
        return render_template("admin_variables.html", items=items)

    @app.route("/admin/variables/<int:var_id>/delete", methods=["POST"])
    def admin_variables_delete(var_id: int):
        db = SessionLocal()
        try:
            var = db.query(SystemVariable).filter(SystemVariable.id == var_id).first()
            if var:
                db.delete(var)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Variável não encontrada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()


    @app.route("/admin/finance/companies", methods=["GET", "POST"])
    def admin_finance_companies():
        db = SessionLocal()
        if request.method == "POST":
            cid = request.form.get("id")
            if cid:
                c = db.query(Company).filter(Company.id == cid).first()
                if c:
                    c.name = request.form.get("name") or c.name
                    c.legal_name = request.form.get("legal_name") or c.legal_name
                    c.document = request.form.get("document") or c.document
                    c.email = request.form.get("email") or c.email
                    c.phone = request.form.get("phone") or c.phone
                    c.is_active = request.form.get("active") == "on"
                    db.commit()
            else:
                c = Company(
                    name=request.form.get("name") or "",
                    legal_name=request.form.get("legal_name") or "",
                    document=request.form.get("document") or "",
                    email=request.form.get("email") or "",
                    phone=request.form.get("phone") or "",
                    is_active=request.form.get("active") == "on",
                )
                db.add(c)
                db.commit()
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
                 return {"success": True, "message": "Empresa salva com sucesso"}
        
        q = db.query(Company)
        name = request.args.get("name")
        document = request.args.get("document")
        if name:
            q = q.filter(Company.name.ilike(f"%{name}%"))
        if document:
            q = q.filter(Company.document.ilike(f"%{document}%"))
            
        companies_list = q.order_by(Company.created_at.desc()).limit(100).all()
        items = []
        for c in companies_list:
            items.append({
                "id": c.id,
                "name": c.name,
                "legal_name": c.legal_name,
                "document": c.document,
                "email": c.email,
                "phone": c.phone,
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat() if c.created_at else None
            })
        db.close()
        return render_template("admin_finance_companies.html", items=items)

    @app.route("/admin/finance/companies/<int:id>/delete", methods=["POST"])
    def admin_finance_companies_delete(id: int):
        db = SessionLocal()
        try:
            c = db.query(Company).filter(Company.id == id).first()
            if c:
                db.delete(c)
                db.commit()
        except Exception:
            pass
        finally:
            db.close()
        return {"success": True}

    @app.route("/admin/finance/carriers", methods=["GET", "POST"])
    def admin_finance_carriers():
        db = SessionLocal()
        if request.method == "POST":
            cid = request.form.get("id")
            if cid:
                ca = db.query(Carrier).filter(Carrier.id == cid).first()
                if ca:
                    ca.name = request.form.get("name") or ca.name
                    ca.bank_code = request.form.get("bank_code") or ca.bank_code
                    ca.agency = request.form.get("agency") or ca.agency
                    ca.account = request.form.get("account") or ca.account
                    ca.wallet = request.form.get("wallet") or ca.wallet
                    ca.cnab_layout = request.form.get("cnab_layout") or ca.cnab_layout
                    db.commit()
            else:
                ca = Carrier(
                    name=request.form.get("name") or "",
                    bank_code=request.form.get("bank_code") or "",
                    agency=request.form.get("agency") or "",
                    account=request.form.get("account") or "",
                    wallet=request.form.get("wallet") or "",
                    cnab_layout=request.form.get("cnab_layout") or "400",
                    is_active=True,
                )
                db.add(ca)
                db.commit()
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
                 return {"success": True, "message": "Portador salvo com sucesso"}

        q = db.query(Carrier)
        name = request.args.get("name")
        bank_code = request.args.get("bank_code")
        if name:
            q = q.filter(Carrier.name.ilike(f"%{name}%"))
        if bank_code:
            q = q.filter(Carrier.bank_code == bank_code)

        carriers = q.order_by(Carrier.created_at.desc()).limit(100).all()
        items = []
        for c in carriers:
            items.append({
                "id": c.id,
                "name": c.name,
                "bank_code": c.bank_code,
                "agency": c.agency,
                "account": c.account,
                "wallet": c.wallet,
                "cnab_layout": c.cnab_layout,
                "created_at": c.created_at.isoformat() if c.created_at else None
            })
        db.close()
        return render_template("admin_finance_carriers.html", items=items)

    @app.route("/admin/finance/carriers/<int:id>/delete", methods=["POST"])
    def admin_finance_carriers_delete(id: int):
        db = SessionLocal()
        try:
            c = db.query(Carrier).filter(Carrier.id == id).first()
            if c:
                db.delete(c)
                db.commit()
        except Exception:
            pass
        finally:
            db.close()
        return {"success": True}

    @app.route("/admin/finance/receipts", methods=["GET", "POST"])
    def admin_finance_receipts():
        db = SessionLocal()
        if request.method == "POST":
            rid = request.form.get("id")
            if rid:
                r = db.query(ReceiptPoint).filter(ReceiptPoint.id == rid).first()
                if r:
                    r.name = request.form.get("name") or r.name
                    r.description = request.form.get("description") or r.description
                    if request.form.get("company_id"):
                        r.company_id = int(request.form.get("company_id"))
                    db.commit()
            else:
                rp = ReceiptPoint(
                    name=request.form.get("name") or "",
                    description=request.form.get("description") or "",
                    company_id=int(request.form.get("company_id")),
                )
                db.add(rp)
                db.commit()
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
                 return {"success": True, "message": "Ponto de recebimento salvo com sucesso"}
        
        q = db.query(ReceiptPoint)
        name = request.args.get("name")
        description = request.args.get("description")
        
        if name:
            q = q.filter(ReceiptPoint.name.ilike(f"%{name}%"))
        if description:
            q = q.filter(ReceiptPoint.description.ilike(f"%{description}%"))
            
        receipts_list = q.order_by(ReceiptPoint.created_at.desc()).limit(100).all()
        items = []
        for r in receipts_list:
            items.append({
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "company": {
                    "id": r.company_id,
                    "name": r.company.name if r.company else None,
                },
                "created_at": r.created_at.isoformat() if r.created_at else None
            })
        companies = db.query(Company).order_by(Company.name.asc()).all()
        db.close()
        return render_template("admin_finance_receipts.html", items=items, companies=companies)

    @app.route("/admin/finance/receipts/<int:id>/delete", methods=["POST"])
    def admin_finance_receipts_delete(id: int):
        db = SessionLocal()
        try:
            r = db.query(ReceiptPoint).filter(ReceiptPoint.id == id).first()
            if r:
                db.delete(r)
                db.commit()
        except Exception:
            pass
        finally:
            db.close()
        return {"success": True}

    @app.route("/admin/finance/parameters", methods=["GET", "POST"])
    def admin_finance_parameters():
        db = SessionLocal()
        if request.method == "POST":
            pid = request.form.get("id")
            default_carrier_id = request.form.get("default_carrier_id")
            
            if pid:
                p = db.query(FinancialParameter).filter(FinancialParameter.id == pid).first()
                if p:
                    p.company_id = int(request.form.get("company_id"))
                    p.default_carrier_id = int(default_carrier_id) if default_carrier_id else None
                    p.fine_percent = float(request.form.get("fine_percent") or 2.0)
                    p.interest_percent = float(request.form.get("interest_percent") or 1.0)
                    p.send_email_on_issue = request.form.get("send_email_on_issue") == "on"
                    db.commit()
            else:
                p = FinancialParameter(
                    company_id=int(request.form.get("company_id")),
                    default_carrier_id=int(default_carrier_id) if default_carrier_id else None,
                    fine_percent=float(request.form.get("fine_percent") or 2.0),
                    interest_percent=float(request.form.get("interest_percent") or 1.0),
                    send_email_on_issue=request.form.get("send_email_on_issue") == "on",
                )
                db.add(p)
                db.commit()
            
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
                 return {"success": True, "message": "Parâmetro salvo com sucesso"}
        
        q = db.query(FinancialParameter)
        # Add filtering if needed, though usually few parameters exist
        company_id = request.args.get("company_id")
        if company_id:
            try:
                cid = int(company_id)
                q = q.filter(FinancialParameter.company_id == cid)
            except ValueError:
                pass

        params_list = q.order_by(FinancialParameter.created_at.desc()).limit(100).all()
        items = []
        for p in params_list:
            items.append({
                "id": p.id,
                "company": {
                    "id": p.company_id,
                    "name": p.company.name if p.company else None,
                },
                "carrier": {
                    "id": p.default_carrier_id,
                    "name": p.carrier.name if p.carrier else None,
                },
                "fine_percent": p.fine_percent,
                "interest_percent": p.interest_percent,
                "send_email_on_issue": p.send_email_on_issue,
                "created_at": p.created_at.isoformat() if p.created_at else None
            })
        companies = db.query(Company).order_by(Company.name.asc()).all()
        carriers = db.query(Carrier).order_by(Carrier.name.asc()).all()
        db.close()
        return render_template("admin_finance_params.html", items=items, companies=companies, carriers=carriers)

    @app.route("/admin/finance/parameters/<int:id>/delete", methods=["POST"])
    def admin_finance_parameters_delete(id: int):
        db = SessionLocal()
        try:
            p = db.query(FinancialParameter).filter(FinancialParameter.id == id).first()
            if p:
                db.delete(p)
                db.commit()
        except Exception:
            pass
        finally:
            db.close()
        return {"success": True}

    @app.route("/admin/finance/remittance", methods=["GET", "POST"])
    def admin_finance_remittance():
        from datetime import date

        db = SessionLocal()
        content: str | None = None
        error: str | None = None
        form_values = {
            "mode": "bank",
            "bank_code": "",
            "layout": "400",
            "due_from": "",
            "due_to": "",
        }
        try:
            if request.method == "POST":
                mode = (request.form.get("mode") or "bank").strip()
                due_from_raw = request.form.get("due_from") or ""
                due_to_raw = request.form.get("due_to") or ""
                bank_code_form = (request.form.get("bank_code") or "").strip()
                layout_form = (request.form.get("layout") or "400").strip()

                form_values.update({
                    "mode": mode,
                    "bank_code": bank_code_form,
                    "layout": layout_form,
                    "due_from": due_from_raw,
                    "due_to": due_to_raw,
                })

                df = None
                dt = None
                try:
                    if due_from_raw:
                        df = date.fromisoformat(due_from_raw)
                    if due_to_raw:
                        dt = date.fromisoformat(due_to_raw)
                except ValueError:
                    error = "Datas inválidas. Use AAAA-MM-DD."

                if error is None:
                    if mode == "bank":
                        bank_code = bank_code_form
                        layout = layout_form
                        if not bank_code:
                            error = "Informe o código do banco."
                        else:
                            try:
                                content = generate_remittance_file(db, bank_code, df, dt, layout)
                            except Exception as e:
                                error = f"Erro ao gerar remessa: {e}"
                    elif mode == "default":
                        try:
                            content = generate_remittance_file_for_default_carrier(db, df, dt)
                        except Exception as e:
                            error = f"Erro ao gerar remessa padrão: {e}"

            carriers = db.query(Carrier).order_by(Carrier.name.asc()).all()
        finally:
            db.close()
        return render_template("admin_finance_remittance.html", content=content, error=error, carriers=carriers, form_values=form_values)

    @app.route("/admin/finance/remittance/download", methods=["POST"])
    def admin_finance_remittance_download():
        from datetime import date, datetime

        db = SessionLocal()
        content: str = ""
        filename: str = "remessa_cnab.txt"
        try:
            mode = (request.form.get("mode") or "bank").strip()
            due_from_raw = request.form.get("due_from") or ""
            due_to_raw = request.form.get("due_to") or ""
            df = None
            dt = None
            if due_from_raw:
                try:
                    df = date.fromisoformat(due_from_raw)
                except ValueError:
                    pass
            if due_to_raw:
                try:
                    dt = date.fromisoformat(due_to_raw)
                except ValueError:
                    pass

            today_str = datetime.utcnow().strftime("%Y%m%d")
            if mode == "bank":
                bank_code = (request.form.get("bank_code") or "").strip()
                layout = (request.form.get("layout") or "400").strip()
                content = generate_remittance_file(db, bank_code, df, dt, layout)
                filename = f"remessa_{bank_code}_{layout}_{today_str}.txt"
            else:
                content = generate_remittance_file_for_default_carrier(db, df, dt)
                filename = f"remessa_default_{today_str}.txt"
        finally:
            db.close()

        resp = make_response(content)
        resp.headers["Content-Type"] = "text/plain; charset=utf-8"
        resp.headers["Content-Disposition"] = f"attachment; filename=\"{filename}\""
        return resp

    @app.route("/admin/finance/client", methods=["GET"]) 
    def admin_finance_client():
        from datetime import date

        db = SessionLocal()
        items = []
        totals = {"open": 0.0, "paid": 0.0, "overdue": 0.0}
        try:
            from ..app.modules.billing.models import Title
            client_id_raw = request.args.get("client_id") or ""
            status_ = (request.args.get("status") or "").strip()
            due_from_raw = request.args.get("due_from") or ""
            due_to_raw = request.args.get("due_to") or ""
            df = date.fromisoformat(due_from_raw) if due_from_raw else None
            dt = date.fromisoformat(due_to_raw) if due_to_raw else None

            q = db.query(Title)
            if client_id_raw:
                try:
                    cid = int(client_id_raw)
                    from ..app.modules.contracts.models import Contract
                    q = q.join(Contract, Title.contract_id == Contract.id).filter(Contract.client_id == cid)
                except Exception:
                    pass
            if status_:
                q = q.filter(Title.status == status_)
            if df:
                q = q.filter(Title.due_date >= df)
            if dt:
                q = q.filter(Title.due_date <= dt)
            items = q.order_by(Title.due_date.asc()).limit(200).all()
            for t in items:
                if t.status in totals:
                    totals[t.status] += float(t.amount)
        finally:
            db.close()
        return render_template("admin_finance_client_modern.html", items=items, totals=totals, client_id=client_id_raw, status_=status_, due_from=due_from_raw, due_to=due_to_raw)

    @app.route("/admin/finance/title", methods=["GET", "POST"]) 
    def admin_finance_title():
        db = SessionLocal()
        title = None
        adjustments = []
        effective_amount = None
        error = None
        message = None
        try:
            from ..app.modules.billing.models import Title
            from ..app.modules.billing.models import TitleAdjustment
            from ..app.modules.billing.service import calculate_title_effective_amount
            title_id_raw = (request.values.get("title_id") or request.args.get("title_id") or "").strip()
            document_number = (request.values.get("document_number") or request.args.get("document_number") or "").strip()
            if title_id_raw:
                try:
                    tid = int(title_id_raw)
                    title = db.query(Title).filter(Title.id == tid).first()
                except Exception:
                    error = "ID de título inválido"
            elif document_number:
                title = db.query(Title).filter(Title.document_number == document_number).first()
            if request.method == "POST" and title:
                action = (request.form.get("action") or "").strip()
                if action == "generate_boleto":
                    try:
                        t2 = generate_boleto(db, title)
                        title = t2
                        message = "Boleto gerado com sucesso"
                    except Exception as e:
                        error = f"Erro ao gerar boleto: {e}"
                elif action == "register_payment":
                    try:
                        amount_raw = request.form.get("amount") or "0"
                        method = (request.form.get("method") or "boleto").strip()
                        amount = float(amount_raw.replace(",", "."))
                        t2 = register_payment(db, title, amount, method)
                        title = t2
                        message = "Pagamento registrado"
                    except Exception as e:
                        error = f"Erro ao registrar pagamento: {e}"
            if title:
                adjustments = db.query(TitleAdjustment).filter(TitleAdjustment.title_id == title.id).order_by(TitleAdjustment.created_at.desc()).all()
                effective_amount = calculate_title_effective_amount(db, title.id)
        except Exception as e:
            error = f"Erro: {e}"
        finally:
            db.close()
        return render_template("admin_finance_title.html", title=title, adjustments=adjustments, effective_amount=effective_amount, error=error, message=message)

    @app.route("/admin/finance/promises", methods=["GET", "POST"])
    def admin_finance_promises():
        from datetime import date
        db = SessionLocal()
        try:
            from ..app.modules.billing.models import PaymentPromise
            if request.method == "POST":
                pid = request.form.get("id")
                if pid:
                    # Update
                    p = db.query(PaymentPromise).filter(PaymentPromise.id == pid).first()
                    if p:
                        p.promised_date = date.fromisoformat(request.form.get("promised_date")) if request.form.get("promised_date") else None
                        p.amount = float(request.form.get("amount").replace(",", ".")) if request.form.get("amount") else 0.0
                        p.status = request.form.get("status") or "pending"
                        p.notes = request.form.get("notes") or ""
                        db.commit()
                else:
                    # Create
                    p = PaymentPromise(
                        client_id=int(request.form.get("client_id")),
                        contract_id=int(request.form.get("contract_id")) if request.form.get("contract_id") else None,
                        title_id=int(request.form.get("title_id")) if request.form.get("title_id") else None,
                        promised_date=date.fromisoformat(request.form.get("promised_date")) if request.form.get("promised_date") else None,
                        amount=float(request.form.get("amount").replace(",", ".")) if request.form.get("amount") else 0.0,
                        status=request.form.get("status") or "pending",
                        notes=request.form.get("notes") or "",
                        created_by=session.get("user_id") # Assuming user_id is in session, or None
                    )
                    db.add(p)
                    db.commit()
                
                if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
                     return {"success": True, "message": "Promessa de pagamento salva com sucesso"}
            
            q = db.query(PaymentPromise)
            client_id = request.args.get("client_id")
            status_ = request.args.get("status")
            if client_id:
                try:
                    cid = int(client_id)
                    q = q.filter(PaymentPromise.client_id == cid)
                except ValueError:
                    pass
            if status_:
                q = q.filter(PaymentPromise.status == status_)
            
            items = q.order_by(PaymentPromise.promised_date.desc()).limit(100).all()
            return render_template("admin_payment_promises.html", items=items)
        finally:
            db.close()

    @app.route("/admin/finance/promises/<int:id>/delete", methods=["POST"])
    def admin_finance_promises_delete(id: int):
        db = SessionLocal()
        try:
            from ..app.modules.billing.models import PaymentPromise
            p = db.query(PaymentPromise).filter(PaymentPromise.id == id).first()
            if p:
                db.delete(p)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Promessa não encontrada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @app.route("/admin/finance/return", methods=["GET", "POST"])
    def admin_finance_return():
        from datetime import date

        db = SessionLocal()
        message = None
        error = None
        if request.method == "POST":
            file_name = request.form.get("file_name") or "retorno_cnab.txt"
            content = request.form.get("content") or ""
            items: list[dict] = []
            try:
                raw = content.strip().splitlines()
                for line in raw:
                    parts = [p.strip() for p in line.split(";")]
                    if len(parts) >= 4:
                        try:
                            title_id = int(parts[0])
                            status_str = parts[1]
                            value = float(parts[2].replace(",", "."))
                            occurred = date.fromisoformat(parts[3])
                            items.append({"title_id": title_id, "status": status_str, "value": value, "occurred_at": occurred})
                        except Exception:
                            continue
                from ..app.modules.billing.schemas import ReturnCreate
                from ..app.modules.billing.service import process_return

                rf = process_return(db, ReturnCreate(file_name=file_name, items=items))
                message = f"Retorno processado: {rf.total_items} itens"
            except Exception as e:
                error = f"Erro ao processar retorno: {e}"
        db.close()
        return render_template("admin_finance_return.html", message=message, error=error)

    @app.route("/admin/invoices", methods=["GET", "POST"])
    def admin_invoices():
        from datetime import date
        db = SessionLocal()
        try:
            from ..app.modules.fiscal.models import Invoice
            from ..app.modules.fiscal.schemas import InvoiceCreate
            from ..app.modules.fiscal.service import create_invoice_record
            
            if request.method == "POST":
                try:
                    data = InvoiceCreate(
                        contract_id=int(request.form.get("contract_id")),
                        total_amount=float(request.form.get("total_amount") or 0),
                        service_description=request.form.get("service_description") or "Serviço de Internet",
                        number=str(int(datetime.utcnow().timestamp())), # Mock number generation
                        series="1",
                        status="draft",
                        municipality_code="0000000",
                        taxation_code="0000"
                    )
                    create_invoice_record(db, data)
                    flash("Nota fiscal criada (rascunho)", "success")
                except Exception as e:
                    flash(f"Erro ao criar nota: {e}", "error")
                return redirect(url_for("admin_invoices"))

            q = db.query(Invoice)
            status_ = request.args.get("status")
            contract_id = request.args.get("contract_id")
            
            if status_:
                q = q.filter(Invoice.status == status_)
            if contract_id:
                try:
                    q = q.filter(Invoice.contract_id == int(contract_id))
                except ValueError:
                    pass
            
            items = q.order_by(Invoice.created_at.desc()).limit(100).all()
            return render_template("admin_invoices.html", items=items, status_=status_, contract_id=contract_id)
        finally:
            db.close()

    @app.route("/admin/invoices/<int:id>/emit", methods=["POST"])
    def admin_invoices_emit(id: int):
        db = SessionLocal()
        try:
            from ..app.modules.fiscal.service import emit_invoice
            emit_invoice(db, id)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @app.route("/admin/backups", methods=["GET", "POST"])
    def admin_backups():
        db = SessionLocal()
        if request.method == "POST":
            bid = request.form.get("id")
            if bid:
                job = db.query(BackupJob).filter(BackupJob.id == bid).first()
                if job:
                    job.name = request.form.get("name") or job.name
                    job.type = request.form.get("type") or job.type
                    job.schedule_cron = request.form.get("schedule_cron") or job.schedule_cron
                    job.storage_dir = request.form.get("storage_dir") or job.storage_dir
                    job.is_active = request.form.get("is_active") == "on"
                    db.commit()
            else:
                job = BackupJob(
                    name=request.form.get("name") or "",
                    type=request.form.get("type") or "database",
                    schedule_cron=request.form.get("schedule_cron") or None,
                    storage_dir=request.form.get("storage_dir") or "backups",
                    is_active=request.form.get("is_active") == "on",
                )
                db.add(job)
                db.commit()
        
        q = db.query(BackupJob)
        name = request.args.get("name")
        type_ = request.args.get("type")
        if name:
            q = q.filter(BackupJob.name.ilike(f"%{name}%"))
        if type_:
            q = q.filter(BackupJob.type == type_)
            
        jobs = q.order_by(BackupJob.created_at.desc()).limit(100).all()
        execs = db.query(BackupExecution).order_by(BackupExecution.started_at.desc()).limit(50).all()
        db.close()
        return render_template("admin_backups.html", jobs=jobs, execs=execs)

    @app.route("/admin/backups/<int:job_id>/delete", methods=["POST"])
    def admin_backups_delete(job_id: int):
        db = SessionLocal()
        try:
            job = db.query(BackupJob).filter(BackupJob.id == job_id).first()
            if job:
                db.delete(job)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Backup Job não encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()


    @app.route("/admin/backups/run/<int:job_id>")
    def admin_backups_run(job_id: int):
        db = SessionLocal()
        try:
            job = db.query(BackupJob).filter(BackupJob.id == job_id).first()
            if job:
                trigger_backup(db, job)
        finally:
            db.close()
        return redirect(url_for("admin_backups"))

    @app.route("/admin/network/assignments", methods=["GET", "POST"])
    def admin_network_assignments():
        db = SessionLocal()
        
        if request.method == "POST":
            # Handle Edit/Update of Assignment
            c_id = request.form.get("contract_id")
            if c_id:
                assign = db.query(ContractNetworkAssignment).filter(ContractNetworkAssignment.contract_id == int(c_id)).first()
                if not assign:
                    # Create if not exists (though usually created by contract approval)
                    assign = ContractNetworkAssignment(contract_id=int(c_id))
                    db.add(assign)
                
                assign.device_id = int(request.form.get("device_id")) if request.form.get("device_id") else None
                assign.ip_pool_id = int(request.form.get("ip_pool_id")) if request.form.get("ip_pool_id") else None
                assign.vlan_id = int(request.form.get("vlan_id")) if request.form.get("vlan_id") else None
                assign.profile_id = int(request.form.get("profile_id")) if request.form.get("profile_id") else None
                assign.static_ip = request.form.get("static_ip") or None
                assign.cgnat = request.form.get("cgnat") == "on"
                
                assign.pppoe_user = request.form.get("pppoe_user") or None
                assign.pppoe_password = request.form.get("pppoe_password") or None
                assign.mac_address = request.form.get("mac_address") or None
                assign.wifi_ssid = request.form.get("wifi_ssid") or None
                assign.wifi_password = request.form.get("wifi_password") or None
                
                db.commit()
                flash(f"Atribuição do contrato {c_id} atualizada!", "success")
                return redirect(url_for("admin_network_assignments"))

        q = db.query(ContractNetworkAssignment).options(
            joinedload(ContractNetworkAssignment.device),
            joinedload(ContractNetworkAssignment.ip_pool),
            joinedload(ContractNetworkAssignment.vlan),
            joinedload(ContractNetworkAssignment.profile)
        )
        status_ = request.args.get("status")
        contract_id = request.args.get("contract_id")
        message = request.args.get("msg")
        if status_:
            q = q.filter(ContractNetworkAssignment.status == status_)
        if contract_id:
            q = q.filter(ContractNetworkAssignment.contract_id == int(contract_id))
        items = q.order_by(ContractNetworkAssignment.updated_at.desc()).limit(100).all()
        
        # Load options for dropdowns
        devices = db.query(NetworkDevice).order_by(NetworkDevice.name).all()
        pools = db.query(IPPool).order_by(IPPool.name).all()
        vlans = db.query(VLAN).order_by(VLAN.name).all()
        profiles = db.query(ServiceProfile).order_by(ServiceProfile.name).all()
        
        try:
            return render_template("admin_network_assignments.html", items=items, status_=status_, contract_id=contract_id, message=message, devices=devices, pools=pools, vlans=vlans, profiles=profiles)
        finally:
            db.close()

    @app.route("/admin/network/olt-status")
    def admin_network_olt_status():
        db = SessionLocal()
        items = []
        device_id_raw = request.args.get("device_id") or ""
        contract_id_raw = request.args.get("contract_id") or ""
        try:
            from ..app.modules.network.models import ContractNetworkAssignment, NetworkDevice
            from ..app.modules.network.service import get_onu_status
            q = (
                db.query(ContractNetworkAssignment)
                .join(NetworkDevice, ContractNetworkAssignment.device_id == NetworkDevice.id)
                .filter(NetworkDevice.vendor.in_(["huawei", "zte", "vsol"]))
            )
            if device_id_raw:
                try:
                    did = int(device_id_raw)
                    q = q.filter(ContractNetworkAssignment.device_id == did)
                except Exception:
                    pass
            if contract_id_raw:
                try:
                    cid = int(contract_id_raw)
                    q = q.filter(ContractNetworkAssignment.contract_id == cid)
                except Exception:
                    pass
            for a in q.order_by(ContractNetworkAssignment.updated_at.desc()).limit(50).all():
                try:
                    status = get_onu_status(db, a.device_id, str(a.contract_id))
                    items.append({
                        "contract_id": a.contract_id,
                        "device_name": a.device.name if a.device else "-",
                        "vendor": status.get("vendor"),
                        "onu_id": status.get("onu_id"),
                        "online": status.get("online"),
                        "rx_power_dbm": status.get("rx_power_dbm"),
                        "tx_power_dbm": status.get("tx_power_dbm"),
                        "uptime_seconds": status.get("uptime_seconds"),
                    })
                except Exception:
                    continue
            devices = db.query(NetworkDevice).filter(NetworkDevice.vendor.in_(["huawei", "zte", "vsol"])) .order_by(NetworkDevice.name.asc()).all()
        finally:
            db.close()
        return render_template("admin_olt_status.html", items=items, devices=devices, device_id=device_id_raw, contract_id=contract_id_raw)







    @app.route("/admin/support/occurrences/edit/<int:occurrence_id>", methods=["GET", "POST"]) 
    def admin_support_occurrence_edit(occurrence_id: int):
        db = SessionLocal()
        message = None
        error = None
        occurrence = None
        try:
            from ..app.modules.support.models import Occurrence
            from ..app.modules.support.schemas import OccurrenceUpdate
            from ..app.modules.support.service import update_occurrence
            occurrence = db.query(Occurrence).filter(Occurrence.id == occurrence_id).first()
            if not occurrence:
                error = "Ocorrência não encontrada"
            elif request.method == "POST":
                data = OccurrenceUpdate(
                    status=(request.form.get("status") or occurrence.status),
                    severity=(request.form.get("severity") or occurrence.severity),
                    description=(request.form.get("description") or occurrence.description),
                    closed_at=None,
                    ticket_id=int(request.form.get("ticket_id")) if request.form.get("ticket_id") else occurrence.ticket_id,
                    service_order_id=int(request.form.get("service_order_id")) if request.form.get("service_order_id") else occurrence.service_order_id,
                )
                occurrence = update_occurrence(db, occurrence, data)
                message = "Ocorrência atualizada"
        except Exception as e:
            error = f"Erro: {e}"
        finally:
            db.close()
        return render_template("admin_occurrence_edit.html", occurrence=occurrence, message=message, error=error)

    @app.route("/admin/support/occurrences/close/<int:occurrence_id>")
    def admin_support_occurrence_close(occurrence_id: int):
        db = SessionLocal()
        try:
            from ..app.modules.support.models import Occurrence
            from ..app.modules.support.schemas import OccurrenceUpdate
            from ..app.modules.support.service import update_occurrence
            from datetime import datetime
            o = db.query(Occurrence).filter(Occurrence.id == occurrence_id).first()
            if o:
                data = OccurrenceUpdate(status="closed", closed_at=datetime.utcnow())
                update_occurrence(db, o, data)
        finally:
            db.close()
        return redirect(url_for("admin_support_occurrences", status="open"))

    @app.route("/admin/support/occurrences/create-os/<int:occurrence_id>")
    def admin_support_occurrence_create_os(occurrence_id: int):
        db = SessionLocal()
        try:
            from ..app.modules.support.models import Occurrence
            from ..app.modules.service_orders.schemas import ServiceOrderCreate, ServiceOrderItemCreate
            from ..app.modules.service_orders.service import create_order
            from ..app.modules.support.schemas import OccurrenceUpdate
            from ..app.modules.support.service import update_occurrence
            o = db.query(Occurrence).filter(Occurrence.id == occurrence_id).first()
            if o:
                priority_map = {"urgent": "urgent", "high": "high", "medium": "medium", "low": "low"}
                pr = priority_map.get((o.severity or "medium").lower(), "medium")
                data = ServiceOrderCreate(
                    client_id=o.client_id,
                    contract_id=o.contract_id,
                    ticket_id=o.ticket_id,
                    type="repair",
                    priority=pr,
                    status="open",
                    technician_name=None,
                    scheduled_at=None,
                    notes=f"Gerada da ocorrência #{o.id}: {o.description}",
                    items=[ServiceOrderItemCreate(description="Diagnóstico", quantity=1)],
                )
                order = create_order(db, data)
                update_occurrence(db, o, OccurrenceUpdate(service_order_id=order.id))
        finally:
            db.close()
        return redirect(url_for("admin_support_occurrences"))

    @app.route("/admin/support/occurrences/export")
    def admin_support_occurrences_export():
        db = SessionLocal()
        content = ""
        filename = "occorrencias.csv"
        try:
            from ..app.modules.support.models import Occurrence
            import csv, io
            q = db.query(Occurrence)
            # same filters as list
            status_ = request.args.get("status") or ""
            severity = request.args.get("severity") or ""
            category = request.args.get("category") or ""
            contract_id_raw = request.args.get("contract_id") or ""
            client_id_raw = request.args.get("client_id") or ""
            opened_from_raw = request.args.get("opened_from") or ""
            opened_to_raw = request.args.get("opened_to") or ""
            from datetime import date
            from sqlalchemy import func
            if status_:
                q = q.filter(Occurrence.status == status_)
            if severity:
                q = q.filter(Occurrence.severity == severity)
            if category:
                q = q.filter(Occurrence.category == category)
            if contract_id_raw:
                try:
                    q = q.filter(Occurrence.contract_id == int(contract_id_raw))
                except Exception:
                    pass
            if client_id_raw:
                try:
                    q = q.filter(Occurrence.client_id == int(client_id_raw))
                except Exception:
                    pass
            if opened_from_raw:
                try:
                    of = date.fromisoformat(opened_from_raw)
                    q = q.filter(func.date(Occurrence.opened_at) >= of)
                except Exception:
                    pass
            if opened_to_raw:
                try:
                    ot = date.fromisoformat(opened_to_raw)
                    q = q.filter(func.date(Occurrence.opened_at) <= ot)
                except Exception:
                    pass
            items = q.order_by(Occurrence.created_at.desc()).limit(1000).all()
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["id", "client_id", "contract_id", "category", "severity", "status", "opened_at", "closed_at", "ticket_id", "service_order_id", "description"])
            for o in items:
                writer.writerow([o.id, o.client_id, o.contract_id, o.category, o.severity, o.status, o.opened_at, o.closed_at, o.ticket_id, o.service_order_id, o.description])
            content = buf.getvalue()
        finally:
            db.close()
        resp = make_response(content)
        resp.headers["Content-Type"] = "text/csv; charset=utf-8"
        resp.headers["Content-Disposition"] = f"attachment; filename=\"{filename}\""
        return resp

    @app.route("/admin/network/devices", methods=["GET", "POST"])
    def admin_network_devices():
        db = SessionLocal()
        if request.method == "POST":
            dev_id = request.form.get("id")
            if dev_id:
                dev = db.query(NetworkDevice).filter(NetworkDevice.id == int(dev_id)).first()
                if dev:
                    dev.name = request.form.get("name") or dev.name
                    dev.type = request.form.get("type") or dev.type
                    dev.vendor = request.form.get("vendor") or dev.vendor
                    dev.host = request.form.get("host") or dev.host
                    dev.port = int(request.form.get("port") or 8728)
                    dev.username = request.form.get("username") or dev.username
                    if request.form.get("password"):
                        dev.password = request.form.get("password")
                    dev.enabled = request.form.get("enabled") == "on"
            else:
                dev = NetworkDevice(
                    name=request.form.get("name") or "",
                    type=request.form.get("type") or "router",
                    vendor=request.form.get("vendor") or "generic",
                    host=request.form.get("host") or "",
                    port=int(request.form.get("port") or 8728),
                    username=request.form.get("username") or "",
                    password=request.form.get("password") or "",
                    enabled=request.form.get("enabled") == "on",
                )
                db.add(dev)
            db.commit()
        
        q = db.query(NetworkDevice)
        name = request.args.get("name")
        type_ = request.args.get("type")
        vendor = request.args.get("vendor")
        
        if name:
            q = q.filter(NetworkDevice.name.ilike(f"%{name}%"))
        if type_:
            q = q.filter(NetworkDevice.type == type_)
        if vendor:
            q = q.filter(NetworkDevice.vendor.ilike(f"%{vendor}%"))
            
        items = q.order_by(NetworkDevice.created_at.desc()).limit(100).all()
        try:
            return render_template("admin_network_devices.html", items=items)
        finally:
            db.close()

    @app.route("/admin/network/devices/<int:device_id>/delete", methods=["POST"])
    def admin_network_devices_delete(device_id: int):
        db = SessionLocal()
        try:
            dev = db.query(NetworkDevice).filter(NetworkDevice.id == device_id).first()
            if dev:
                db.delete(dev)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Dispositivo não encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @app.route("/admin/network/devices/<int:device_id>/test", methods=["POST"])
    def admin_network_devices_test(device_id: int):
        db = SessionLocal()
        try:
            success = test_device_connection(db, device_id)
            if success:
                return {"success": True, "message": "Conexão bem-sucedida!"}
            return {"success": False, "error": "Falha na conexão"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()


    @app.route("/admin/network/vlans", methods=["GET", "POST"])
    def admin_network_vlans():
        print("DEBUG: Entering admin_network_vlans")
        try:
            db = SessionLocal()
            if request.method == "POST":
                vid = request.form.get("id")
                if vid:
                    v = db.query(VLAN).filter(VLAN.id == vid).first()
                    if v:
                        v.device_id = int(request.form.get("device_id")) if request.form.get("device_id") else None
                        v.vlan_id = int(request.form.get("vlan_id") or 0)
                        v.name = request.form.get("name") or ""
                        v.purpose = request.form.get("purpose") or "clients"
                        db.commit()
                else:
                    vlan = VLAN(
                        device_id=int(request.form.get("device_id")) if request.form.get("device_id") else None,
                        vlan_id=int(request.form.get("vlan_id") or 0),
                        name=request.form.get("name") or "",
                        purpose=request.form.get("purpose") or "clients",
                    )
                    db.add(vlan)
                    db.commit()
            
            q = db.query(VLAN) # .options(joinedload(VLAN.device))
            name = request.args.get("name")
            purpose = request.args.get("purpose")
            vlan_id = request.args.get("vlan_id")
            
            if name:
                q = q.filter(VLAN.name.ilike(f"%{name}%"))
            if purpose:
                q = q.filter(VLAN.purpose == purpose)
            if vlan_id:
                try:
                    q = q.filter(VLAN.vlan_id == int(vlan_id))
                except ValueError:
                    pass
                    
            items = q.order_by(VLAN.created_at.desc()).limit(100).all()
            devices = db.query(NetworkDevice).order_by(NetworkDevice.name.asc()).all()
            try:
                print("DEBUG: Rendering template")
                return render_template("admin_network_vlans.html", items=items, devices=devices)
            finally:
                db.close()
        except Exception as e:
            print(f"DEBUG: Error in admin_network_vlans: {e}")
            import traceback
            traceback.print_exc()
            raise e

    @app.route("/admin/network/vlans/<int:id>/delete", methods=["POST"])
    def admin_network_vlans_delete(id: int):
        db = SessionLocal()
        try:
            v = db.query(VLAN).filter(VLAN.id == id).first()
            if v:
                db.delete(v)
                db.commit()
        except Exception:
            pass
        finally:
            db.close()
        return {"success": True}

    @app.route("/admin/network/pools", methods=["GET", "POST"])
    def admin_network_pools():
        db = SessionLocal()
        if request.method == "POST":
            pool_id = request.form.get("id")
            if pool_id:
                pool = db.query(IPPool).filter(IPPool.id == int(pool_id)).first()
                if pool:
                    pool.name = request.form.get("name") or pool.name
                    pool.cidr = request.form.get("cidr") or pool.cidr
                    pool.type = request.form.get("type") or pool.type
                    pool.gateway = request.form.get("gateway") or pool.gateway
                    pool.dns_primary = request.form.get("dns_primary") or pool.dns_primary
                    pool.dns_secondary = request.form.get("dns_secondary") or pool.dns_secondary
                    pool.device_id = int(request.form.get("device_id")) if request.form.get("device_id") else None
                    pool.vlan_id = int(request.form.get("vlan_id")) if request.form.get("vlan_id") else None
                    db.commit()
            else:
                pool = IPPool(
                    name=request.form.get("name") or "",
                    cidr=request.form.get("cidr") or "",
                    type=request.form.get("type") or "dynamic",
                    gateway=request.form.get("gateway") or "",
                    dns_primary=request.form.get("dns_primary") or "",
                    dns_secondary=request.form.get("dns_secondary") or "",
                    device_id=int(request.form.get("device_id")) if request.form.get("device_id") else None,
                    vlan_id=int(request.form.get("vlan_id")) if request.form.get("vlan_id") else None,
                )
                db.add(pool)
                db.commit()
        items = db.query(IPPool).options(joinedload(IPPool.device), joinedload(IPPool.vlan)).order_by(IPPool.created_at.desc()).limit(100).all()
        devices = db.query(NetworkDevice).order_by(NetworkDevice.name.asc()).all()
        vlans = db.query(VLAN).order_by(VLAN.vlan_id.asc()).all()
        try:
            return render_template("admin_network_pools.html", items=items, devices=devices, vlans=vlans)
        finally:
            db.close()

    @app.route("/admin/network/pools/<int:id>/delete", methods=["POST"])
    def admin_network_pools_delete(id: int):
        db = SessionLocal()
        try:
            pool = db.query(IPPool).filter(IPPool.id == id).first()
            if pool:
                db.delete(pool)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Pool não encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @app.route("/admin/network/profiles", methods=["GET", "POST"])
    def admin_network_profiles():
        db = SessionLocal()
        if request.method == "POST":
            pid = request.form.get("id")
            if pid:
                prof = db.query(ServiceProfile).filter(ServiceProfile.id == int(pid)).first()
                if prof:
                    prof.name = request.form.get("name") or prof.name
                    prof.download_speed_mbps = float(request.form.get("download_speed_mbps") or 0.0)
                    prof.upload_speed_mbps = float(request.form.get("upload_speed_mbps") or 0.0)
                    prof.burst_enabled = request.form.get("burst_enabled") == "on"
                    prof.burst_rate_percent = float(request.form.get("burst_rate_percent") or 0.0)
                    prof.burst_threshold_seconds = int(request.form.get("burst_threshold_seconds") or 0)
            else:
                prof = ServiceProfile(
                    name=request.form.get("name") or "",
                    download_speed_mbps=float(request.form.get("download_speed_mbps") or 0.0),
                    upload_speed_mbps=float(request.form.get("upload_speed_mbps") or 0.0),
                    burst_enabled=request.form.get("burst_enabled") == "on",
                    burst_rate_percent=float(request.form.get("burst_rate_percent") or 0.0),
                    burst_threshold_seconds=int(request.form.get("burst_threshold_seconds") or 0),
                )
                db.add(prof)
            db.commit()
        
        q = db.query(ServiceProfile)
        name = request.args.get("name")
        if name:
            q = q.filter(ServiceProfile.name.ilike(f"%{name}%"))
            
        items = q.order_by(ServiceProfile.created_at.desc()).limit(100).all()
        try:
            return render_template("admin_network_profiles.html", items=items)
        finally:
            db.close()

    @app.route("/admin/network/profiles/<int:id>/delete", methods=["POST"])
    def admin_network_profiles_delete(id: int):
        db = SessionLocal()
        try:
            prof = db.query(ServiceProfile).filter(ServiceProfile.id == id).first()
            if prof:
                db.delete(prof)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Perfil não encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @app.route("/admin/network/assignments/provision/<int:contract_id>")
    def admin_network_assignments_provision(contract_id: int):
        db = SessionLocal()
        try:
            provision_contract(db, contract_id)
            flash(f"Contrato {contract_id} provisionado com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao provisionar contrato {contract_id}: {str(e)}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_network_assignments"))

    @app.route("/admin/network/assignments/block/<int:contract_id>")
    def admin_network_assignments_block(contract_id: int):
        db = SessionLocal()
        try:
            block_contract(db, contract_id)
            flash(f"Contrato {contract_id} bloqueado com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao bloquear contrato {contract_id}: {str(e)}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_network_assignments"))

    @app.route("/admin/network/assignments/unblock/<int:contract_id>")
    def admin_network_assignments_unblock(contract_id: int):
        db = SessionLocal()
        try:
            unblock_contract(db, contract_id)
            flash(f"Contrato {contract_id} desbloqueado com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao desbloquear contrato {contract_id}: {str(e)}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_network_assignments"))

    @app.route("/admin/network/assignments/sync-billing/<int:contract_id>")
    def admin_network_assignments_sync_billing(contract_id: int):
        db = SessionLocal()
        try:
            sync_billing_blocking(db, contract_id)
            flash(f"Sincronização financeira realizada para o contrato {contract_id}!", "success")
        except Exception as e:
            flash(f"Erro ao sincronizar contrato {contract_id}: {str(e)}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_network_assignments"))

    @app.route("/api/network/radius/session/<username>")
    def api_network_radius_session(username: str):
        db = SessionLocal()
        try:
            session_data = get_radius_active_session(db, username)
            if session_data:
                return session_data.dict()
            return "null"
        finally:
            db.close()

    @app.route("/api/network/radius/history/<username>")
    def api_network_radius_history(username: str):
        db = SessionLocal()
        try:
            history = get_radius_usage_history(db, username)
            return [h.dict() for h in history]
        finally:
            db.close()




    @app.route("/network/blocked", methods=["GET", "POST"])
    def network_blocked():
        db = SessionLocal()
        
        if request.method == "POST":
            contract_id = request.form.get("contract_id")
            if contract_id:
                try:
                    block_contract(db, int(contract_id))
                    flash(f"Contrato {contract_id} bloqueado com sucesso.", "success")
                except Exception as e:
                    flash(f"Erro ao bloquear contrato: {str(e)}", "error")
        
        message = request.args.get("msg")
        
        q = db.query(ContractNetworkAssignment).filter(ContractNetworkAssignment.status == "blocked")
        contract_id_filter = request.args.get("contract_id")
        if contract_id_filter:
            try:
                q = q.filter(ContractNetworkAssignment.contract_id == int(contract_id_filter))
            except ValueError:
                pass
                
        assignments = q.order_by(ContractNetworkAssignment.updated_at.desc()).limit(100).all()
        items = []
        for a in assignments:
            items.append({
                "id": a.id,
                "contract_id": a.contract_id,
                "status": a.status,
                "ip_address": a.ip_address,
                "mac_address": a.mac_address,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None
            })
        try:
            return render_template("network_blocked.html", items=items, message=message)
        finally:
            db.close()

    @app.route("/network/unblock/<int:contract_id>")
    def network_unblock(contract_id: int):
        db = SessionLocal()
        try:
            unblock_contract(db, contract_id)
        finally:
            db.close()
        return redirect(url_for("network_blocked", msg=f"Contrato {contract_id} desbloqueado"))

    @app.route("/network/tech-history/<int:contract_id>", methods=["GET", "POST"])
    def network_tech_history(contract_id: int):
        db = SessionLocal()
        
        if request.method == "POST":
            try:
                technician = request.form.get("technician")
                action = request.form.get("action")
                description = request.form.get("description")
                
                history = ContractTechHistory(
                    contract_id=contract_id,
                    technician=technician,
                    action=action,
                    description=description,
                    occurred_at=datetime.utcnow()
                )
                db.add(history)
                db.commit()
                flash("Histórico registrado com sucesso!", "success")
            except Exception as e:
                flash(f"Erro ao registrar histórico: {str(e)}", "error")

        history_list = (
            db.query(ContractTechHistory)
            .filter(ContractTechHistory.contract_id == contract_id)
            .order_by(ContractTechHistory.occurred_at.desc())
            .limit(100)
            .all()
        )
        items = []
        for h in history_list:
            items.append({
                "id": h.id,
                "contract_id": h.contract_id,
                "technician": h.technician,
                "action": h.action,
                "description": h.description,
                "occurred_at": h.occurred_at.isoformat() if h.occurred_at else None
            })
        try:
            return render_template("network_tech_history.html", items=items, contract_id=contract_id)
        finally:
            db.close()

    # ==========================================
    # USERS MANAGEMENT
    # ==========================================
    @app.route("/admin/users", methods=["GET", "POST"])
    def admin_users():
        db = SessionLocal()
        try:
            if request.method == "POST":
                user_id = request.form.get("id")
                username = request.form.get("username")
                email = request.form.get("email")
                password = request.form.get("password")
                is_active = request.form.get("is_active") == "on"
                role_ids = request.form.getlist("roles")
                
                if user_id:
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        user.username = username
                        user.email = email
                        user.is_active = is_active
                        if password:
                            user.hashed_password = hash_password(password)
                        
                        # Update roles
                        user.roles = []
                        if role_ids:
                            roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
                            user.roles = roles
                        
                        db.commit()
                        flash("Usuário atualizado com sucesso!", "success")
                else:
                    hashed = hash_password(password) if password else hash_password("123456") # Fallback
                    new_user = User(
                        username=username,
                        email=email,
                        hashed_password=hashed,
                        is_active=is_active
                    )
                    if role_ids:
                        roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
                        new_user.roles = roles
                    
                    db.add(new_user)
                    db.commit()
                    flash("Usuário criado com sucesso!", "success")
                
                return redirect(url_for("admin_users"))

            # GET
            users = db.query(User).all()
            roles = db.query(Role).all()
            return render_template("admin_users.html", items=users, roles=roles)
        except Exception as e:
            db.rollback()
            flash(f"Erro: {str(e)}", "error")
            return redirect(url_for("admin_users"))
        finally:
            db.close()

    @app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
    def admin_users_delete(user_id: int):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                db.delete(user)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Usuário não encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    # ==========================================
    # ROLES MANAGEMENT
    # ==========================================
    @app.route("/admin/groups", methods=["GET", "POST"])
    @app.route("/admin/roles", methods=["GET", "POST"])
    def admin_roles():
        db = SessionLocal()
        try:
            if request.method == "POST":
                role_id = request.form.get("id")
                name = request.form.get("name")
                perm_ids = request.form.getlist("permissions")
                
                if role_id:
                    role = db.query(Role).filter(Role.id == role_id).first()
                    if role:
                        role.name = name
                        # Update permissions
                        role.permissions = []
                        if perm_ids:
                            perms = db.query(Permission).filter(Permission.id.in_(perm_ids)).all()
                            role.permissions = perms
                        db.commit()
                        flash("Função atualizada com sucesso!", "success")
                else:
                    new_role = Role(name=name)
                    if perm_ids:
                        perms = db.query(Permission).filter(Permission.id.in_(perm_ids)).all()
                        new_role.permissions = perms
                    db.add(new_role)
                    db.commit()
                    flash("Função criada com sucesso!", "success")
                
                return redirect(url_for("admin_roles"))

            # GET
            roles = db.query(Role).all()
            permissions = db.query(Permission).all()
            return render_template("admin_roles.html", items=roles, permissions=permissions)
        except Exception as e:
            db.rollback()
            flash(f"Erro: {str(e)}", "error")
            return redirect(url_for("admin_roles"))
        finally:
            db.close()

    @app.route("/admin/roles/<int:role_id>/delete", methods=["POST"])
    def admin_roles_delete(role_id: int):
        db = SessionLocal()
        try:
            role = db.query(Role).filter(Role.id == role_id).first()
            if role:
                db.delete(role)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Função não encontrada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    # ==========================================
    # PERMISSIONS MANAGEMENT
    # ==========================================
    @app.route("/admin/permissions", methods=["GET", "POST"])
    def admin_permissions():
        db = SessionLocal()
        try:
            if request.method == "POST":
                perm_id = request.form.get("id")
                code = request.form.get("code")
                description = request.form.get("description")
                
                if perm_id:
                    perm = db.query(Permission).filter(Permission.id == perm_id).first()
                    if perm:
                        perm.code = code
                        perm.description = description
                        db.commit()
                        flash("Permissão atualizada com sucesso!", "success")
                else:
                    new_perm = Permission(code=code, description=description)
                    db.add(new_perm)
                    db.commit()
                    flash("Permissão criada com sucesso!", "success")
                
                return redirect(url_for("admin_permissions"))

            # GET
            permissions = db.query(Permission).all()
            return render_template("admin_permissions.html", items=permissions)
        except Exception as e:
            db.rollback()
            flash(f"Erro: {str(e)}", "error")
            return redirect(url_for("admin_permissions"))
        finally:
            db.close()

    @app.route("/admin/permissions/<int:permission_id>/delete", methods=["POST"])
    def admin_permissions_delete(permission_id: int):
        db = SessionLocal()
        try:
            perm = db.query(Permission).filter(Permission.id == permission_id).first()
            if perm:
                db.delete(perm)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Permissão não encontrada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    # ==========================================
    # CLIENTS MANAGEMENT
    # ==========================================
    @app.route("/admin/clients", methods=["GET", "POST"])
    def admin_clients():
        db = SessionLocal()
        try:
            if request.method == "POST":
                client_id = request.form.get("id")
                person_type = request.form.get("person_type")
                name = request.form.get("name")
                document = request.form.get("document")
                email = request.form.get("email")
                phone = request.form.get("phone")
                is_active = request.form.get("is_active") == "on"
                
                # Address fields
                zipcode = request.form.get("zipcode")
                city = request.form.get("city")
                state = request.form.get("state")
                street = request.form.get("street")
                number = request.form.get("number")
                neighborhood = request.form.get("neighborhood")

                if client_id:
                    client = db.query(Client).filter(Client.id == client_id).first()
                    if client:
                        client.person_type = person_type
                        client.name = name
                        client.document = document
                        client.email = email
                        client.phone = phone
                        client.is_active = is_active
                        
                        # Update primary address or create new
                        address = db.query(ClientAddress).filter(ClientAddress.client_id == client.id, ClientAddress.is_primary == True).first()
                        if not address:
                            # Try to find any address if primary not set
                            address = db.query(ClientAddress).filter(ClientAddress.client_id == client.id).first()
                        
                        if address:
                            address.zipcode = zipcode
                            address.city = city
                            address.state = state
                            address.street = street
                            address.number = number
                            address.neighborhood = neighborhood
                            address.is_primary = True
                        else:
                            new_addr = ClientAddress(
                                client_id=client.id,
                                zipcode=zipcode,
                                city=city,
                                state=state,
                                street=street,
                                number=number,
                                neighborhood=neighborhood,
                                is_primary=True
                            )
                            db.add(new_addr)

                        db.commit()
                        flash("Cliente atualizado com sucesso!", "success")
                else:
                    new_client = Client(
                        person_type=person_type,
                        name=name,
                        document=document,
                        email=email,
                        phone=phone,
                        is_active=is_active
                    )
                    db.add(new_client)
                    db.flush() # Get ID
                    
                    new_addr = ClientAddress(
                        client_id=new_client.id,
                        zipcode=zipcode,
                        city=city,
                        state=state,
                        street=street,
                        number=number,
                        neighborhood=neighborhood,
                        is_primary=True
                    )
                    db.add(new_addr)
                    
                    db.commit()
                    flash("Cliente criado com sucesso!", "success")
                
                return redirect(url_for("admin_clients"))

            # GET
            # Eager load addresses would be better but for simplicity relying on lazy load in template loop (careful with N+1)
            # Actually, let's join or options(joinedload) if we imported it. 
            # For now, standard query is fine for admin panel scale.
            clients = db.query(Client).all()
            return render_template("admin_clients.html", items=clients)
        except Exception as e:
            db.rollback()
            flash(f"Erro: {str(e)}", "error")
            return redirect(url_for("admin_clients"))
        finally:
            db.close()

    @app.route("/admin/clients/<int:client_id>/delete", methods=["POST"])
    def admin_clients_delete(client_id: int):
        db = SessionLocal()
        try:
            client = db.query(Client).filter(Client.id == client_id).first()
            if client:
                db.delete(client)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Cliente não encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    # ==========================================
    # PLANS MANAGEMENT
    # ==========================================
    @app.route("/admin/plans", methods=["GET", "POST"])
    def admin_plans():
        db = SessionLocal()
        try:
            if request.method == "POST":
                plan_id = request.form.get("id")
                name = request.form.get("name")
                category = request.form.get("category")
                price = float(request.form.get("price") or 0)
                download = float(request.form.get("download_speed_mbps") or 0)
                upload = float(request.form.get("upload_speed_mbps") or 0)
                description = request.form.get("description")
                is_active = request.form.get("is_active") == "on"
                
                burst_enabled = request.form.get("burst_enabled") == "on"
                burst_rate = float(request.form.get("burst_rate_percent") or 0)
                burst_time = int(request.form.get("burst_threshold_seconds") or 0)
                
                if plan_id:
                    plan = db.query(Plan).filter(Plan.id == plan_id).first()
                    if plan:
                        plan.name = name
                        plan.category = category
                        plan.price = price
                        plan.download_speed_mbps = download
                        plan.upload_speed_mbps = upload
                        plan.description = description
                        plan.is_active = is_active
                        plan.burst_enabled = burst_enabled
                        plan.burst_rate_percent = burst_rate
                        plan.burst_threshold_seconds = burst_time
                        db.commit()
                        flash("Plano atualizado com sucesso!", "success")
                else:
                    new_plan = Plan(
                        name=name,
                        category=category,
                        price=price,
                        download_speed_mbps=download,
                        upload_speed_mbps=upload,
                        description=description,
                        is_active=is_active,
                        burst_enabled=burst_enabled,
                        burst_rate_percent=burst_rate,
                        burst_threshold_seconds=burst_time
                    )
                    db.add(new_plan)
                    db.commit()
                    flash("Plano criado com sucesso!", "success")
                
                return redirect(url_for("admin_plans"))

            # GET
            plans = db.query(Plan).all()
            return render_template("admin_plans.html", items=plans)
        except Exception as e:
            db.rollback()
            flash(f"Erro: {str(e)}", "error")
            return redirect(url_for("admin_plans"))
        finally:
            db.close()

    @app.route("/admin/plans/<int:plan_id>/delete", methods=["POST"])
    def admin_plans_delete(plan_id: int):
        db = SessionLocal()
        try:
            plan = db.query(Plan).filter(Plan.id == plan_id).first()
            if plan:
                db.delete(plan)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Plano não encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    # ==========================================
    # CONTRACTS MANAGEMENT
    # ==========================================
    @app.route("/admin/contracts", methods=["GET", "POST"])
    def admin_contracts():
        db = SessionLocal()
        try:
            if request.method == "POST":
                contract_id = request.form.get("id")
                client_id = request.form.get("client_id")
                plan_id = request.form.get("plan_id")
                status = request.form.get("status")
                start_date_str = request.form.get("start_date")
                billing_day = int(request.form.get("billing_day") or 10)
                installation_address = request.form.get("installation_address")
                price_override_val = request.form.get("price_override")
                suspend_on_arrears = request.form.get("suspend_on_arrears") == "on"
                
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else datetime.utcnow().date()
                price_override = float(price_override_val) if price_override_val else None

                if contract_id:
                    contract = db.query(Contract).filter(Contract.id == contract_id).first()
                    if contract:
                        contract.client_id = client_id
                        contract.plan_id = plan_id
                        contract.status = status
                        contract.start_date = start_date
                        contract.billing_day = billing_day
                        contract.installation_address = installation_address
                        contract.price_override = price_override
                        contract.suspend_on_arrears = suspend_on_arrears
                        db.commit()
                        flash("Contrato atualizado com sucesso!", "success")
                else:
                    new_contract = Contract(
                        client_id=client_id,
                        plan_id=plan_id,
                        status=status,
                        start_date=start_date,
                        billing_day=billing_day,
                        installation_address=installation_address,
                        price_override=price_override,
                        suspend_on_arrears=suspend_on_arrears
                    )
                    db.add(new_contract)
                    db.commit()
                    flash("Contrato criado com sucesso!", "success")
                
                return redirect(url_for("admin_contracts"))

            # GET
            contracts = db.query(Contract).all()
            clients = db.query(Client).filter(Client.is_active == True).all()
            plans = db.query(Plan).filter(Plan.is_active == True).all()
            return render_template("admin_contracts.html", items=contracts, clients=clients, plans=plans)
        except Exception as e:
            db.rollback()
            flash(f"Erro: {str(e)}", "error")
            return redirect(url_for("admin_contracts"))
        finally:
            db.close()

    @app.route("/admin/contracts/<int:contract_id>/delete", methods=["POST"])
    def admin_contracts_delete(contract_id: int):
        db = SessionLocal()
        try:
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            if contract:
                db.delete(contract)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Contrato não encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    # ==========================================
    # SUPPORT / HELPDESK
    # ==========================================
    @app.route("/admin/support/categories", methods=["GET", "POST"])
    def admin_support_categories():
        db = SessionLocal()
        try:
            if request.method == "POST":
                cat_id = request.form.get("id")
                name = request.form.get("name")
                description = request.form.get("description")
                is_active = request.form.get("is_active") == "on"
                
                if cat_id:
                    cat = db.query(TicketCategory).filter(TicketCategory.id == cat_id).first()
                    if cat:
                        cat.name = name
                        cat.description = description
                        cat.is_active = is_active
                        db.commit()
                        flash("Categoria atualizada!", "success")
                else:
                    create_category(db, CategoryCreate(name=name, description=description, is_active=is_active))
                    flash("Categoria criada!", "success")
                
                return redirect(url_for("admin_support_categories"))

            items = get_categories(db, active_only=False)
            return render_template("admin_support_categories.html", items=items)
        except Exception as e:
            db.rollback()
            flash(f"Erro: {str(e)}", "error")
            return redirect(url_for("admin_support_categories"))
        finally:
            db.close()

    @app.route("/admin/support/tickets", methods=["GET", "POST"])
    def admin_support_tickets():
        db = SessionLocal()
        try:
            if request.method == "POST":
                # Create Ticket
                data = TicketCreate(
                    client_id=int(request.form.get("client_id")),
                    category_id=int(request.form.get("category_id")),
                    assignee_id=int(request.form.get("assignee_id")) if request.form.get("assignee_id") else None,
                    subject=request.form.get("subject"),
                    description=request.form.get("description"),
                    priority=request.form.get("priority"),
                    origin="manual"
                )
                create_ticket(db, data)
                flash("Ticket criado com sucesso!", "success")
                return redirect(url_for("admin_support_tickets"))

            # Filters
            query = db.query(Ticket)
            
            # Simple filters
            status = request.args.get("status")
            if status:
                query = query.filter(Ticket.status == status)
            
            priority = request.args.get("priority")
            if priority:
                query = query.filter(Ticket.priority == priority)
                
            protocol = request.args.get("protocol")
            if protocol:
                query = query.filter(Ticket.protocol.ilike(f"%{protocol}%"))

            items = query.order_by(Ticket.created_at.desc()).limit(100).all()
            
            clients = db.query(Client).filter(Client.is_active == True).order_by(Client.name).all()
            categories = get_categories(db)
            users = db.query(User).filter(User.is_active == True).all()
            
            return render_template("admin_support_tickets.html", items=items, clients=clients, categories=categories, users=users)
        finally:
            db.close()

    @app.route("/admin/support/tickets/<int:ticket_id>", methods=["GET"])
    def admin_support_ticket_detail(ticket_id: int):
        db = SessionLocal()
        try:
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if not ticket:
                flash("Ticket não encontrado", "error")
                return redirect(url_for("admin_support_tickets"))
            
            messages = get_ticket_messages(db, ticket_id)
            categories = get_categories(db)
            users = db.query(User).filter(User.is_active == True).all()
            
            return render_template("admin_support_ticket_detail.html", ticket=ticket, messages=messages, categories=categories, users=users)
        finally:
            db.close()

    @app.route("/admin/support/tickets/<int:ticket_id>/update", methods=["POST"])
    def admin_support_ticket_update(ticket_id: int):
        db = SessionLocal()
        try:
            update_data = TicketUpdate(
                status=request.form.get("status"),
                priority=request.form.get("priority"),
                assignee_id=int(request.form.get("assignee_id")) if request.form.get("assignee_id") else None,
                category_id=int(request.form.get("category_id")) if request.form.get("category_id") else None
            )
            update_ticket(db, ticket_id, update_data)
            flash("Ticket atualizado!", "success")
        except Exception as e:
            flash(f"Erro ao atualizar: {str(e)}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_support_ticket_detail", ticket_id=ticket_id))

    @app.route("/admin/support/tickets/<int:ticket_id>/reply", methods=["POST"])
    def admin_support_ticket_reply(ticket_id: int):
        db = SessionLocal()
        try:
            # Current user (mocked for now as we don't have full auth context in session object easily available without query)
            # In production, get user_id from session['user_id']
            username = session.get("user")
            user = db.query(User).filter(User.username == username).first()
            user_id = user.id if user else None

            msg_data = MessageCreate(
                ticket_id=ticket_id,
                user_id=user_id,
                content=request.form.get("content"),
                is_internal=request.form.get("is_internal") == "on"
            )
            add_message(db, msg_data)
            flash("Resposta enviada!", "success")
        except Exception as e:
            flash(f"Erro ao enviar resposta: {str(e)}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_support_ticket_detail", ticket_id=ticket_id))

    @app.route("/admin/support/tickets/<int:ticket_id>/create-os")
    def admin_support_ticket_create_os(ticket_id: int):
        db = SessionLocal()
        try:
            from ..app.modules.service_orders.schemas import ServiceOrderCreate, ServiceOrderItemCreate
            from ..app.modules.service_orders.service import create_order
            
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if ticket:
                # Determine priority based on ticket priority
                priority_map = {"critical": "urgent", "high": "high", "normal": "medium", "low": "low"}
                pr = priority_map.get((ticket.priority or "normal").lower(), "medium")
                
                data = ServiceOrderCreate(
                    client_id=ticket.client_id,
                    ticket_id=ticket.id,
                    type="repair", # Default to repair
                    priority=pr,
                    status="open",
                    notes=f"Gerada do ticket #{ticket.protocol}: {ticket.description}",
                    items=[ServiceOrderItemCreate(description="Verificação técnica", quantity=1)],
                )
                create_order(db, data)
                
                # Update ticket status
                ticket.status = "in_progress"
                db.commit()
                
                flash("Ordem de Serviço gerada com sucesso!", "success")
                return redirect(url_for("admin_service_orders"))
            else:
                flash("Ticket não encontrado", "error")
        except Exception as e:
            flash(f"Erro ao gerar OS: {str(e)}", "error")
        finally:
            db.close()
        return redirect(url_for("admin_support_ticket_detail", ticket_id=ticket_id))

    @app.route("/admin/support/occurrences", methods=["GET", "POST"])
    def admin_support_occurrences():
        db = SessionLocal()
        try:
            if request.method == "POST":
                # Create or Update
                occ_id = request.form.get("occurrence_id")
                
                # Helper to parse dates/ints
                client_id = int(request.form.get("client_id")) if request.form.get("client_id") else None
                contract_id = int(request.form.get("contract_id")) if request.form.get("contract_id") else None
                
                if occ_id:
                    # Update
                    occ = db.query(Occurrence).filter(Occurrence.id == occ_id).first()
                    if occ:
                        data = OccurrenceUpdate(
                            category=request.form.get("category"),
                            severity=request.form.get("severity"),
                            description=request.form.get("description"),
                            status=request.form.get("status")
                        )
                        update_occurrence(db, occ, data)
                        flash(f"Ocorrência #{occ_id} atualizada!", "success")
                else:
                    # Create
                    data = OccurrenceCreate(
                        client_id=client_id,
                        contract_id=contract_id,
                        category=request.form.get("category"),
                        severity=request.form.get("severity"),
                        description=request.form.get("description")
                    )
                    create_occurrence(db, data)
                    flash("Ocorrência criada com sucesso!", "success")
                
                return redirect(url_for("admin_support_occurrences"))

            # GET - List with filters
            query = db.query(Occurrence)
            
            status = request.args.get("status")
            if status:
                query = query.filter(Occurrence.status == status)
                
            client_id = request.args.get("client_id")
            if client_id:
                query = query.filter(Occurrence.client_id == client_id)

            items = query.order_by(Occurrence.created_at.desc()).limit(100).all()
            return render_template("admin_support_occurrences.html", items=items)
        except Exception as e:
            db.rollback()
            flash(f"Erro: {str(e)}", "error")
            return redirect(url_for("admin_support_occurrences"))
        finally:
            db.close()

    @app.route("/admin/support/occurrences/delete/<int:occ_id>", methods=["POST"])
    def admin_support_occurrences_delete(occ_id: int):
        db = SessionLocal()
        try:
            occ = db.query(Occurrence).filter(Occurrence.id == occ_id).first()
            if occ:
                db.delete(occ)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Ocorrência não encontrada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    # ==========================================
    # SERVICE ORDERS
    # ==========================================
    @app.route("/admin/service-orders", methods=["GET", "POST"])
    def admin_service_orders():
        db = SessionLocal()
        try:
            if request.method == "POST":
                # Create Service Order
                so_id = request.form.get("service_order_id")
                
                client_id = int(request.form.get("client_id")) if request.form.get("client_id") else None
                contract_id = int(request.form.get("contract_id")) if request.form.get("contract_id") else None
                ticket_id = int(request.form.get("ticket_id")) if request.form.get("ticket_id") else None
                
                so_type = request.form.get("type")
                priority = request.form.get("priority")
                status = request.form.get("status") or "open"
                notes = request.form.get("notes")
                technician_name = request.form.get("technician_name")
                scheduled_at_str = request.form.get("scheduled_at")
                
                scheduled_at = None
                if scheduled_at_str:
                    try:
                        scheduled_at = datetime.strptime(scheduled_at_str, "%Y-%m-%dT%H:%M")
                    except ValueError:
                        pass

                if so_id:
                    # Update
                    so = db.query(ServiceOrder).filter(ServiceOrder.id == so_id).first()
                    if so:
                        so.client_id = client_id
                        so.contract_id = contract_id
                        so.ticket_id = ticket_id
                        so.type = so_type
                        so.priority = priority
                        so.status = status
                        so.notes = notes
                        so.technician_name = technician_name
                        so.scheduled_at = scheduled_at
                        
                        if status == "completed" and not so.executed_at:
                            so.executed_at = datetime.utcnow()
                            
                        db.commit()
                        flash(f"Ordem de Serviço #{so_id} atualizada!", "success")
                else:
                    # Create
                    new_so = ServiceOrder(
                        client_id=client_id,
                        contract_id=contract_id,
                        ticket_id=ticket_id,
                        type=so_type,
                        priority=priority,
                        status=status,
                        notes=notes,
                        technician_name=technician_name,
                        scheduled_at=scheduled_at
                    )
                    db.add(new_so)
                    db.commit()
                    flash("Ordem de Serviço criada com sucesso!", "success")
                
                return redirect(url_for("admin_service_orders"))

            # GET List
            query = db.query(ServiceOrder)
            
            status = request.args.get("status")
            if status:
                query = query.filter(ServiceOrder.status == status)
                
            priority = request.args.get("priority")
            if priority:
                query = query.filter(ServiceOrder.priority == priority)
                
            type_ = request.args.get("type")
            if type_:
                query = query.filter(ServiceOrder.type == type_)
                
            technician = request.args.get("technician")
            if technician:
                query = query.filter(ServiceOrder.technician_name.ilike(f"%{technician}%"))

            items = query.order_by(ServiceOrder.created_at.desc()).limit(100).all()
            
            # Helper data for modal
            clients = db.query(Client).filter(Client.is_active == True).order_by(Client.name).limit(200).all()
            users = db.query(User).filter(User.is_active == True).all() # For technicians
            
            return render_template("admin_service_orders.html", items=items, clients=clients, users=users)
        except Exception as e:
            db.rollback()
            flash(f"Erro: {str(e)}", "error")
            return redirect(url_for("admin_service_orders"))
        finally:
            db.close()

    @app.route("/admin/service-orders/<int:so_id>/delete", methods=["POST"])
    def admin_service_orders_delete(so_id: int):
        db = SessionLocal()
        try:
            so = db.query(ServiceOrder).filter(ServiceOrder.id == so_id).first()
            if so:
                db.delete(so)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Ordem de Serviço não encontrada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    # ==========================================
    # COMMUNICATION
    # ==========================================


    @app.route("/communication/queue/<int:msg_id>/dispatch", methods=["POST"])
    def communication_dispatch(msg_id: int):
        db = SessionLocal()
        try:
            msg = db.query(MessageQueue).filter(MessageQueue.id == msg_id).first()
            if msg:
                dispatch_message(db, msg)
                return {"success": True}
            return {"success": False, "error": "Mensagem não encontrada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @app.route("/communication/queue/<int:msg_id>/delete", methods=["POST"])
    def communication_delete(msg_id: int):
        db = SessionLocal()
        try:
            msg = db.query(MessageQueue).filter(MessageQueue.id == msg_id).first()
            if msg:
                db.delete(msg)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Mensagem não encontrada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()








    # ==========================================
    # CUSTOMER PORTAL
    # ==========================================
    from ..app.modules.customer_app.service import authenticate_client, compute_profile, list_titles, list_contracts, open_ticket
    from ..app.modules.customer_app.schemas import TicketCreate
    from ..app.modules.clients.models import Client
    from ..app.modules.support.models import Ticket

    @app.route("/portal/login", methods=["GET", "POST"])
    def portal_login():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            
            db = SessionLocal()
            try:
                client = authenticate_client(db, email, password)
                if client:
                    session["client_id"] = client.id
                    session["client_name"] = client.name
                    return redirect("/portal/dashboard")
                else:
                    flash("Credenciais inválidas", "danger")
            finally:
                db.close()
                
        return render_template("portal/login.html")

    @app.route("/portal/logout")
    def portal_logout():
        session.pop("client_id", None)
        session.pop("client_name", None)
        return redirect("/portal/login")

    @app.route("/portal/dashboard")
    def portal_dashboard():
        if "client_id" not in session:
            return redirect("/portal/login")
            
        db = SessionLocal()
        try:
            client = db.query(Client).get(session["client_id"])
            profile = compute_profile(db, client)
            return render_template("portal/dashboard.html", client=client, profile=profile)
        finally:
            db.close()

    @app.route("/portal/invoices")
    def portal_invoices():
        if "client_id" not in session:
            return redirect("/portal/login")
            
        db = SessionLocal()
        try:
            titles = list_titles(db, session["client_id"])
            return render_template("portal/invoices.html", titles=titles)
        finally:
            db.close()
            
    @app.route("/portal/contracts")
    def portal_contracts():
        if "client_id" not in session:
            return redirect("/portal/login")
            
        db = SessionLocal()
        try:
            contracts = list_contracts(db, session["client_id"])
            return render_template("portal/contracts.html", contracts=contracts)
        finally:
            db.close()

    @app.route("/portal/support", methods=["GET"])
    def portal_support():
        if "client_id" not in session:
            return redirect("/portal/login")
            
        db = SessionLocal()
        try:
            tickets = db.query(Ticket).filter(Ticket.client_id == session["client_id"]).order_by(Ticket.created_at.desc()).all()
            contracts = list_contracts(db, session["client_id"])
            return render_template("portal/support.html", tickets=tickets, contracts=contracts)
        finally:
            db.close()

    @app.route("/portal/support/create", methods=["POST"])
    def portal_support_create():
        if "client_id" not in session:
            return redirect("/portal/login")
            
        db = SessionLocal()
        try:
            data = TicketCreate(
                subject=request.form.get("subject"),
                category=request.form.get("category"),
                priority="medium", # Default for client
                contract_id=int(request.form.get("contract_id")) if request.form.get("contract_id") else None,
                description=request.form.get("subject") # Using subject as description for simplicity or add field
            )
            open_ticket(db, session["client_id"], data)
            flash("Chamado aberto com sucesso!", "success")
            return redirect("/portal/support")
        except Exception as e:
            flash(f"Erro ao abrir chamado: {str(e)}", "danger")
            return redirect("/portal/support")
        finally:
            db.close()

    # ==========================================
    # TECHNICIAN APP
    # ==========================================
    from ..app.modules.technician_app.service import get_profile_by_user, list_assigned_orders, start_order, complete_order
    from ..app.modules.technician_app.models import TechnicianProfile

    # ==========================================
    # STOCK MANAGEMENT
    # ==========================================
    @app.route("/admin/stock/dashboard")
    def admin_stock_dashboard():
        db = SessionLocal()
        try:
            total_items = db.query(StockItem).count()
            total_warehouses = db.query(Warehouse).count()
            
            # Calculate balances
            balances_q = db.query(
                StockMovement.item_id,
                func.sum(case((StockMovement.type == "in", StockMovement.quantity), else_=0.0)).label("in_qty"),
                func.sum(case((StockMovement.type == "out", StockMovement.quantity), else_=0.0)).label("out_qty")
            ).group_by(StockMovement.item_id).all()
            
            item_balances = {
                item_id: float(in_qty or 0) - float(out_qty or 0) 
                for item_id, in_qty, out_qty in balances_q
            }
            
            items = db.query(StockItem).filter(StockItem.is_active == True).all()
            low_stock_items = []
            low_stock_count = 0
            total_value_est = 0.0
            
            for item in items:
                qty = item_balances.get(item.id, 0.0)
                item.current_qty = qty  # Attach for template
                
                if qty <= item.min_qty:
                    low_stock_count += 1
                    low_stock_items.append(item)
                
                # Estimate value using last purchase price
                last_in = db.query(StockMovement).filter(
                    StockMovement.item_id == item.id, 
                    StockMovement.type == 'in'
                ).order_by(StockMovement.created_at.desc()).first()
                
                cost = last_in.unit_cost if last_in and last_in.unit_cost else 0.0
                total_value_est += qty * cost

            data = {
                "total_items": total_items,
                "total_warehouses": total_warehouses,
                "low_stock_count": low_stock_count,
                "total_value": total_value_est,
                "low_stock_items": low_stock_items
            }

            recent_movements = db.query(StockMovement).order_by(StockMovement.created_at.desc()).limit(10).all()
            
            return render_template("admin_stock_dashboard.html", 
                                 data=data,
                                 recent_movements=recent_movements)
        finally:
            db.close()

    @app.route("/admin/stock/items", methods=["GET", "POST"])
    def admin_stock_items():
        db = SessionLocal()
        try:
            if request.method == "POST":
                item_id = request.form.get("id")
                name = request.form.get("name")
                code = request.form.get("code")
                unit = request.form.get("unit")
                min_qty = float(request.form.get("min_qty") or 0)
                is_active = request.form.get("is_active") == "on"

                if item_id:
                    item = db.query(StockItem).filter(StockItem.id == item_id).first()
                    if item:
                        item.name = name
                        item.code = code
                        item.unit = unit
                        item.min_qty = min_qty
                        item.is_active = is_active
                        db.commit()
                        flash("Item atualizado com sucesso!", "success")
                else:
                    new_item = StockItem(
                        name=name,
                        code=code,
                        unit=unit,
                        min_qty=min_qty,
                        is_active=is_active
                    )
                    db.add(new_item)
                    db.commit()
                    flash("Item criado com sucesso!", "success")
                
                return redirect(url_for("admin_stock_items"))

            items = db.query(StockItem).all()
            return render_template("admin_stock_items.html", items=items)
        finally:
            db.close()

    @app.route("/admin/stock/items/<int:item_id>/delete", methods=["POST"])
    def admin_stock_items_delete(item_id: int):
        db = SessionLocal()
        try:
            item = db.query(StockItem).filter(StockItem.id == item_id).first()
            if item:
                db.delete(item)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Item não encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @app.route("/admin/stock/warehouses", methods=["GET", "POST"])
    def admin_stock_warehouses():
        db = SessionLocal()
        try:
            if request.method == "POST":
                wh_id = request.form.get("id")
                name = request.form.get("name")
                code = request.form.get("code")
                address = request.form.get("address")
                is_active = request.form.get("is_active") == "on"

                if wh_id:
                    wh = db.query(Warehouse).filter(Warehouse.id == wh_id).first()
                    if wh:
                        wh.name = name
                        wh.code = code
                        wh.address = address
                        wh.is_active = is_active
                        db.commit()
                        flash("Almoxarifado atualizado com sucesso!", "success")
                else:
                    new_wh = Warehouse(
                        name=name,
                        code=code,
                        address=address,
                        is_active=is_active
                    )
                    db.add(new_wh)
                    db.commit()
                    flash("Almoxarifado criado com sucesso!", "success")
                
                return redirect(url_for("admin_stock_warehouses"))

            warehouses = db.query(Warehouse).all()
            return render_template("admin_stock_warehouses.html", warehouses=warehouses)
        finally:
            db.close()

    @app.route("/admin/stock/warehouses/<int:wh_id>/delete", methods=["POST"])
    def admin_stock_warehouses_delete(wh_id: int):
        db = SessionLocal()
        try:
            wh = db.query(Warehouse).filter(Warehouse.id == wh_id).first()
            if wh:
                db.delete(wh)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Almoxarifado não encontrado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @app.route("/admin/stock/movements", methods=["GET", "POST"])
    def admin_stock_movements():
        db = SessionLocal()
        try:
            if request.method == "POST":
                item_id = int(request.form.get("item_id"))
                warehouse_id = int(request.form.get("warehouse_id"))
                type_ = request.form.get("type") # in, out
                quantity = float(request.form.get("quantity"))
                unit_cost = float(request.form.get("unit_cost") or 0)
                note = request.form.get("note")

                movement = StockMovement(
                    item_id=item_id,
                    warehouse_id=warehouse_id,
                    type=type_,
                    quantity=quantity,
                    unit_cost=unit_cost,
                    total_value=quantity * unit_cost,
                    note=note
                )
                db.add(movement)
                db.commit()
                flash("Movimento registrado com sucesso!", "success")
                return redirect(url_for("admin_stock_movements"))

            movements = db.query(StockMovement).order_by(StockMovement.created_at.desc()).limit(100).all()
            items = db.query(StockItem).filter(StockItem.is_active == True).all()
            warehouses = db.query(Warehouse).filter(Warehouse.is_active == True).all()
            
            return render_template("admin_stock_movements.html", 
                                 movements=movements,
                                 items=items,
                                 warehouses=warehouses)
        finally:
            db.close()

    @app.route("/admin/communication/queue")
    def admin_communication_queue():
        db = SessionLocal()
        try:
            items = db.query(MessageQueue).filter(MessageQueue.status == "queued").order_by(MessageQueue.created_at.desc()).all()
            return render_template("admin_communication_queue.html", items=items)
        finally:
            db.close()

    @app.route("/admin/communication/queue/requeue", methods=["POST"])
    def admin_communication_requeue():
        db = SessionLocal()
        try:
            data = request.json
            msg_ids = data.get("ids", [])
            if not msg_ids:
                return {"success": False, "error": "Nenhuma mensagem selecionada"}
            
            for mid in msg_ids:
                try:
                    requeue_failed(db, int(mid))
                except:
                    pass
            
            return {"success": True}
        finally:
            db.close()

    @app.route("/admin/communication/queue/dispatch", methods=["POST"])
    def admin_communication_dispatch():
        db = SessionLocal()
        try:
            data = request.json
            msg_ids = data.get("ids", [])
            if not msg_ids:
                # Single dispatch via ID in URL? The template uses onclick="dispatchMessage(${row.id})"
                # which probably calls an API. Let's support both single and bulk.
                # If body has ids array, it's bulk.
                # If URL param... wait, the template JS likely does POST to specific URL or this one.
                # Let's assume the JS function sends {ids: [id]}.
                return {"success": False, "error": "Nenhuma mensagem selecionada"}
            
            for mid in msg_ids:
                msg = db.query(MessageQueue).filter(MessageQueue.id == mid).first()
                if msg:
                    dispatch_message(db, msg)
            
            return {"success": True}
        finally:
            db.close()

    @app.route("/admin/communication/queue/<int:msg_id>/delete", methods=["POST"])
    def admin_communication_delete(msg_id: int):
        db = SessionLocal()
        try:
            msg = db.query(MessageQueue).filter(MessageQueue.id == msg_id).first()
            if msg:
                db.delete(msg)
                db.commit()
                return {"success": True}
            return {"success": False, "error": "Mensagem não encontrada"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @app.route("/admin/communication/history")
    def admin_communication_history():
        db = SessionLocal()
        try:
            items = db.query(MessageQueue).filter(MessageQueue.status.in_(["sent", "failed"])).order_by(MessageQueue.created_at.desc()).limit(100).all()
            return render_template("admin_communication_history.html", items=items)
        finally:
            db.close()

    # ==========================================
    # REPORTS MANAGEMENT
    # ==========================================
    @app.route("/admin/reports/financial")
    def admin_reports_financial():
        db = SessionLocal()
        try:
            from sqlalchemy import func
            from datetime import datetime, timedelta

            today = datetime.now().date()
            first_day = today.replace(day=1)
            next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)

            # Revenue Estimated (Due this month)
            revenue_estimated = db.query(func.sum(Title.amount)).filter(
                Title.due_date >= first_day,
                Title.due_date < next_month,
                Title.status != 'canceled'
            ).scalar() or 0.0

            # Amount Overdue (Total overdue)
            amount_overdue = db.query(func.sum(Title.amount)).filter(
                Title.status == 'overdue'
            ).scalar() or 0.0

            # Titles Open
            titles_open = db.query(func.count(Title.id)).filter(
                Title.status == 'open'
            ).scalar() or 0

            # Delinquency Rate (Amount Overdue / Total Billed last 12 months roughly, or just simple ratio)
            # Let's do a simple ratio of Overdue / (Overdue + Paid)
            total_billed = db.query(func.sum(Title.amount)).filter(
                Title.status.in_(['paid', 'overdue'])
            ).scalar() or 1.0 # avoid div by zero
            
            delinquency_rate = (amount_overdue / total_billed) * 100 if total_billed > 0 else 0.0

            # By Status
            by_status_query = db.query(
                Title.status,
                func.count(Title.id).label('count'),
                func.sum(Title.amount).label('amount')
            ).group_by(Title.status).all()

            by_status = []
            for s, c, a in by_status_query:
                by_status.append({
                    "status": s,
                    "count": c,
                    "amount": a or 0.0
                })

            data = {
                "revenue_estimated": revenue_estimated,
                "amount_overdue": amount_overdue,
                "titles_open": titles_open,
                "delinquency_rate": delinquency_rate,
                "by_status": by_status
            }

            return render_template("admin_reports_financial.html", data=data)
        finally:
            db.close()

    @app.route("/admin/reports/network")
    def admin_reports_network():
        db = SessionLocal()
        try:
            from sqlalchemy import func
            
            # Contracts Active
            contracts_active = db.query(func.count(Contract.id)).filter(Contract.status == 'active').scalar() or 0
            
            # Contracts Blocked
            contracts_blocked = db.query(func.count(Contract.id)).filter(Contract.status == 'blocked').scalar() or 0
            
            # NAS Count (Routers/Concentrators)
            nas_count = db.query(func.count(NetworkDevice.id)).filter(NetworkDevice.type.in_(['router', 'bras'])).scalar() or 0
            
            # OLTs Online (Assuming type='olt')
            olts_online = db.query(func.count(NetworkDevice.id)).filter(NetworkDevice.type == 'olt').scalar() or 0
            
            # SICI Accesses (Total active contracts)
            sici_accesses = contracts_active
            
            # SICI Avg Speed (Avg download speed of active contracts)
            sici_avg_speed = db.query(func.avg(Plan.download_speed_mbps)).join(Contract, Contract.plan_id == Plan.id).filter(Contract.status == 'active').scalar() or 0.0
            
            data = {
                "contracts_active": contracts_active,
                "contracts_blocked": contracts_blocked,
                "nas_count": nas_count,
                "olts_online": olts_online,
                "sici_accesses": sici_accesses,
                "sici_avg_speed": round(sici_avg_speed, 2)
            }
            
            return render_template("admin_reports_network.html", data=data)
        finally:
            db.close()

    @app.route("/admin/reports/growth")
    def admin_reports_growth():
        db = SessionLocal()
        try:
            from sqlalchemy import func
            from datetime import datetime, timedelta
            
            today = datetime.now()
            last_30d = today - timedelta(days=30)
            
            # New Contracts 30d
            new_contracts_30d = db.query(func.count(Contract.id)).filter(Contract.created_at >= last_30d).scalar() or 0
            
            # Canceled Contracts 30d
            canceled_contracts_30d = db.query(func.count(Contract.id)).filter(
                Contract.status == 'canceled',
                Contract.updated_at >= last_30d
            ).scalar() or 0
            
            # Total Clients
            total_clients = db.query(func.count(Client.id)).scalar() or 0
            
            # Churn Rate
            churn_rate = (canceled_contracts_30d / total_clients) * 100 if total_clients > 0 else 0.0
            
            data = {
                "new_contracts_30d": new_contracts_30d,
                "canceled_contracts_30d": canceled_contracts_30d,
                "churn_rate": churn_rate,
                "total_clients": total_clients
            }
            
            return render_template("admin_reports_growth.html", data=data)
        finally:
            db.close()

    @app.route("/admin/network/olt_status")
    def admin_olt_status():
        db = SessionLocal()
        try:
            # Get OLT devices for filter
            devices = db.query(NetworkDevice).filter(NetworkDevice.type == 'olt').all()
            
            # Get Items (Simulated for now based on Assignments)
            assignments = db.query(
                ContractNetworkAssignment, 
                NetworkDevice.name.label('device_name'), 
                NetworkDevice.vendor
            ).join(NetworkDevice, ContractNetworkAssignment.device_id == NetworkDevice.id)\
             .filter(NetworkDevice.type == 'olt').limit(100).all()
            
            import random
            
            items = []
            for assign, dev_name, dev_vendor in assignments:
                # Simulate live data
                is_online = random.choice([True, True, True, False])
                items.append({
                    "contract_id": assign.contract_id,
                    "device_name": dev_name,
                    "vendor": dev_vendor,
                    "onu_id": f"ONU-{assign.id}", 
                    "online": is_online,
                    "rx_power_dbm": round(random.uniform(-25.0, -15.0), 2) if is_online else 0.0,
                    "tx_power_dbm": round(random.uniform(2.0, 5.0), 2) if is_online else 0.0,
                    "uptime_seconds": random.randint(3600, 864000) if is_online else 0
                })
            
            return render_template("admin_olt_status.html", items=items, devices=devices)
        finally:
            db.close()

    @app.route("/tech/login", methods=["GET", "POST"])
    def tech_login():
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            
            db = SessionLocal()
            try:
                user = authenticate_user(db, username, password)
                if user and user.is_active:
                    # Check if user has technician profile or role?
                    # For now just allow any user, but ideally check permissions
                    session["tech_user_id"] = user.id
                    session["tech_username"] = user.username
                    return redirect("/tech/dashboard")
                else:
                    flash("Credenciais inválidas", "danger")
            finally:
                db.close()
                
        return render_template("tech/login.html")

    @app.route("/tech/logout")
    def tech_logout():
        session.pop("tech_user_id", None)
        session.pop("tech_username", None)
        return redirect("/tech/login")

    @app.route("/tech/dashboard")
    def tech_dashboard():
        if "tech_user_id" not in session:
            return redirect("/tech/login")
            
        db = SessionLocal()
        try:
            orders = list_assigned_orders(db, session["tech_username"])
            # Eager load contract and client for template
            # list_assigned_orders returns ServiceOrder objects. 
            # If lazy loading is enabled, it might fail if session closed? 
            # But here we are inside session scope.
            # However, Jinja access happens after route returns? No, render_template renders immediately.
            # But relationships might trigger queries.
            # To be safe, we might need to join/eager load in service or access them here.
            # Let's trust render_template does it while session is open.
            
            return render_template("tech/dashboard.html", orders=orders)
        finally:
            db.close()

    @app.route("/tech/order/<int:order_id>")
    def tech_order_detail(order_id: int):
        if "tech_user_id" not in session:
            return redirect("/tech/login")
            
        db = SessionLocal()
        try:
            order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
            if not order:
                return "Ordem não encontrada", 404
            return render_template("tech/order_detail.html", order=order)
        finally:
            db.close()

    @app.route("/tech/order/<int:order_id>/start", methods=["POST"])
    def tech_order_start(order_id: int):
        if "tech_user_id" not in session:
            return redirect("/tech/login")
            
        db = SessionLocal()
        try:
            order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
            if order:
                start_order(db, order, session["tech_username"])
                flash("Ordem iniciada!", "success")
            return redirect(f"/tech/order/{order_id}")
        finally:
            db.close()

    @app.route("/tech/order/<int:order_id>/complete", methods=["POST"])
    def tech_order_complete(order_id: int):
        if "tech_user_id" not in session:
            return redirect("/tech/login")
            
        db = SessionLocal()
        try:
            order = db.query(ServiceOrder).filter(ServiceOrder.id == order_id).first()
            if order:
                notes = request.form.get("notes")
                complete_order(db, order, notes)
                flash("Ordem concluída!", "success")
            return redirect("/tech/dashboard")
        finally:
            db.close()

    return app


app = create_app()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
