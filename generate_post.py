"""
Multi-Course Daily Lesson Generator
-------------------------------------
Ye script har course ke liye EK daily lesson generate karta hai (roz 3:00 PM
Pakistan time par GitHub Actions se chalta hai) aur:

1. Google Gemini (FREE API) se har course ka naya step-by-step lesson likhta hai
2. Har lesson ko uske course ke apne folder mein HTML page banata hai
   (courses/<course-slug>/posts/<date>-<id>.html)
3. Har course ka apna index page update karta hai (courses/<course-slug>/index.html)
   jisme us course ke saare lessons list hote hain (daily order mein)
4. Main homepage (index.html) update karta hai jahan har course ek tappable
   card ke through dikhta hai (logo/icon ke sath)
5. Har lesson page par Share buttons (WhatsApp/Facebook/Telegram/Instagram/Other) hote hain
6. Optionally har naye lesson ko Facebook Page aur Telegram par bhi post karta hai

Naya course add karna ho to bas neeche "COURSES" dictionary mein ek naya
entry add karo — baaki sab automatically kaam karega (index, pages, posting).

Environment variables (GitHub Secrets se aate hain):
- GEMINI_API_KEY        -> Google AI Studio se free API key
- FB_PAGE_ID / FB_PAGE_ACCESS_TOKEN  -> (optional) Facebook auto-posting
- TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID -> (optional) Telegram auto-posting
"""

import os
import sys
import json
import random
import time
from datetime import datetime
from google import genai
import requests

