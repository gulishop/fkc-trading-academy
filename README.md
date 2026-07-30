# FKC Trading Academy — Daily Lesson Auto-Post System

Yeh repo har din **3:00 PM Pakistan time** par automatic **agla lesson** Telegram group mein post karta hai. Pehle 30 din ka Python/coding course pehle se likha hua hai. Day 31 se aage, agar aap khud lesson nahi likhte, **Gemini AI khud naya lesson likh kar** post kar deta hai — matlab yeh **mahinon tak** khud-ba-khud chalta rahega, bina rukay (coding ke baad e-commerce, phir trading wagera).

Students group mein lesson parhte hain, practice karte hain, aur apni assignment (code) group mein ya GitHub par submit karte hain.

---

## 📁 Is Repo Mein Kya Hai

```
coding-academy-repo/
├── lessons/              → Har din ka lesson (day-01.md, day-02.md... jitne bhi ban jayen)
├── assignments/          → Students yahan apna code upload/submit karenge
├── scripts/              → build_page.py — lesson ko docs/index.html page mein badalta hai
├── docs/                 → GitHub Pages yahan se site banata hai (index.html khud-ba-khud update hoti hai)
├── .github/workflows/    → Automation jo har din "agla" lesson Telegram par bhejta hai + page banata hai
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

### Step 4: Gemini API Key Banayen (Day 31 ke baad ke liye)
Yeh key Day 30 khatam hone ke baad AI se naye lessons khud likhwane ke liye chahiye — bilkul free hai shuru mein.
1. Browser mein jayen: **aistudio.google.com**
2. Apne Google account se sign in karein
3. Left menu mein **"Get API key"** par tap karein
4. **"Create API key"** dabayen
5. Jo key milegi, usay copy karke kahin save kar lein (yeh dobara poori nahi dikhegi)

### Step 5: GitHub mein Secrets Add Karein
1. Apne GitHub repo mein jayen: **Settings → Secrets and variables → Actions**
2. "New repository secret" par click karein, teen secrets banayen:
   - `TELEGRAM_BOT_TOKEN` → Step 2 wala token
   - `TELEGRAM_CHAT_ID` → Step 3 wala chat id
   - `GEMINI_API_KEY` → Step 4 wali Gemini key
3. Har ek ke baad "Add secret" dabayen

### Step 6: Workflow ko Likhne ki Ijazat Dein
System ko har lesson bhejne ke baad ek chota "counter" file save karni hoti hai (taake use yaad rahe kaunsa lesson agla hai, aur Gemini ka likha lesson bhi save ho sake). Iske liye ek baar yeh on karna hoga:
1. Repo mein **Settings → Actions → General** par jayen
2. Neeche **"Workflow permissions"** section dhundein
3. **"Read and write permissions"** select karein
4. **"Save"** dabayen

### Step 7: GitHub Pages On Karein (lesson page + WhatsApp share ke liye)
1. Repo mein **Settings → Pages** par jayen
2. **"Build and deployment" → Source** mein select karein: **Deploy from a branch**
3. Branch: **main**, folder: **/docs** — phir **Save** dabayen
4. Thodi der baad yahan ek link mil jayegi jaise: `https://gulishop.github.io/fkc-trading-academy/` — yeh aapki lesson page hai

### Step 8: Test Karein
1. GitHub repo mein **Actions** tab par jayen
2. "Daily Lesson Post" workflow chunein
3. "Run workflow" button dabayen (manual test ke liye)
4. Telegram group check karein — lesson message aa jani chahiye
5. Step 7 wali Pages link kholein — aaj ka lesson page par bhi dikhna chahiye

Bas! Ab yeh har roz **automatic, 3:00 PM Pakistan time par** us din ka lesson khud group mein post karta rahega:
- **Day 1–30:** pehle se likhe hue lessons post honge
- **Day 31 se aage:** agar aap khud naya lesson nahi likhte, to **Gemini AI khud us din ka lesson likh kar** post kar dega aur repo mein save bhi kar dega — matlab system kabhi nahi rukega
- Har post ke sath **docs/index.html** (aapki Pages site) bhi khud-ba-khud update ho jayegi

---

## 🌐 Lesson Page + WhatsApp Share (Naya Feature)

Har din jab lesson post hota hai, system usi lesson se ek chhoti web page bhi bana deta hai (`docs/index.html`, Step 7 wali link par live).

**WhatsApp ka koi free/official group-bot API nahi hai** (Telegram jaisa), isliye poori posting automatic nahi ho sakti — is wajah se page par do buttons diye gaye hain:

- **"Share lesson on WhatsApp"** — yeh button aap dabayen: WhatsApp khud khulega, lesson ka poora text pehle se likha hoga, aap sirf apna students wala WhatsApp group choose karke bhej dein. Isi tarah aap keh rahe the ke "jab bhi lesson post hoga mai students k WhatsApp group mai share kroga" — yeh button wahi kaam ek tap mein karta hai.
- **Assignment box** — page ke neeche ek alag section hai jahan student apna naam aur jawab/code likh kar **"Send via WhatsApp"** dabata hai — uska WhatsApp bhi khud khulega, jawab pehle se likha hoga, student apna group choose karke submit kar dega.

Yeh Telegram wali automatic posting ko replace nahi karta — Telegram post hota rehta hai jaisa pehle tha, page sirf WhatsApp ke liye ek aasan tareeqa hai.

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

## ➕ Naya Lesson: Khud Likhein Ya AI Pe Chhod Dein

**Day 31 se aage do tareeke hain, aap kabhi bhi switch kar sakte hain:**

**Option A — Khud Likhna (Full Control):**
1. Repo mein `lessons` folder kholein
2. **"Add file" → "Create new file"**
3. Naam dein agle number ke hisaab se — jaise `day-31.md`
4. Us din ka lesson likhein (concept, example, practice, mini project)
5. "Commit new file" dabayen

Agar aap khud file daal dete hain, system usay hi post karega — Gemini use nahi karega us din.

**Option B — Gemini Pe Chhorna (Automatic):**
Kuch na karein. Agar us din ki file maujood nahi, system khud Gemini AI se lesson likhwa kar post kar dega aur repo mein save kar dega — taake aap baad mein check kar saken kya bheja gaya.

**Sifarish:** Shuru mein Gemini ke bhejay hue lessons **Telegram/GitHub mein check karte rahen** — agar content theek na lage, us din khud likh kar file daal dein, agli baar system wahi use karega.

**Note:** Agar 99 din se aage (matlab ~3+ mahine) jana ho, tab number format 2-digit se 3-digit karna padega — us waqt bata dijiyega, main workflow update kar dunga.

---

## ⏰ Post Time Badalna Ho To
Abhi yeh **roz 3:00 PM Pakistan time (PKT)** par set hai. `daily-lesson.yml` mein yeh line hai:
```
- cron: '0 10 * * *'
```
Yeh UTC time hai. Pakistan time (PKT) = UTC + 5 ghante. Misal:
- 3 PM PKT (abhi ka setting) → `0 10 * * *`
- Subah 9 AM PKT chahiye → `0 4 * * *`
- Shaam 6 PM PKT chahiye → `0 13 * * *`

---

## ❓ Agar Koi Masla Aaye
- Message nahi aa raha → check karein bot Admin hai group mein, aur Chat ID sahi hai
- Workflow fail ho raha → GitHub repo ke **Actions** tab mein error dekh sakte hain
