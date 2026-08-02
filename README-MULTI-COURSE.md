# Multi-Course Daily Lessons — Setup Guide

## Kya badla hai

- **`generate_post.py`** — poori tarah rewrite. Ab ek hi run mein **10 courses**
  (`COURSES` dictionary dekhein: YouTube Automation, Social Media Marketing, AI
  Tools & Automation, Facebook Page Growth, Amazon FBA, Daraz Seller,
  Dropshipping, Freelancing, Digital Marketing & SEO, Graphic Design/Canva) ke
  liye alag-alag daily lesson banata hai.
- **`daily-post.yml`** — ab sirf **ek** schedule hai: `0 10 * * *` (10:00 UTC =
  **3:00 PM Pakistan time**), jab woh saare courses ke lessons ek sath generate
  karta hai.
- **`index.html`** (auto-generated) — ab har course ek **tappable card** hai
  (icon/logo, tagline, latest lesson preview). Card par tap karne se us course
  ka apna page khulta hai.
- **`courses/<course-slug>/index.html`** (auto-generated) — har course ka apna
  lessons list, purane se naye order mein.
- **`courses/<course-slug>/posts/<date>-<id>.html`** (auto-generated) — har
  individual lesson, jisme pehle jaisa hi Share box hai (WhatsApp, Facebook,
  Telegram, Instagram, Other).
- **`courses.css`** — naya stylesheet, sirf card-grid aur course-tag styling ke
  liye. Yeh aapke maujooda `style.css` ko override nahi karta, sirf uske saath
  load hota hai.
- **`style.css`** — is bundle mein ek basic fallback diya gaya hai. **Agar
  aapke repo mein pehle se `style.css` maujood hai to isse skip/replace na
  karein** — bas `courses.css` ko add kar dein, dono sath load ho jayenge.
- **`posts.json`** — ab format badal gaya hai: pehle ek flat list thi, ab
  `{ "course-slug": [ {...}, {...} ] }` jaisa dictionary hai (per-course
  history). Purani `posts.json` is naye script ke saath compatible nahi hai —
  ise delete/rename kar dein taake script fresh shuru kare.

## Naya course add karna ho to

`generate_post.py` mein `COURSES` dictionary mein bas ek naya entry add karein:

```python
"new-course-slug": {
    "name": "Course Ka Naam",
    "icon": "🚀",
    "tagline": "Ek line tagline",
    "topics": ["Topic 1", "Topic 2", ...],
},
```

Baaki sab (home card, course page, lessons, posting) automatically ban jayega.

## Deploy karne ke steps

1. In files ko apne GitHub repo mein daal dein (`generate_post.py`,
   `.github/workflows/daily-post.yml` ki jagah is naye `daily-post.yml` ko
   rakhein, `courses.css`, aur agar zaroorat ho to `style.css`).
2. Purani `posts.json` delete/rename kar dein.
3. GitHub Secrets check karein — ab sirf ye chahiye:
   `GEMINI_API_KEY` (zaroori), aur optional: `SITE_URL`,
   `TELEGRAM_CHANNEL_LINK`, `FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN`,
   `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
4. `Actions` tab se workflow ko manually ek dafa run karein
   (`workflow_dispatch`) taake pehla set of lessons ban jaye aur `index.html`
   generate ho.

## Note

- Forex/Crypto wala purana single-topic system ab is naye script mein
  shamil nahi hai (agar chahiye to woh alag repo/workflow mein rehne dein) —
  ye naya system general skill-courses ke liye hai jo aapne request kiya.
