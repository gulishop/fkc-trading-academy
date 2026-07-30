# Day 18 — Report Banana (Total Income/Expense)

- **Concept:** Sirf credit ya sirf debit ka total nikalna
- **Example:**
  ```python
  def total_income():
      return sum(t["amount"] for t in transactions if t["type"] == "credit")

  def total_expense():
      return sum(t["amount"] for t in transactions if t["type"] == "debit")
  ```
- **Practice:** Total income aur expense alag print karwayen
- **Mini Project:** "Income vs Expense Report"