# ---------- SITE CONFIG ----------
SITE_TITLE = "Skill Academy — Daily Lessons"
SITE_TAGLINE = "✨ Har Roz Ek Naya Practical Lesson — Apni Pasand Ka Course Chuno"
SITE_URL = os.environ.get("SITE_URL", "https://example.github.io/skill-academy/")
TELEGRAM_CHANNEL_LINK = os.environ.get("TELEGRAM_CHANNEL_LINK", "https://t.me/YourChannel")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ---------- COURSES ----------
# Naya course add karna ho to bas ek naya entry yahan add kar dein.
# "topics" list mein jitne zyada items honge utna lamba cycle chalega
# (ek dafa sab topics cover hone ke baad dubara shuru ho jata hai).
COURSES = {
    "youtube-automation": {
        "name": "YouTube Automation",
        "icon": "🎬",
        "tagline": "Bina face show kiye YouTube channel banayein aur grow karein",
        "topics": [
            "YouTube Automation channel kaise start karein - complete roadmap",
            "Faceless YouTube channel ke liye niche kaise choose karein",
            "AI voiceover aur script se video kaise banayein",
            "YouTube SEO - title, tags aur description sahi kaise likhein",
            "Thumbnail design ke rules jo CTR barhate hain",
            "YouTube Monetization (AdSense) ke liye eligibility aur steps",
            "Video editing tools jo beginners free mein use kar sakte hain",
            "YouTube Shorts se channel ko fast grow kaise karein",
            "Copyright se bachne ke liye content sourcing ke sahi tareeke",
            "Consistency aur upload schedule kaise maintain karein",
        ],
    },
    "social-media-marketing": {
        "name": "Social Media Marketing",
        "icon": "📱",
        "tagline": "Brands aur businesses ke liye social media grow karna seekhein",
        "topics": [
            "Social Media Marketing kya hai aur beginners kahan se shuru karein",
            "Content calendar kaise banayein jo consistent posting yaqeeni banaye",
            "Instagram par organic reach barhane ke practical tarike",
            "Facebook Ads ka basic structure - campaign, ad set, ad",
            "Engaging captions aur hooks likhne ka formula",
            "Hashtag research sahi tarike se kaise karein",
            "Client ke liye social media report kaise banayein",
            "Reels aur short-form video trends ko kaise use karein",
            "Community management - comments aur DMs handle karna",
            "Personal brand banane ke 3 zaroori steps",
        ],
    },
    "ai-tools": {
        "name": "AI Tools & Automation",
        "icon": "🤖",
        "tagline": "Roz kaam aasan banane wale AI tools aur prompts seekhein",
        "topics": [
            "ChatGPT se roz ka kaam fast kaise karein - practical examples",
            "AI se content writing ke liye prompt engineering basics",
            "AI image generation tools (jaise Midjourney) ka istemal",
            "AI se video script aur voiceover kaise banayein",
            "No-code automation tools (Zapier/Make) ka basic use",
            "AI se resume aur cover letter kaise improve karein",
            "AI chatbot business mein kaise use hota hai",
            "Freelancers ke liye best AI productivity tools",
            "AI se data analysis aur Excel tasks fast karna",
            "AI tools use karte waqt privacy aur accuracy ka khayal",
        ],
    },
    "facebook-page-growth": {
        "name": "Facebook Page Growth",
        "icon": "👍",
        "tagline": "Apna Facebook Page organic tareeke se grow karein",
        "topics": [
            "Naya Facebook Page banate waqt zaroori settings",
            "Page ke liye pehle 1000 followers kaise laayein",
            "Facebook algorithm 2026 mein kis tarah ka content push karta hai",
            "Facebook Page insights padhna aur samajhna",
            "Engagement barhane wale post formats (poll, question, carousel)",
            "Facebook Groups se Page traffic kaise laayein",
            "Boost post vs proper Ads campaign - kab kya use karein",
            "Page ko monetize karne ke tareeke (In-stream ads, stars)",
            "Negative comments aur reviews handle karne ka sahi tareeka",
            "Consistent branding - cover photo, bio aur CTA button",
        ],
    },
    "amazon-fba": {
        "name": "Amazon FBA",
        "icon": "📦",
        "tagline": "Amazon par apna private label product bech na seekhein",
        "topics": [
            "Amazon FBA kya hai aur ye kaise kaam karta hai",
            "Product research kaise karein - winning product ke signs",
            "Supplier (Alibaba) se sample mangwane ka process",
            "Amazon listing optimize karna - title, bullet points, images",
            "FBA fees aur profit margin calculate kaise karein",
            "PPC ads se Amazon listing ko rank kaise karayein",
            "Inventory management aur restocking ki planning",
            "Amazon account suspension se bachne ke rules",
            "Reviews aur ratings improve karne ke tareeke",
            "Private label vs Wholesale vs Dropshipping - farq samjhein",
        ],
    },
    "daraz-seller": {
        "name": "Daraz Seller",
        "icon": "🛒",
        "tagline": "Pakistan ke sabse bade marketplace par seller banein",
        "topics": [
            "Daraz par seller account kaise banayein - step by step",
            "Winning product Daraz ke liye kaise dhoondein",
            "Daraz listing ke liye achi photos aur description",
            "Daraz Seller Center dashboard samajhna",
            "Pricing strategy jo competitors se better convert kare",
            "Daraz Ads (Sponsored) se sales kaise barhayein",
            "Order aur return process sahi tarike se handle karna",
            "Daraz performance metrics jo seller rating par asar dalte hain",
            "Local suppliers se product sourcing ke tips",
            "Daraz par seasonal sales (11.11, 12.12) ke liye tayari",
        ],
    },
    "dropshipping": {
        "name": "Dropshipping",
        "icon": "🚚",
        "tagline": "Bina inventory rakhe online store se product bechna seekhein",
        "topics": [
            "Dropshipping business model beginners ke liye explained",
            "Winning product research ke practical tarike",
            "Shopify store setup karne ka step-by-step guide",
            "Reliable supplier (AliExpress/local) kaise choose karein",
            "Facebook/TikTok Ads se dropshipping store par traffic laana",
            "Store ki conversion rate improve karne ke tips",
            "Customer service aur delivery delays handle karna",
            "Dropshipping mein profit margin sahi kaise calculate karein",
            "Branding se generic dropshipping store ko alag banana",
            "Common mistakes jo naye dropshippers karte hain",
        ],
    },
    "freelancing": {
        "name": "Freelancing",
        "icon": "💻",
        "tagline": "Fiverr, Upwork aur online kaam se ghar baithe kamayein",
        "topics": [
            "Freelancing shuru karne ke liye sahi skill kaise choose karein",
            "Fiverr par winning gig kaise banayein",
            "Upwork proposal likhne ka formula jo replies laata hai",
            "Client se sahi tarike se communicate karna",
            "Freelancing rates sahi tarike se set karna",
            "Pehla client kaise laayein - beginner strategy",
            "Portfolio banane ke liye bina experience ke bhi options",
            "Time management - multiple clients ek sath handle karna",
            "Payment safely receive karne ke tareeke Pakistan se",
            "Long-term client relationships kaise banayein",
        ],
    },
    "digital-marketing-seo": {
        "name": "Digital Marketing & SEO",
        "icon": "📊",
        "tagline": "Websites aur brands ko Google par rank karana seekhein",
        "topics": [
            "SEO kya hai aur ye kaam kaise karta hai - basics",
            "Keyword research free tools se kaise karein",
            "On-page SEO checklist - har blog post ke liye",
            "Backlinks kya hote hain aur inhe safely kaise banayein",
            "Google My Business se local business rank karana",
            "Email marketing se leads ko customer mein convert karna",
            "Google Ads ka basic campaign structure",
            "Website speed aur SEO ka taalluq",
            "Content marketing strategy jo organic traffic laaye",
            "Analytics (Google Analytics) padhna seekhein",
        ],
    },
    "graphic-design-canva": {
        "name": "Graphic Design (Canva)",
        "icon": "🎨",
        "tagline": "Bina design background ke professional graphics banayein",
        "topics": [
            "Canva ka interface aur zaroori tools samajhna",
            "Social media post design ke liye sahi size aur layout",
            "Color combinations jo professional lagti hain",
            "Fonts pairing ke basic design rules",
            "Logo design ke liye beginner-friendly tareeka",
            "Canva templates ko apne brand ke mutabiq customize karna",
            "Design se clients ke liye income kaise banayein",
            "Thumbnail aur banner design ke practical tips",
            "Free stock photos aur elements kahan se milte hain",
            "Design consistency - brand kit kaise banayein",
        ],
    },
}

