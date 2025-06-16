import uvicorn
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from account_utils import apply_interest_multiple

# ---------------------- FastAPI and DB Setup ----------------------
app = FastAPI(

)

engine = create_engine("sqlite:///bank_accounts.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ---------------------- Database Model ----------------------
class AccountDB(Base):
    __tablename__ = 'accounts'
    accountno = Column(String, primary_key=True)
    name = Column(String)
    balance = Column(Float)
    acc_type = Column(String)

Base.metadata.create_all(bind=engine)

# ---------------------- Pydantic Models ----------------------
class CreateAccount(BaseModel):
    name: str
    accountno: str
    balance: float
    acc_type: str = '1'

class Transaction(BaseModel):
    amount: float

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------- Account Classes ----------------------
class BankAccount:
    def __init__(self, name, accountno, balance, acc_type='1', min_balance=500.0):
        self.name = name
        self.accountno = accountno
        self.acc_type = acc_type
        self.balance = float(balance)
        self.min_balance = min_balance

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.apply_interest()
            return True
        return False

    def withdraw(self, amount):
        if 0 < amount <= self.balance:
            self.balance -= amount
            return True
        return False

    def get_balance(self):
        return self.balance

    def apply_interest(self):
        pass

class SavingsAccount(BankAccount):
    def __init__(self, name, accountno, balance, acc_type='2'):
        super().__init__(name, accountno, balance, acc_type)
        self.interest_rate = 0.04

    def apply_interest(self):
        interest = self.balance * self.interest_rate
        print(f"Savings Interest of ₹{interest:.2f} added.")
        self.balance += interest

    def withdraw(self, amount):
        if 0 < amount <= self.balance - self.min_balance:
            self.balance -= amount
            return True
        return False

class NRIAccount(SavingsAccount):
    def __init__(self, name, accountno, balance):
        super().__init__(name, accountno, balance, acc_type='3')
        self.interest_rate = 0.065

    def apply_interest(self):
        interest = self.balance * self.interest_rate
        print(f"NRI Interest of ₹{interest:.2f} added.")
        self.balance += interest

    def withdraw(self, amount):
        if 0 < amount <= self.balance + 5000:
            self.balance -= amount
            return True
        return False

# ---------------------- API Endpoints ----------------------
@app.post("/create-account")
def create_account(data: CreateAccount, db: Session = Depends(get_db)):
    if db.query(AccountDB).filter_by(accountno=data.accountno).first():
        return {"error": "Account number already exists."}

    if data.acc_type == '1':
        account = BankAccount(data.name, data.accountno, data.balance, data.acc_type)
    elif data.acc_type == '2':
        account = SavingsAccount(data.name, data.accountno, data.balance)
        account.apply_interest()
    elif data.acc_type == '3':
        account = NRIAccount(data.name, data.accountno, data.balance)
        account.apply_interest()
    else:
        return {"error": "Invalid account type."}

    db_account = AccountDB(
        accountno=account.accountno,
        name=account.name,
        balance=account.balance,
        acc_type=account.acc_type
    )
    # breakpoint()
    db.add(db_account)
    db.commit()
    return {
        "message": f"Account created: {account.name} | Acc No: {account.accountno}",
        "initial_balance_with_interest": account.get_balance()
    }

@app.get("/balance/{accountno}")
def check_balance(accountno: str, db: Session = Depends(get_db)):
    acc = db.query(AccountDB).filter_by(accountno=accountno).first()
    if acc:
        return {"balance: {acc.balance:.2f}"}
    return {"error": "Account not found."}

@app.put("/deposit/{accountno}")
def deposit_money(accountno: str, data: Transaction, db: Session = Depends(get_db)):
    acc = db.query(AccountDB).filter_by(accountno=accountno).first()
    if not acc:
        return {"error": "Account not found."}

    if acc.acc_type == '1':
        account = BankAccount(acc.name, acc.accountno, acc.balance)
    elif acc.acc_type == '2':
        account = SavingsAccount(acc.name, acc.accountno, acc.balance)
        breakpoint()
    else:
        account = NRIAccount(acc.name, acc.accountno, acc.balance)

    if account.deposit(data.amount):
        apply_interest_multiple(account)
        acc.balance = account.balance
        db.commit()
        return {
            "message": f"Deposited: ₹{data.amount:.2f}",
            "new_balance": f"{acc.balance:.2f}"
        }

    return {"message": "Invalid deposit amount."}

@app.put("/withdraw/{accountno}")
def withdraw_money(accountno: str, data: Transaction, db: Session = Depends(get_db)):
    acc = db.query(AccountDB).filter_by(accountno=accountno).first()
    if not acc:
        return {"error": "Account not found."}

    if acc.acc_type == '1':
        account = BankAccount(acc.name, acc.accountno, acc.balance)
        # breakpoint()
    elif acc.acc_type == '2':
        account = SavingsAccount(acc.name, acc.accountno, acc.balance)
        # breakpoint()
    else:
        account = NRIAccount(acc.name, acc.accountno, acc.balance)
        # breakpoint()

    if account.withdraw(data.amount):
        acc.balance = account.balance
        db.commit()
        return {
            "message": f"Withdrew: ₹{data.amount:.2f}",
            "new_balance": acc.balance
        }
    return {"message": "Insufficient balance or invalid amount."}

@app.get("/")
def welcome():
    return {"message": "Welcome to Sarvodaya Bank Online"}
