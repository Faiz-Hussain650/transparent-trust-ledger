from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from ..deps import get_db
from .. import models

router = APIRouter(prefix="/trusts", tags=["trusts"])

# Simple admin key for demo; swap with proper auth/JWT in production
ADMIN_API_KEY_HEADER = "X-Admin-Token"


def verify_admin(x_admin_token: str = Header(None)):
    if x_admin_token != "changeme-admin-token":
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("", dependencies=[Depends(verify_admin)])
def create_trust(name: str, description: str = "", contact_email: str = "", db: Session = Depends(get_db)):
    trust = models.Trust(
        name=name,
        description=description,
        contact_email=contact_email,
    )
    db.add(trust)
    db.commit()
    db.refresh(trust)
    return trust


@router.get("/{trust_id}")
def get_trust(trust_id: str, db: Session = Depends(get_db)):
    trust = db.query(models.Trust).filter(models.Trust.id == trust_id).first()
    if not trust:
        raise HTTPException(status_code=404, detail="Trust not found")
    return trust
