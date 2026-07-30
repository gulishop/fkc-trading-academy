# Computer Academy — 30 Din Coding Lesson Plan (Auto-Post System)

Yeh repo har din automatic ek coding lesson **Telegram group** mein post karta hai. Students wahan lesson parhte hain, practice karte hain, aur apni assignment (code) group mein ya GitHub par submit karte hain.

---

## 📁 Is Repo Mein Kya Hai

```
coding-academy-repo/
├── lessons/              → 30 din ke lessons (day-01.md se day-30.md tak)
├── assignments/          → Students yahan apna code upload/submit karenge
├── .github/workflows/    → Automation jo daily lesson Telegram par bhejta hai
└── README.md             → Yeh file
```

---

## 🚀 Setup Karne Ke Steps (Ek Baar Karna Hai)

### Step 1: GitHub Repository Banayen
1. [github.com](https://github.com) par account banayen (agar nahi hai)
2. Naya repository banayen — naam de dein jaise `coding-academy-lessons`
3. Is folder (`coding-academy-repo`) ke andar ki sari files us repo mein upload kar dein
   - GitHub website par "Add file → Upload files" se seedha upload ho jayega, koi command line zaroori nahi

### Step 2: Telegram Bot Banayen (5 minute ka kaam)
1. Telegram app kholein, **@BotFather** ko search karke message karein
2. `/newbot` type karein
3. Bot ka naam aur username set karein (jaise `MyAcademyBot`)
4. BotFather aapko ek **Bot Token** dega — yeh save kar lein (kisi ko na dikhayen)

### Step 3: Students ka Telegram Group Banayen
1. Telegram mein naya **Group** banayen (Channel bhi chal sakta hai)
2. Sare students ko us group mein add karein
3. Apne bot ko bhi group mein add karein, aur usay **Admin** bana dein
4. Group ka Chat ID pata karne ke liye:
   - Group mein koi bhi message bhejein
   - Browser mein yeh link kholein (BOT_TOKEN apni jagah dalein):
     `https://api.telegram.org/botBOT_TOKEN/getUpdates`
   - Result mein `"chat":{"id": -1001234567890` jaisa number milega — yeh aapka **Chat ID** hai

### Step 4: GitHub mein Secrets Add Karein
1. Apne GitHub repo mein jayen: **Settings → Secrets and variables → Actions**
2. "New repository secret" par click karein, do secrets banayen:
   - `TELEGRAM_BOT_TOKEN` → Step 2 wala token
   - `TELEGRAM_CHAT_ID` → Step 3 wala chat id
3. Save kar dein

### Step 5: Start Date Set Karein
`.github/workflows/daily-lesson.yml` file kholein aur yeh line dhundein:
```
START_DATE="2026-07-30"
```
Yahan wohi tareekh likhein jis din se Day 1 shuru karna hai.

### Step 6: Test Karein
1. GitHub repo mein **Actions** tab par jayen
2. "Daily Lesson Post" workflow chunein
3. "Run workflow" button dabayen (manual test ke liye)
4. Telegram group check karein — lesson message aa jani chahiye

Bas! Ab yeh har roz **automatic** (subah 9 baje PKT, waqt aap badal sakte hain) us din ka lesson khud group mein post karta rahega.

---

## 📝 Students Assignment Kaise Submit Karenge

Do aasan tareeqe hain — jo aapke students ke level ke hisaab se behtar ho, wohi rakhein:

**Tareeqa A (Aasan — Beginners ke liye):**
Student apna code screenshot ya `.py` file **seedha Telegram group mein** bhej de, reply karke us din ke lesson ke sath. Aap group mein check karke feedback de dein.

**Tareeqa B (Thoda Advanced — GitHub sikhane ke liye):**
1. Har student apna naam se ek folder banaye: `assignments/student-naam/`
2. Apna code us folder mein `day-XX.py` naam se upload kare (GitHub app se mobile par bhi ho sakta hai)
3. Yeh unhein GitHub istemal karna bhi sikha dega — jo khud ek coding skill hai

---

## ⏰ Post Time Badalna Ho To
`daily-lesson.yml` mein yeh line hai:
```
- cron: '0 4 * * *'
```
Yeh UTC time hai. Pakistan time (PKT) = UTC + 5 ghante. Misal:
- Subah 9 AM PKT chahiye → `0 4 * * *`
- Shaam 5 PM PKT chahiye → `0 12 * * *`

---

## ❓ Agar Koi Masla Aaye
- Message nahi aa raha → check karein bot Admin hai group mein, aur Chat ID sahi hai
- Workflow fail ho raha → GitHub repo ke **Actions** tab mein error dekh sakte hain
