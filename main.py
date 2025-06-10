import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

class CreateAccount (BaseModel):
    name: str
    account_no:str
    balance: float
    acc_type: str = '1'
    # min_balance: float = 500.0

class Transaction(BaseModel):
    account_no: str
    amount: float
#------------------------------------------------------
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


accounts: Dict[str, BankAccount] = {}

@app.post("/create-account")
def create_account(data: CreateAccount):
    if not data.name.strip():
        return {"error": "Name cannot be empty."}
    if not data.account_no.strip():
        return {"error": "Invalid account number format."}
    if data.account_no in accounts:
        return {"error": "Account number already exists."}

    if data.acc_type == '1':
        account = BankAccount(data.name, data.account_no, data.balance, data.acc_type)
    elif data.acc_type == '2':
        account = SavingsAccount(data.name, data.account_no, data.balance)
    elif data.acc_type == '3':
        account = NRIAccount(data.name, data.account_no, data.balance)
    else:
        return {"error": "Invalid account type."}

    accounts[data.account_no] = account
    return {"message": f"Account created: {account.name} | Acc No: {account.accountno}"}

@app.get("/balance/{accountno}")
def check_balance(accountno: str):
    account = accounts.get(accountno)
    if account:
        return {"balance": account.get_balance()}
    return {"error": "Account not found."}


@app.post("/deposit")
def deposit_money(data: Transaction):
    account = accounts.get(data.accountno)
    if not account:
        return {"error": "Account not found."}
    if account.deposit(data.amount):
        return {
            "message": f"Deposited: ₹{data.amount:.2f}",
            "new_balance": account.get_balance()
        }
    return {"message": "Invalid deposit amount."}


@app.post("/withdraw")
def withdraw_money(data: Transaction):
    account = accounts.get(data.accountno)
    if not account:
        return {"error": "Account not found."}
    if account.withdraw(data.amount):
        return {
            "message": f"Withdrew: ₹{data.amount:.2f}",
            "new_balance": account.get_balance()
        }
    return {"message": "Insufficient balance or invalid amount."}


@app.get("/")
def welcome():
    return {"message": "Welcome to Sarvodaya Bank Online"}