DEFAULT_HASHTAGS = ["#SkillDevelopment", "#OnlineEarning", "#LearnOnline", "#Pakistan"]
BRAND_HASHTAGS = ["#SkillAcademy", "#DailyLesson"]

# ---------- SETUP GEMINI ----------
client = genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL = "gemini-flash-latest"


class QuotaExceededError(Exception):
    """Jab Gemini free-tier quota/rate-limit khatam ho jaye."""
    pass


def _is_quota_error(e):
    text = str(e).lower()
    return any(k in text for k in ["quota", "rate limit", "429", "resource_exhausted"])


def call_gemini(prompt, retries=3, delay=20):
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            return response.text.strip()
        except Exception as e:
            last_err = e
            if _is_quota_error(e):
                if attempt < retries:
                    print(f"⚠️ Quota/rate-limit hit (attempt {attempt}/{retries}), {delay}s baad retry karenge...")
                    time.sleep(delay)
                    continue
                raise QuotaExceededError(str(e)) from e
            raise
    raise QuotaExceededError(str(last_err)) from last_err


def pick_topic(course_slug, all_posts):
    topics = COURSES[course_slug]["topics"]
    course_posts = all_posts.get(course_slug, [])
    recent_used = [p.get("topic") for p in course_posts[-(len(topics) - 1):] if p.get("topic")]
    available = [t for t in topics if t not in recent_used]
    if not available:
        available = topics
    return random.choice(available)


def generate_content(topic, course_name):
    prompt = f"""
    Tum ek professional "{course_name}" mentor/instructor ho, jo daily step-by-step
    lessons deta hai apne students ko (jaise ek online academy mein).
    Aaj ka topic: "{topic}"

    Ek chota, modern aur engaging daily lesson likho (Roman Urdu/Hindi + English mix,
    jaisa online course communities mein likha jata hai). Requirements:
    - 250-350 words
    - Ek catchy heading do (pehli line, bina # ke) jisme relevant emoji ho, aur heading
      se clearly pata chale lesson mein kya milega
    - Content ko step-by-step ya bullet points mein likho (jaise Step 1, Step 2...) taake
      student practice kar sake
    - Har step/point ke shuru mein ek relevant emoji use karo
    - Beginner-friendly, practical aur actionable tone rakho
    - Ant mein ek short "Aaj ka practice task" line do jo student ko turant kuch karne ko kahe
    - Koi "guaranteed income" ya "overnight success" jaisa jhoota claim mat karo
    - Emojis natural lagne chahiye, overuse mat karo (max 1-2 per line)
    """
    return call_gemini(prompt)


