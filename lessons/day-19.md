# Day 19 — File mein Save Karna (CSV)

- **Concept:** Data band karne pe khatam na ho, file mein save ho
- **Example:**
  ```python
  import csv
  with open("ledger.csv", "w", newline="") as f:
      writer = csv.writer(f)
      for t in transactions:
          writer.writerow([t["desc"], t["amount"], t["type"]])
  ```
- **Practice:** Apni transactions ko file mein save karwayen
- **Mini Project:** "Save & Load Ledger"
