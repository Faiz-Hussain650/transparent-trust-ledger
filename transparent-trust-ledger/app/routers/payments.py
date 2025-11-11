from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from decimal import Decimal
import hmac
import hashlib
import razorpay

from ..deps import get_db
from ..config import settings
from .. import models
from ..security import canonicalize, sha256_hex

router = APIRouter(prefix="/payments", tags=["payments"])

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@router.post("/create-order")
def create_order(
    bill_id: str,
    amount: float,
    db: Session = Depends(get_db),
):
    """
    1. Validate bill.
    2. Create Razorpay order for given amount (INR).
    3. Return order_id and key_id for frontend checkout.
    """
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    bill = db.query(models.Bill).filter(models.Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    if bill.status == "PAID":
        raise HTTPException(status_code=400, detail="Bill already fully paid")

    # Optional: cap amount to remaining needed
    remaining = float(bill.amount_required - bill.amount_collected)
    if amount > remaining:
        amount = remaining

    order = razorpay_client.order.create({
        "amount": int(amount * 100),  # rupees to paise
        "currency": "INR",
        "payment_capture": 1,
        "notes": {"bill_id": str(bill.id)},
    })

    return {
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    }


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Razorpay calls this on events.
    We:
    - Verify signature
    - On payment.captured:
      - Build canonical JSON
      - Hash it
      - Insert Transaction
      - Update Bill
      - Append in AuditLog
    """
    body_bytes = await request.body()
    signature = request.headers.get("x-razorpay-signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    payload = await request.json()
    event = payload.get("event")

    if event != "payment.captured":
        # For MVP, ignore other events
        return {"status": "ignored"}

    payment = payload["payload"]["payment"]["entity"]
    bill_id = payment.get("notes", {}).get("bill_id")

    bill = db.query(models.Bill).filter(models.Bill.id == bill_id).first()
    if not bill:
        # Still log attempt
        audit = models.AuditLog(
            event_type="PAYMENT_FOR_UNKNOWN_BILL",
            ref_table="razorpay",
            ref_id=payment["id"],
            data=payment,
        )
        db.add(audit)
        db.commit()
        return {"status": "bill_not_found"}

    txn_meta = {
        "razorpay_payment_id": payment["id"],
        "razorpay_order_id": payment.get("order_id"),
        "bill_id": str(bill.id),
        "trust_id": str(bill.trust_id),
        "amount": payment["amount"] / 100,
        "currency": payment["currency"],
        "email": payment.get("email"),
        "contact": payment.get("contact"),
        "method": payment.get("method"),
        "created_at_unix": payment.get("created_at"),
    }

    canonical = canonicalize(txn_meta)
    txn_hash = sha256_hex(canonical)

    tx = models.Transaction(
        trust_id=bill.trust_id,
        bill_id=bill.id,
        razorpay_payment_id=txn_meta["razorpay_payment_id"],
        razorpay_order_id=txn_meta["razorpay_order_id"],
        donor_email=txn_meta["email"],
        amount=Decimal(str(txn_meta["amount"])),
        currency=txn_meta["currency"],
        canonical_hash=txn_hash,
        ipfs_cid=None,  # add IPFS later if you want
        raw_meta=txn_meta,
    )
    db.add(tx)

    # Update bill aggregate & status
    bill.amount_collected = (bill.amount_collected or 0) + Decimal(str(txn_meta["amount"]))
    if bill.amount_collected >= bill.amount_required:
        bill.status = "PAID"
    elif bill.amount_collected > 0:
        bill.status = "PARTIALLY_PAID"

    audit = models.AuditLog(
        event_type="PAYMENT_RECORDED",
        ref_table="transactions",
        ref_id=txn_meta["razorpay_payment_id"],
        data={"txn_meta": txn_meta, "hash": txn_hash},
    )
    db.add(audit)

    db.commit()
    return {"status": "ok"}