def generate_hashtags(topic, course_name):
    prompt = f"""
    Topic: "{topic}" (Course: {course_name})
    Is online-course topic ke liye 6 relevant English hashtags do (jaise #Freelancing #OnlineEarning).
    Sirf hashtags do, koi extra text nahi, ek line mein space se separate karke.
    """
    tags = None
    try:
        text = call_gemini(prompt, retries=1)
        generated = [t for t in text.strip().split() if t.startswith("#")]
        if len(generated) >= 3:
            tags = generated
    except Exception:
        pass
    if tags is None:
        tags = DEFAULT_HASHTAGS

    final_tags = list(BRAND_HASHTAGS)
    for t in tags:
        if t not in final_tags:
            final_tags.append(t)
    return final_tags


def build_lesson_html(course_slug, title, body_text, date_str, slug, hashtags):
    course = COURSES[course_slug]
    paragraphs = "\n".join(f"<p>{line.strip()}</p>" for line in body_text.split("\n") if line.strip())
    hashtags_html = " ".join(f'<span class="hashtag">{h}</span>' for h in hashtags)
    hashtags_line = " ".join(hashtags)
    post_url = f"{SITE_URL.rstrip('/')}/courses/{course_slug}/posts/{slug}.html"

    share_text = (
        f"{title}\n\n"
        f"{body_text.strip()}\n\n"
        f"{hashtags_line}\n\n"
        f"📚 Course: {course['name']}\n"
        f"📖 Ye lesson yahan padhein: {post_url}\n\n"
        f"📢 Telegram Channel Join karein: {TELEGRAM_CHANNEL_LINK}"
    )
    share_text_json = json.dumps(share_text)
    post_url_json = json.dumps(post_url)

    return f"""<!DOCTYPE html>
<html lang="ur">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | {course['name']} | {SITE_TITLE}</title>
<link rel="stylesheet" href="../../style.css">
<link rel="stylesheet" href="../../courses.css">
</head>
<body>
<div class="container">
  <a href="../../index.html" class="back-link">&larr; Home</a>
  <a href="../index.html" class="back-link course-back-link">{course['icon']} {course['name']} ke saare lessons</a>
  <div class="post-card">
    <p class="course-tag">{course['icon']} {course['name']}</p>
    <h1>{title}</h1>
    <p class="date">📅 {date_str}</p>
    {paragraphs}
    <p class="hashtags">{hashtags_html}</p>
    <div class="share-box">
      <p class="share-label">📤 Is lesson ko share karein:</p>
      <div class="share-icons">
        <a href="#" class="share-icon share-whatsapp" onclick="shareWhatsapp(); return false;" aria-label="Share on WhatsApp">💬 WhatsApp</a>
        <a href="#" class="share-icon share-facebook" onclick="shareFacebook(); return false;" aria-label="Share on Facebook">📘 Facebook</a>
        <a href="#" class="share-icon share-telegram" onclick="shareTelegram(); return false;" aria-label="Share on Telegram">✈️ Telegram</a>
        <a href="#" class="share-icon share-instagram" onclick="shareInstagram(); return false;" aria-label="Share on Instagram">📸 Instagram</a>
        <button class="share-icon share-other" onclick="shareOther()" aria-label="Other share options">🔗 Other</button>
      </div>
      <span class="share-copied" id="shareCopied">Link copied! ✅</span>
    </div>
    <p class="disclaimer">⚠️ Ye lesson sirf educational purpose ke liye hai. Practice consistently karein, results waqt lete hain.</p>
  </div>
</div>
<script>
const shareText = {share_text_json};
const postUrl = {post_url_json};

function copyAndNotify() {{
  navigator.clipboard.writeText(shareText).then(() => {{
    const el = document.getElementById("shareCopied");
    el.classList.add("visible");
    setTimeout(() => el.classList.remove("visible"), 2500);
  }});
}}

function shareWhatsapp() {{
  window.open("https://wa.me/?text=" + encodeURIComponent(shareText), "_blank");
}}

function shareFacebook() {{
  copyAndNotify();
  window.open("https://www.facebook.com/sharer/sharer.php?u=" + encodeURIComponent(postUrl), "_blank");
}}

function shareTelegram() {{
  window.open("https://t.me/share/url?url=" + encodeURIComponent(postUrl) + "&text=" + encodeURIComponent(shareText), "_blank");
}}

function shareInstagram() {{
  copyAndNotify();
  window.open("https://www.instagram.com/", "_blank");
}}

function shareOther() {{
  const shareData = {{ title: document.title, text: shareText }};
  if (navigator.share) {{
    navigator.share(shareData).catch(() => {{}});
  }} else {{
    copyAndNotify();
  }}
}}
</script>
</body>
</html>"""


