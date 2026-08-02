# Multi-Course Daily Lessons — Deploy Karne Ka Tareeqa

Abhi aapki live site (`gulishop.github.io/fkc...`) purane single-course
system par chal rahi hai (Coding → E-commerce → Trading, ek hi sequence).
Yeh naya system uski jagah leta hai: **16 alag courses**, har course ka
apna section, har ek ka daily lesson roz **3:00 PM Pakistan time** par
generate hota hai, aur home page par tappable cards dikhte hain.

## Shamil courses (abhi)

🎬 YouTube Automation · 📱 Social Media Marketing · 🤖 AI Tools &
Automation · 👍 Facebook Page Growth · 📦 Amazon FBA · 🛒 Daraz Seller ·
🚚 Dropshipping · 💼 Freelancing · 📈 Digital Marketing & SEO · 🎨
Graphic Design (Canva) · ✍️ AI Content Writing & Copywriting · 🎞️ Video
Editing · 🔗 Affiliate Marketing · 👕 Print on Demand · 🧩 No-Code App &
Website Building

Jitne bhi is waqt trend mein "ghar baithe kamane" wale skills hain,
sab shamil hain. Naya course add karna ho to `generate_post.py` mein
`COURSES` dictionary mein bas ek naya entry add kar dein — baaki sab
(home card, course page, lessons, posting) khud ban jayega.

## Logo aur branding

Har page (home, course, lesson) par ab **FKC Trading Academy ka logo**
header mein aur neeche ek chhota "brand footer" mein dikhta hai — sath
mein **Fazul Khan Chandio — Director / CEO — +92 333 3909816**.

Jab bhi koi student **"Share lesson on WhatsApp/Telegram/Facebook"**
button dabata hai, share hone wale text ke sath yeh contact line bhi
khud chali jaati hai. Aur agar `SITE_URL` secret set ho, to jab bhi
lesson ka link kahin bhi paste hoga (WhatsApp/Telegram/Facebook sab
jagah), link preview mein **yehi logo image** apne aap dikhega —
kyunke page ke andar "og:image" tag us logo ki taraf point karta hai.

**Zaroori step:** logo file ko apne repo mein `docs/logo.png` ke naam
se (bilkul yehi naam) upload kar dein — GitHub website par "Add file →
Upload files", `docs` folder ke andar. Ek dafa daal dein, phir har run
par khud reh jayegi (script isay delete/replace nahi karta).

## Deploy karne ke steps

1. **In files ko apne repo mein daal dein** (GitHub website par "Add
   file → Upload files" se, koi command line zaroori nahi):
   - `generate_post.py` (repo ke root mein)
   - `requirements.txt` (repo ke root mein)
   - `.github/workflows/daily-post.yml` — **purani `daily-lesson.yml`
     ko is se replace/delete kar dein**, warna dono workflows chalne
     lagenge aur do dafa post/commit hoga

2. **Purani `docs/index.html` aur `lessons/` folder ka kya karein:**
   Naya system apni khud ki `docs/` aur `lessons/<course-slug>/`
   folders banata hai, aur `posts.json` naye format mein use karta
   hai. Purana single-course data (`lessons/day-XX.md`, purani
   `docs/index.html`) safe rakhne ke liye chahen to `archive-old/`
   naam ke folder mein move kar dein — delete karne ki zaroorat nahi,
   bas woh ab site mein show nahi hoga.

3. **GitHub Secrets check karein** (Settings → Secrets and variables →
   Actions): sirf `GEMINI_API_KEY` zaroori hai. Optional:
   `SITE_URL` (aapki live URL, share links mein use hoti hai),
   `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` (agar Telegram par bhi
   auto-post karwana ho), `FB_PAGE_ID` + `FB_PAGE_ACCESS_TOKEN` (agar
   Facebook Page par bhi auto-post karwana ho).

4. **Workflow permissions** already "Read and write" honi chahiye
   (agar pehle se set hai to kuch nahi karna) — Settings → Actions →
   General → Workflow permissions.

5. **GitHub Pages** already `docs/` folder se serve ho rahi hogi
   (agar pehle set kiya tha) — kuch badalne ki zaroorat nahi.

6. **Actions tab se ek dafa manually run karein**
   (`Daily Course Lessons` workflow → "Run workflow") — is se pehli
   dafa sab 16 courses ka Day 1 generate hoga aur naya home page ban
   jayega. Test ke baad har roz yeh khud 3 PM PKT par chalta rahega.

## Har course kaise kaam karta hai

- Har course ki apni curriculum topics list hai (`generate_post.py`
  mein). Har din Gemini AI us course ka agla topic, step-by-step,
  Concept → Example → Practice → Mini Project format mein likhta hai,
  aur pichle lessons repeat nahi karta.
- Chahen to khud bhi lesson likh sakte hain: `lessons/<course-slug>/
  day-XXX.md` naam se file daal dein (jaise `lessons/youtube-automation/
  day-002.md`), agli baar system Gemini ke bajaye woh file use karega.
- Har lesson page par **WhatsApp, Telegram, aur Facebook** share
  buttons hain — student ek tap mein apne group/friends ko bhej sakta
  hai.
- Home page par har course ka logo/icon, ek line tagline, aur latest
  lesson ka title dikhta hai — tap karte hi us course ka poora lessons
  list khul jata hai.

## Naya course add karna ho to

`generate_post.py` mein `COURSES` dictionary mein ek entry add karein:

```python
"new-course-slug": {
    "name": "Course Ka Naam",
    "icon": "🚀",
    "tagline": "Ek line tagline",
    "topics": ["Topic 1", "Topic 2", "..."],
},
```

Save karke commit karein — agli daily run par yeh course bhi home page
par apna card le kar aa jayega.
