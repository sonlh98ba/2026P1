from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from datetime import datetime
import uuid

from .database import SessionLocal
from .models import Account, Transaction, Ledger, BalanceSnapshot
from .audit import audit_log


router = APIRouter()


# ------------------------------
# Database dependency
# ------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------
# Schemas
# ------------------------------
class TransferRequest(BaseModel):
    from_account_no: str
    to_account_no: str
    amount: int
    description: str | None = None


# ------------------------------
# Helper functions
# ------------------------------

def get_account_by_no(db: Session, acc_no: str) -> Account:
    acc = db.query(Account).filter(Account.account_no == acc_no).first()
    if not acc:
        raise HTTPException(404, f"Account {acc_no} not found")
    return acc


def get_balance(db: Session, acc_id):
    snap = db.query(BalanceSnapshot)\
             .filter(BalanceSnapshot.account_id == acc_id)\
             .first()
    return snap.balance if snap else 0


def update_balance(db: Session, acc_id, balance):
    snap = db.query(BalanceSnapshot)\
             .filter(BalanceSnapshot.account_id == acc_id)\
             .first()

    if snap:
        snap.balance = balance
        snap.updated_at = datetime.utcnow()
    else:
        snap = BalanceSnapshot(
            account_id=acc_id,
            balance=balance
        )
        db.add(snap)


# ------------------------------
# API: Create account
# ------------------------------
@router.post("/accounts")
def create_account(db: Session = Depends(get_db)):
    try:
        acc = Account(
            account_no=str(uuid.uuid4())[:10],
            status="ACTIVE"
        )

        db.add(acc)
        db.flush()

        snapshot = BalanceSnapshot(
            account_id=acc.id,
            balance=0
        )

        db.add(snapshot)
        db.commit()

        audit_log(
            action="CREATE_ACCOUNT",
            api="/api/accounts",
            method="POST",
            user=acc.account_no,
            status="SUCCESS"
        )

        return {
            "account_id": str(acc.id),
            "account_no": acc.account_no,
            "balance": 0
        }

    except Exception as e:
        db.rollback()

        audit_log(
            action="CREATE_ACCOUNT",
            api="/api/accounts",
            method="POST",
            status="FAILED",
            extra={
                "error": str(e)
            }
        )

        raise HTTPException(500, "Create account failed")


# ------------------------------
# API: Get balance (by account_no)
# ------------------------------
@router.get("/balance/{account_no}")
def get_account_balance(account_no: str, db: Session = Depends(get_db)):
    acc = get_account_by_no(db, account_no)
    balance = get_balance(db, acc.id)
    return {
        "account_no": account_no,
        "balance": balance
    }


# ------------------------------
# API: Transfer money (by account_no)
# ------------------------------
@router.post("/transfer")
def transfer_money(req: TransferRequest, db: Session = Depends(get_db)):
    try:
        if req.amount <= 0:
            raise HTTPException(400, "Invalid transfer amount")

        from_acc = get_account_by_no(db, req.from_account_no)
        to_acc = get_account_by_no(db, req.to_account_no)

        from_id = from_acc.id
        to_id = to_acc.id

        # Lock rows
        db.execute(
            text("SELECT * FROM balance_snapshots WHERE account_id=:id FOR UPDATE"),
            {"id": from_id}
        )
        db.execute(
            text("SELECT * FROM balance_snapshots WHERE account_id=:id FOR UPDATE"),
            {"id": to_id}
        )

        from_balance = get_balance(db, from_id)
        to_balance = get_balance(db, to_id)

        if from_balance < req.amount:
            raise HTTPException(400, "Insufficient balance")

        desc = req.description or f"{req.from_account_no} chuyen tien"

        tx = Transaction(
            id=uuid.uuid4(),
            type="TRANSFER",
            status="PENDING",
            amount=req.amount,
            description=desc,
            created_at=datetime.utcnow()
        )
        db.add(tx)
        db.flush()

        db.add(Ledger(
            id=uuid.uuid4(),
            account_id=from_id,
            tx_id=tx.id,
            debit=req.amount,
            credit=0,
            balance_after=from_balance - req.amount
        ))

        db.add(Ledger(
            id=uuid.uuid4(),
            account_id=to_id,
            tx_id=tx.id,
            debit=0,
            credit=req.amount,
            balance_after=to_balance + req.amount
        ))

        update_balance(db, from_id, from_balance - req.amount)
        update_balance(db, to_id, to_balance + req.amount)

        tx.status = "SUCCESS"
        db.commit()

        audit_log(
            action="TRANSFER",
            api="/api/transfer",
            method="POST",
            user=req.from_account_no,
            amount=req.amount,
            description=desc,
            status="SUCCESS"
        )

        return {
            "status": "success",
            "tx_id": str(tx.id),
            "from_account": req.from_account_no,
            "to_account": req.to_account_no,
            "amount": req.amount
        }

    except HTTPException as e:
        db.rollback()

        audit_log(
            action="TRANSFER",
            api="/api/transfer",
            method="POST",
            user=req.from_account_no,
            amount=req.amount,
            status="FAILED",
            extra={
                "reason": e.detail,
                "code": e.status_code
            }
        )

        raise e

    except Exception as e:
        db.rollback()

        audit_log(
            action="TRANSFER",
            api="/api/transfer",
            method="POST",
            user=req.from_account_no,
            amount=req.amount,
            status="FAILED",
            extra={
                "error": str(e)
            }
        )

        raise HTTPException(500, "System error")


# ------------------------------
# API: Transaction history (by account_no)
# ------------------------------
@router.get("/transactions/{account_no}")
def get_transaction_history(account_no: str, db: Session = Depends(get_db)):
    acc = get_account_by_no(db, account_no)

    rows = (
        db.query(Ledger, Transaction)
        .join(Transaction, Ledger.tx_id == Transaction.id)
        .filter(Ledger.account_id == acc.id)
        .order_by(Ledger.created_at.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "time": ledger.created_at,
            "debit": ledger.debit,
            "credit": ledger.credit,
            "balance_after": ledger.balance_after,
            "tx_id": str(ledger.tx_id),
            "description": tx.description
        }
        for ledger, tx in rows
    ]