def update_course_index(course_slug, all_posts):
    course = COURSES[course_slug]
    posts = all_posts.get(course_slug, [])
    items = "\n".join(
        f'<li><a href="posts/{p["slug"]}.html">{course["icon"]} {p["title"]}</a><span class="date">{p["date"]}</span></li>'
        for p in reversed(posts)
    )
    html = f"""<!DOCTYPE html>
<html lang="ur">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{course['name']} | {SITE_TITLE}</title>
<link rel="stylesheet" href="../style.css">
<link rel="stylesheet" href="../courses.css">
</head>
<body>
<div class="container">
  <a href="../index.html" class="back-link">&larr; Home / Saare Courses</a>
  <h1>{course['icon']} {course['name']}</h1>
  <p class="subtitle">{course['tagline']}</p>
  <ul class="post-list">
  {items if items else '<li class="empty">Pehla lesson jald aa raha hai — kal 3 PM PKT par wapis check karein! 🙂</li>'}
  </ul>
</div>
</body>
</html>"""
    os.makedirs(f"courses/{course_slug}", exist_ok=True)
    with open(f"courses/{course_slug}/index.html", "w", encoding="utf-8") as f:
        f.write(html)


def update_home_index(all_posts):
    cards = []
    for slug, course in COURSES.items():
        posts = all_posts.get(slug, [])
        lesson_count = len(posts)
        latest = posts[-1]["title"] if posts else "Pehla lesson jald aa raha hai"
        cards.append(f"""
    <a class="course-card" href="courses/{slug}/index.html">
      <div class="course-card-icon">{course['icon']}</div>
      <div class="course-card-body">
        <h2>{course['name']}</h2>
        <p class="course-card-tagline">{course['tagline']}</p>
        <p class="course-card-latest">📖 {latest}</p>
        <p class="course-card-count">{lesson_count} daily lessons so far</p>
      </div>
      <div class="course-card-arrow">›</div>
    </a>""")

    html = f"""<!DOCTYPE html>
<html lang="ur">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{SITE_TITLE}</title>
<link rel="stylesheet" href="style.css">
<link rel="stylesheet" href="courses.css">
</head>
<body>
<div class="container">
  <h1>🎓 {SITE_TITLE}</h1>
  <p class="subtitle">{SITE_TAGLINE}</p>
  <p class="home-note">📅 Har course ka naya lesson roz <strong>3:00 PM Pakistan time</strong> par post hota hai. Jis course mein interest ho, us par tap karein!</p>
  <div class="course-grid">
  {''.join(cards)}
  </div>
  <p class="footer-note">📢 Updates ke liye Telegram Channel Join karein 👉 <a href="{TELEGRAM_CHANNEL_LINK}" target="_blank" rel="noopener">{TELEGRAM_CHANNEL_LINK}</a></p>
</div>
</body>
</html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)


def post_to_facebook(course, title, body_text, hashtags, post_url):
    if not FB_PAGE_ID or not FB_PAGE_ACCESS_TOKEN:
        return
    hashtags_line = " ".join(hashtags)
    message = (
        f"{course['icon']} {course['name']} — Daily Lesson\n\n"
        f"{title}\n\n"
        f"{body_text.strip()}\n\n"
        f"{hashtags_line}\n\n"
        f"📖 Poora lesson: {post_url}\n"
        f"📢 Telegram Channel: {TELEGRAM_CHANNEL_LINK}"
    )
    url = f"https://graph.facebook.com/v25.0/{FB_PAGE_ID}/feed"
    payload = {"message": message, "link": post_url, "access_token": FB_PAGE_ACCESS_TOKEN}
    try:
        response = requests.post(url, data=payload, timeout=30)
        data = response.json()
        if "id" in data:
            print(f"✅ Facebook pe post ho gaya ({course['name']}): {data['id']}")
        else:
            print(f"⚠️ Facebook post failed ({course['name']}): {data}")
    except Exception as e:
        print(f"⚠️ Facebook post error ({course['name']}): {e}")


def post_to_telegram(course, title, body_text, hashtags, post_url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    chat_ids = [c.strip() for c in TELEGRAM_CHAT_ID.split(",") if c.strip()]
    hashtags_line = " ".join(hashtags)
    message = (
        f"{course['icon']} {course['name']} — Daily Lesson\n\n"
        f"{title}\n\n"
        f"{body_text.strip()}\n\n"
        f"{hashtags_line}\n\n"
        f"📖 Poora lesson: {post_url}\n"
        f"📢 Channel Share karein 👉 {TELEGRAM_CHANNEL_LINK}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for chat_id in chat_ids:
        payload = {"chat_id": chat_id, "text": message, "disable_web_page_preview": False}
        try:
            response = requests.post(url, data=payload, timeout=30)
            data = response.json()
            if data.get("ok"):
                print(f"✅ Telegram ({chat_id}) pe post ho gaya ({course['name']})")
            else:
                print(f"⚠️ Telegram post failed ({chat_id}, {course['name']}): {data}")
        except Exception as e:
            print(f"⚠️ Telegram post error ({chat_id}, {course['name']}): {e}")


def load_posts(posts_file):
    if os.path.exists(posts_file):
        with open(posts_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_posts(posts_file, all_posts):
    with open(posts_file, "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)


def generate_lesson_for_course(course_slug, all_posts):
    course = COURSES[course_slug]
    topic = pick_topic(course_slug, all_posts)
    print(f"➡️ {course['icon']} {course['name']}: topic = {topic}")

    try:
        content = generate_content(topic, course["name"])
    except QuotaExceededError as e:
        print(f"⚠️ Gemini quota khatam ho gaya - {course['name']} ka lesson skip kiya. Details: {e}")
        return

    hashtags = generate_hashtags(topic, course["name"])
    lines = content.split("\n")
    title = lines[0].strip().lstrip("#").strip()
    body = "\n".join(lines[1:]).strip()

    today = datetime.now()
    date_str = today.strftime("%d-%m-%Y")
    slug = today.strftime("%Y-%m-%d") + "-" + str(random.randint(100, 999))

    lesson_html = build_lesson_html(course_slug, title, body, date_str, slug, hashtags)
    os.makedirs(f"courses/{course_slug}/posts", exist_ok=True)
    with open(f"courses/{course_slug}/posts/{slug}.html", "w", encoding="utf-8") as f:
        f.write(lesson_html)

    all_posts.setdefault(course_slug, []).append(
        {"title": title, "date": date_str, "slug": slug, "hashtags": hashtags, "topic": topic}
    )

    update_course_index(course_slug, all_posts)

    post_url = f"{SITE_URL.rstrip('/')}/courses/{course_slug}/posts/{slug}.html"
    post_to_facebook(course, title, body, hashtags, post_url)
    post_to_telegram(course, title, body, hashtags, post_url)

    print(f"✅ Lesson ban gaya: [{course['name']}] {title}")


def main():
    posts_file = "posts.json"
    all_posts = load_posts(posts_file)

    for course_slug in COURSES:
        generate_lesson_for_course(course_slug, all_posts)
        save_posts(posts_file, all_posts)  # har course ke baad save, taake partial failure pe data na khoye

    update_home_index(all_posts)
    print("🎉 Aaj ke saare course lessons taiyar ho gaye!")


if __name__ == "__main__":
    main()
