

def apply_interest_multiple(account):
    for _ in range(10):
        account.apply_interest()
        account.balance = round(account.balance, 2)
        print(f"Updated Balance: ₹{account.balance}")

         # Ensure balance is rounded to 2 decimal places

