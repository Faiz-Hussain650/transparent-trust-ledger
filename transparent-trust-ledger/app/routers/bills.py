from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal
from ..deps import get_db
from .. import models

router = APIRouter(prefix="/bills", tags=["bills"])

ADMIN_API_KEY_HEADER = "X-Admin-Token"


def verify_admin(x_admin_token: str = Header(None)):
    if x_admin_token != "changeme-admin-token":
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("", dependencies=[Depends(verify_admin)])
def create_bill(
    trust_id: str,
    title: str,
    amount_required: float,
    description: str = "",
    due_date: date | None = None,
    invoice_url: str | None = None,
    db: Session = Depends(get_db),
):
    trust = db.query(models.Trust).filter(models.Trust.id == trust_id).first()
    if not trust:
        raise HTTPException(status_code=404, detail="Trust not found")

    bill = models.Bill(
        trust_id=trust.id,
        title=title,
        description=description,
        amount_required=Decimal(str(amount_required)),
        due_date=due_date,
        invoice_url=invoice_url,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill
