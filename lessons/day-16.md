# Day 16 — Ledger ka Core Function

- **Concept:** Naya transaction add karne wala function
- **Example:**
  ```python
  transactions = []

  def add_transaction(desc, amount, type_):
      transactions.append({"desc": desc, "amount": amount, "type": type_})

  add_transaction("Salary", 5000, "credit")
  add_transaction("Rent", 1000, "debit")
  ```
- **Practice:** 3-4 transactions add karwayen aur print karwayen
- **Mini Project:** "Add Transaction Tool"
