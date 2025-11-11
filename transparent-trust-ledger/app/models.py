import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, DateTime, JSON, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base

class Trust(Base):
    __tablename__ = "trusts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    contact_email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    bills = relationship("Bill", back_populates="trust")

class Bill(Base):
    __tablename__ = "bills"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trust_id = Column(UUID(as_uuid=True), ForeignKey("trusts.id"))
    title = Column(String(255))
    description = Column(Text)
    amount_required = Column(Numeric(12,2))
    amount_collected = Column(Numeric(12,2), default=0)
    status = Column(String(32), default="OPEN")
    created_at = Column(DateTime, default=datetime.utcnow)
    trust = relationship("Trust", back_populates="bills")
    transactions = relationship("Transaction", back_populates="bill")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("bills.id"))
    razorpay_payment_id = Column(String(255))
    amount = Column(Numeric(12,2))
    canonical_hash = Column(String(128))
    raw_meta = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    bill = relationship("Bill", back_populates="transactions")

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_type = Column(String(64))
    ref_table = Column(String(64))
    ref_id = Column(String(255))
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
