# Day 17 — Balance Calculate Karna

- **Concept:** Credit - Debit se balance nikalna
- **Example:**
  ```python
  def calculate_balance():
      balance = 0
      for t in transactions:
          if t["type"] == "credit":
              balance += t["amount"]
          else:
              balance -= t["amount"]
      return balance

  print("Balance:", calculate_balance())
  ```
- **Practice:** Apni transactions ka balance nikalwayen
- **Mini Project:** "Balance Checker"
