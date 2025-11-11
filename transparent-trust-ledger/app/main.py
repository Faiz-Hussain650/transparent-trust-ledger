from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from .database import Base, engine
from .routers import trusts, bills, public, payments
from .deps import get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Transparent Trust Ledger")

# CORS (you can tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# Template directory
templates = Jinja2Templates(directory="app/templates")

# Serve static files (optional CSS/images)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(trusts.router)
app.include_router(bills.router)
app.include_router(payments.router)
app.include_router(public.router)

# Simple web routes
@app.get("/")
def home(request: Request, db=next(get_db())):
    from . import models
    trusts = db.query(models.Trust).order_by(models.Trust.created_at.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "trusts": trusts})

@app.get("/trusts/{trust_id}")
def view_trust(trust_id: str, request: Request, db=next(get_db())):
    from . import models
    trust = db.query(models.Trust).filter(models.Trust.id == trust_id).first()
    bills = db.query(models.Bill).filter(models.Bill.trust_id == trust_id).all()
    return templates.TemplateResponse("trust.html", {"request": request, "trust": trust, "bills": bills})

@app.get("/bills/{bill_id}/view")
def view_bill(bill_id: str, request: Request, db=next(get_db())):
    from . import models
    bill = db.query(models.Bill).filter(models.Bill.id == bill_id).first()
    txns = db.query(models.Transaction).filter(models.Transaction.bill_id == bill_id).all()
    return templates.TemplateResponse("bill.html", {"request": request, "bill": bill, "transactions": txns})
