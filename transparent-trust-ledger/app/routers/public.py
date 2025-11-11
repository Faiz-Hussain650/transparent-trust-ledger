from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..deps import get_db
from .. import models

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/trusts")
def list_trusts(db: Session = Depends(get_db)):
    return db.query(models.Trust).all()


@router.get("/trusts/{trust_id}/bills")
def list_bills_for_trust(trust_id: str, db: Session = Depends(get_db)):
    bills = db.query(models.Bill).filter(models.Bill.trust_id == trust_id).all()
    return bills


@router.get("/bills/{bill_id}")
def bill_detail(bill_id: str, db: Session = Depends(get_db)):
    bill = (
        db.query(models.Bill)
        .filter(models.Bill.id == bill_id)
        .first()
    )
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    txns = (
        db.query(models.Transaction)
        .filter(models.Transaction.bill_id == bill_id)
        .order_by(models.Transaction.created_at.desc())
        .all()
    )

    return {"bill": bill, "transactions": txns}


@router.get("/verify/{payment_id}")
def verify_transaction(payment_id: str, db: Session = Depends(get_db)):
    tx = (
        db.query(models.Transaction)
        .filter(models.Transaction.razorpay_payment_id == payment_id)
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {
        "payment_id": tx.razorpay_payment_id,
        "bill_id": str(tx.bill_id),
        "trust_id": str(tx.trust_id),
        "amount": float(tx.amount),
        "currency": tx.currency,
        "canonical_hash": tx.canonical_hash,
        "ipfs_cid": tx.ipfs_cid,
        "created_at": tx.created_at,
    }
