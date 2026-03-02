from sqlalchemy import Column, String, BigInteger, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from .database import Base

class Account(Base):
    __tablename__ = "accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_no = Column(String, unique=True)
    status = Column(String)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String)
    status = Column(String)
    amount = Column(BigInteger)
    description = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Ledger(Base):
    __tablename__ = "ledger_entries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    tx_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    debit = Column(BigInteger, default=0)
    credit = Column(BigInteger, default=0)
    balance_after = Column(BigInteger)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class BalanceSnapshot(Base):
    __tablename__ = "balance_snapshots"
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), primary_key=True)
    balance = Column(BigInteger)
