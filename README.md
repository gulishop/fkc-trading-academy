# FKC Trading Academy — Daily Lesson Auto-Post System

Yeh repo har din automatic **agla lesson** Telegram group mein post karta hai. Shuruati 30 din ka Python/coding course already yahan maujood hai — lekin system sirf 30 din tak mehdood nahi, aap khud roz naya lesson (`day-31.md`, `day-32.md`...) likh kar daal sakte hain aur yeh **mahinon tak** khud-ba-khud chalta rahega (coding ke baad e-commerce, phir trading wagera).

Students group mein lesson parhte hain, practice karte hain, aur apni assignment (code) group mein ya GitHub par submit karte hain.

---

## 📁 Is Repo Mein Kya Hai

```
coding-academy-repo/
├── lessons/              → Har din ka lesson (day-01.md, day-02.md... jitne bhi ban jayen)
├── assignments/          → Students yahan apna code upload/submit karenge
├── .github/workflows/    → Automation jo har din "agla" lesson Telegram par bhejta hai
└── README.md             → Yeh file
```

**Zaroori baat:** Yeh system din ki tareekh se nahi, balke **sequence** se chalta hai. Matlab agar aaj `day-31.md` post hui, to kal khud-ba-khud `day-32.md` dhoondega — agar woh file maujood ho to bhej dega, agar nahi to us din kuch nahi bhejega aur agle din phir try karega. Isliye aap jab bhi free hon, agla lesson likh kar daal dein, koi jaldi nahi.

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

### Step 6: Workflow ko Likhne ki Ijazat Dein
System ko har lesson bhejne ke baad ek chota "counter" file save karni hoti hai (taake use yaad rahe kaunsa lesson agla hai). Iske liye ek baar yeh on karna hoga:
1. Repo mein **Settings → Actions → General** par jayen
2. Neeche **"Workflow permissions"** section dhundein
3. **"Read and write permissions"** select karein
4. **"Save"** dabayen

### Step 7: Test Karein
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

## ➕ Naya Lesson Roz Kaise Add Karein

1. Repo mein `lessons` folder kholein
2. **"Add file" → "Create new file"**
3. Naam dein agle number ke hisaab se — jaise agar Day 30 tak ho chuka hai, to naya file `day-31.md` (2-digit number, jaise `31`, `32`... `99` tak)
4. Us din ka lesson likhein (concept, example, practice, mini project — jaisa format pehle 30 din mein tha)
5. "Commit new file" dabayen

Bas itna hi — agli baar jab automation chalega, yeh khud yeh nayi file dhoond kar bhej dega. Aapko kahin aur kuch badalna nahi.

**Note:** Agar 99 din se aage (matlab ~3+ mahine) jana ho, tab number format 2-digit se 3-digit karna padega — us waqt bata dijiyega, main workflow update kar dunga.

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
