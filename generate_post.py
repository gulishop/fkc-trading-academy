#!/usr/bin/env python3
"""
Skill Academy — Multi-Course Daily Lesson Generator.

Har din (GitHub Action se, 3:00 PM Pakistan time par) yeh script chalta
hai aur COURSES dictionary mein diye gaye HAR course ke liye us course
ka "agla" daily lesson generate karta hai (Gemini AI se, agar lessons/
mein file pehle se maujood nahi), phir poori site (docs/) dobara
banata hai:

  docs/index.html                              -> home page, course cards
  docs/courses/<slug>/index.html                -> us course ke sab lessons
  docs/courses/<slug>/posts/<date>-day-XX.html  -> ek individual lesson,
                                                    Share buttons ke sath
  posts.json                                    -> har course ki history
                                                    (source of truth)
  lessons/<slug>/day-XX.md                      -> raw lesson text (aap
                                                    khud bhi yahan file
                                                    daal kar Gemini ko
                                                    us din ke liye skip
                                                    kar sakte hain)

Naya course add karna ho to bas COURSES dictionary mein ek entry add
kar dein — baaki sab khud ban jayega.

Usage (GitHub Action isay khud chalata hai):
    python generate_post.py

Sirf EK course generate karna ho (alag scheduled runs ke liye), COURSE_SLUG
environment variable set karein ya slug ko pehle argument ke tor par dein:
    COURSE_SLUG=amazon-fba python generate_post.py
    python generate_post.py amazon-fba

Is case mein sirf usi course ka lesson generate + rebuild hota hai, lekin
docs/index.html (home page) hamesha SAB courses ke latest data se dobara
banta hai — is liye home page kabhi purana nahi rehta.
"""
import os
import re
import sys
import time
import json
import html
import datetime
import urllib.request
import urllib.parse
import urllib.error

# ---------------------------------------------------------------------
# 1. COURSES — yahan naya course add/hata/edit karein
# ---------------------------------------------------------------------
COURSES = {
    "youtube-automation": {
        "name": "YouTube Automation",
        "icon": "🎬",
        "tagline": "Bina face show kiye YouTube channel banayein aur grow karein",
        "topics": [
            "Niche select karna aur channel setup",
            "Script likhna AI se",
            "Faceless video banane ke tools (CapCut, Pictory, etc.)",
            "Voiceover aur background music",
            "Thumbnail aur title jo click karwaye",
            "YouTube SEO aur tags",
            "Monetization (AdSense) ke rules",
            "Upload schedule aur consistency",
            "Analytics padhna aur improve karna",
            "Channel ko scale karna / team banana",
        ],
    },
    "social-media-marketing": {
        "name": "Social Media Marketing",
        "icon": "📱",
        "tagline": "Brands aur businesses ke liye social media grow karna seekhein",
        "topics": [
            "Social media strategy banana",
            "Content calendar planning",
            "Reels/Shorts jo viral hon",
            "Instagram growth tactics",
            "Engagement aur community building",
            "Paid ads basics (Meta Ads Manager)",
            "Influencer collaborations",
            "Analytics aur reporting client ko",
            "Client dhoondna aur pitch karna",
            "Ek chhoti agency shuru karna",
        ],
    },
    "ai-tools": {
        "name": "AI Tools & Automation",
        "icon": "🤖",
        "tagline": "Roz kaam aasan banane wale AI tools aur automation seekhein",
        "topics": [
            "ChatGPT/Gemini se prompt likhna (prompt engineering basics)",
            "AI se content, captions, aur emails likhwana",
            "AI image generation (Midjourney/Ideogram)",
            "AI video tools",
            "No-code automation (Zapier/Make) se workflows",
            "AI chatbot banana business ke liye",
            "AI se data/Excel kaam automate karna",
            "AI tools bech kar service dena (freelance AI agency)",
            "Latest AI tools jo naye aa rahe hain",
            "AI ko responsibly aur safely use karna",
        ],
    },
    "facebook-page-growth": {
        "name": "Facebook Page Growth",
        "icon": "👍",
        "tagline": "Facebook Page se organic reach aur sales badhana seekhein",
        "topics": [
            "Facebook Page professional setup karna",
            "Content jo Facebook par chalta hai",
            "Reels aur video content",
            "Groups se traffic lana",
            "Facebook Ads basics",
            "Messenger se sales close karna",
            "Facebook Marketplace se bechna",
            "Page ko monetize karna",
            "Fake/copyright issues se bachna",
            "Page ko brand mein badalna",
        ],
    },
    "amazon-fba": {
        "name": "Amazon FBA",
        "icon": "📦",
        "tagline": "Amazon par apna private-label product bech kar business banayein",
        "topics": [
            "Amazon FBA model samajhna",
            "Product research (demand, competition, margin)",
            "Supplier dhoondna (Alibaba)",
            "Sample order aur quality check",
            "Amazon seller account banana",
            "Listing banana (title, bullet points, images)",
            "FBA shipment bhejna",
            "PPC ads chalana",
            "Reviews aur ranking badhana",
            "Numbers/profit track karna",
        ],
    },
    "daraz-seller": {
        "name": "Daraz Seller",
        "icon": "🛒",
        "tagline": "Pakistan ke sabse bade marketplace par apni dukaan banayein",
        "topics": [
            "Daraz Seller Center account banana",
            "Product research Pakistan market ke liye",
            "Listing aur pricing strategy",
            "Product photos jo bikte hain",
            "Daraz Ads (Sponsored Discovery)",
            "Orders aur delivery (Daraz Express/Dropship)",
            "Rating aur reviews manage karna",
            "Vouchers aur campaigns mein hissa lena",
            "Return/refund handle karna",
            "Store ko monthly scale karna",
        ],
    },
    "dropshipping": {
        "name": "Dropshipping",
        "icon": "🚚",
        "tagline": "Bina stock rakhe online store se products bechna seekhein",
        "topics": [
            "Dropshipping model samajhna",
            "Winning product dhoondna",
            "Supplier dhoondna (local ya AliExpress)",
            "Shopify/WhatsApp store banana",
            "Product page jo convert kare",
            "Facebook/TikTok ads se traffic lana",
            "Cash on delivery orders handle karna (Pakistan)",
            "Customer support aur trust banana",
            "Return/refund policy",
            "Store ko scale karna",
        ],
    },
    "freelancing": {
        "name": "Freelancing",
        "icon": "💼",
        "tagline": "Fiverr, Upwork jaisi platforms se ghar baithe kamana seekhein",
        "topics": [
            "Sahi skill choose karna",
            "Fiverr/Upwork profile banana jo client ko impress kare",
            "Winning gig/proposal likhna",
            "Portfolio banana bina experience ke",
            "Client se communication",
            "Pricing aur negotiation",
            "Pehla order lena",
            "5-star review lena",
            "Multiple platforms par expand karna",
            "Freelancing se agency tak jana",
        ],
    },
    "digital-marketing-seo": {
        "name": "Digital Marketing & SEO",
        "icon": "📈",
        "tagline": "Websites aur brands ko Google par rank karwana seekhein",
        "topics": [
            "Digital marketing ka poora landscape",
            "SEO basics (keywords, on-page)",
            "Google search console aur analytics",
            "Content marketing strategy",
            "Email marketing basics",
            "Google Ads basics",
            "Local SEO (Google Business Profile)",
            "Backlinks aur off-page SEO",
            "SEO client kaise dhoondein",
            "Ek chhota SEO audit khud karna",
        ],
    },
    "graphic-design-canva": {
        "name": "Graphic Design (Canva)",
        "icon": "🎨",
        "tagline": "Bina design background ke professional graphics banayein",
        "topics": [
            "Canva interface aur basics",
            "Color aur font combinations",
            "Social media post templates",
            "Logo aur brand kit banana",
            "Thumbnail aur banner design",
            "Presentation/pitch deck design",
            "Mockups aur product design",
            "AI tools Canva ke andar",
            "Design bech kar paisa kamana (Fiverr/Etsy)",
            "Apna design portfolio banana",
        ],
    },
    "ai-content-writing": {
        "name": "AI Content Writing & Copywriting",
        "icon": "✍️",
        "tagline": "AI ki madad se paisa kamane wala content aur copy likhein",
        "topics": [
            "Copywriting ke basics (hook, benefit, CTA)",
            "AI se blog articles likhwana aur edit karna",
            "Social captions aur ad copy",
            "Sales page/landing page copy",
            "Email sequences likhna",
            "SEO content likhna",
            "Apni writing ko AI se better banana",
            "Content writing gigs dhoondna",
            "Ek content writing portfolio banana",
            "Content agency ka idea",
        ],
    },
    "video-editing": {
        "name": "Video Editing (CapCut/Premiere)",
        "icon": "🎞️",
        "tagline": "Reels se le kar YouTube tak — video editing ek in-demand skill",
        "topics": [
            "CapCut/Premiere interface basics",
            "Cutting aur pacing jo attention rakhe",
            "Captions/subtitles add karna",
            "Transitions aur effects",
            "Color grading basics",
            "Sound design aur music sync",
            "Short-form (Reels/Shorts) editing style",
            "Long-form YouTube editing style",
            "Export settings har platform ke liye",
            "Editing services bech kar kamana",
        ],
    },
    "affiliate-marketing": {
        "name": "Affiliate Marketing",
        "icon": "🔗",
        "tagline": "Doosron ke products promote kar ke commission kamayein",
        "topics": [
            "Affiliate marketing model samajhna",
            "Sahi niche aur platform choose karna",
            "Amazon Associates / Daraz Affiliate program",
            "Content banana jo bikri karwaye",
            "Link placement aur disclosure",
            "Social media se affiliate traffic",
            "Email list se affiliate sales",
            "Tracking aur analytics",
            "Multiple income sources banana",
            "Long-term affiliate brand banana",
        ],
    },
    "print-on-demand": {
        "name": "Print on Demand",
        "icon": "👕",
        "tagline": "Apni design se t-shirts/mugs bech kar bina inventory ke kamayein",
        "topics": [
            "Print on demand model samajhna",
            "Platform choose karna (Printful/local vendors)",
            "Design ideas aur trends dhoondna",
            "Canva/AI se designs banana",
            "Mockups banana",
            "Store setup karna",
            "Marketing (social/ads)",
            "Pricing aur profit margin",
            "Orders aur quality control",
            "Store ko scale karna",
        ],
    },
    "no-code-app-dev": {
        "name": "No-Code App & Website Building",
        "icon": "🧩",
        "tagline": "Bina coding seekhe apps aur websites banana seekhein",
        "topics": [
            "No-code kya hai aur kyun demand mein hai",
            "Website builders (Framer/Webflow/Wix)",
            "App builders (FlutterFlow/Glide)",
            "Database aur automation (Airtable/Notion)",
            "AI se no-code development",
            "Client project ka basic structure",
            "MVP banana startup idea ke liye",
            "No-code se freelancing",
            "Hosting aur domain basics",
            "No-code ki limitations samajhna",
        ],
    },
}

BRAND_NAME = "FKC Trading Academy"
BRAND_LOGO = "logo.png"  # docs/logo.png — repo mein khud upload karein
BRAND_CONTACT_NAME = "Fazul Khan Chandio"
BRAND_CONTACT_TITLE = "Director / CEO"
BRAND_CONTACT_PHONE = "+92 333 3909816"
BRAND_LINE = f"{BRAND_CONTACT_NAME} — {BRAND_CONTACT_TITLE} — {BRAND_CONTACT_PHONE}"

SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
TELEGRAM_CHANNEL_LINK = os.environ.get("TELEGRAM_CHANNEL_LINK", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "")
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")

POSTS_JSON = "posts.json"
LESSONS_DIR = "lessons"
DOCS_DIR = "docs"

ACCENTS = ["#D4A73A", "#3FB68B", "#5B8DEF", "#E2574C", "#9B6BD8", "#2FB6C4"]


# ---------------------------------------------------------------------
# 2. Helpers — posts.json load/save
# ---------------------------------------------------------------------
def load_posts():
    if os.path.exists(POSTS_JSON):
        with open(POSTS_JSON, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_posts(posts):
    with open(POSTS_JSON, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------
# 3. Lesson content — Gemini generate ya manual file parhein
# ---------------------------------------------------------------------
def gemini_generate(prompt_text, max_retries=5):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY set nahi hai.")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    )
    body = json.dumps({"contents": [{"parts": [{"text": prompt_text}]}]}).encode()

    wait = 20
    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < max_retries:
                print(f"Gemini {e.code} mila (attempt {attempt}) — {wait}s ruk kar dobara koshish...", file=sys.stderr)
                time.sleep(wait)
                wait = min(wait * 2, 120)
                continue
            raise
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        print("Gemini response se text nahi mila:", data, file=sys.stderr)
        return ""


def build_prompt(slug, course, day_num, previous_titles):
    topics = course["topics"]
    topic_hint = topics[(day_num - 1) % len(topics)]
    prev = "; ".join(previous_titles[-6:]) if previous_titles else "(koi nahi, yeh pehla lesson hai)"
    return (
        f"Tum '{course['name']}' course ke ek teacher ho, Roman Urdu/Hindi mein "
        f"beginner-to-intermediate students ke liye. Yeh course ka Day {day_num} hai. "
        f"Poora curriculum yeh topics cover karta hai (order mein): {', '.join(topics)}. "
        f"Aaj ka focus topic: '{topic_hint}' — lekin agar pichle lessons already isse "
        f"cover kar chuke hain to agla logical topic khud choose kar lo aur curriculum se "
        f"aage badhte raho, kabhi mat rukna (curriculum khatam ho jaye to isi field ke "
        f"advanced/trending topics par khud aage likhte raho). "
        f"Pichle lessons ke titles (dobara mat likhna): {prev}. "
        "Format bilkul yeh follow karo, aur kuch mat likho: "
        f"'# Day {day_num} — <chhota, clear title>' phir "
        "'**Concept:**' (2-3 lines mein aaj ka topic samjhao), "
        "'**Example:**' (ek practical/real misal ya chhota step-by-step tarika), "
        "'**Practice:**' (1 kaam jo student abhi khud kare), "
        "'**Mini Project:**' (agar is topic ke liye banta ho to 1 chhota project, warna skip kar do), "
        "'**Answer Key:**' (Practice ka result represent karne wale 2-4 chhote keywords, comma se separate — sirf checking ke liye, student ko show nahi hoga). "
        "Total length chhoti rakho (max ~350 words), practical aur step-by-step, koi extra intro/outro nahi."
    )


def parse_lesson_text(text, day_num):
    lines = text.strip("\n").split("\n")
    title = f"Day {day_num}"
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            title = line.strip().lstrip("#").strip()
            body_start = i + 1
            break
    rest = "\n".join(lines[body_start:]).strip()

    pattern = re.compile(r"\*\*([^*\n]+):\*\*")
    parts = pattern.split(rest)
    preamble = parts[0].strip()

    sections = []
    for i in range(1, len(parts), 2):
        label = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections.append([label, content])

    answer_key = ""
    kept_sections = []
    for label, content in sections:
        if "answer key" in label.lower():
            answer_key = ", ".join(k.strip().lower() for k in content.split(",") if k.strip())
        else:
            kept_sections.append([label, content])

    return title, preamble, kept_sections, answer_key


def get_or_generate_lesson(slug, course, day_num, previous_titles):
    padded = f"{day_num:03d}"
    course_lessons_dir = os.path.join(LESSONS_DIR, slug)
    os.makedirs(course_lessons_dir, exist_ok=True)
    md_path = os.path.join(course_lessons_dir, f"day-{padded}.md")

    if os.path.exists(md_path):
        print(f"[{slug}] Pehle se likhi hui file mil gayi: {md_path}")
        with open(md_path, encoding="utf-8") as f:
            raw = f.read()
    else:
        print(f"[{slug}] Day {day_num} Gemini se generate ho raha hai...")
        prompt = build_prompt(slug, course, day_num, previous_titles)
        try:
            raw = gemini_generate(prompt)
        except Exception as e:
            print(f"[{slug}] Gemini call fail ho gayi, aaj yeh course skip: {e}", file=sys.stderr)
            return None
        if not raw:
            print(f"[{slug}] Gemini se lesson nahi mila, aaj skip.", file=sys.stderr)
            return None
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(raw)
        time.sleep(5)  # free-tier per-minute rate limit se bachne ke liye

    title, preamble, sections, answer_key = parse_lesson_text(raw, day_num)
    today = datetime.date.today().isoformat()
    return {
        "day": day_num,
        "id": f"day-{padded}",
        "date": today,
        "title": title,
        "preamble": preamble,
        "sections": sections,
        "answer_key": answer_key,
    }


# ---------------------------------------------------------------------
# 4. HTML rendering — shared style
# ---------------------------------------------------------------------
BASE_CSS = """
:root{--ink:#EDECE4;--paper:#0B1220;--panel:#111a2b;--line:#22304a;
--gold:#D4A73A;--green:#3FB68B;--muted:#93a0b8;}
*{box-sizing:border-box;}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:'IBM Plex Mono',monospace;line-height:1.6;}
.wrap{max-width:760px;margin:0 auto;padding:28px 18px 70px;}
a{color:var(--gold);}
.top{display:flex;align-items:baseline;gap:10px;color:var(--gold);
letter-spacing:.06em;font-size:14px;border-bottom:1px solid var(--line);
padding-bottom:14px;margin-bottom:22px;}
.top .lbl{color:var(--muted);font-weight:400;}
h1{font-family:'Fraunces',serif;font-size:1.6em;margin:.2em 0;}
h2{font-family:'Fraunces',serif;font-size:1.25em;margin:1em 0 .4em;}
h3{color:var(--gold);font-size:1em;margin:1.2em 0 .3em;}
p{margin:.4em 0;}
.muted{color:var(--muted);font-size:.9em;}
.card{background:var(--panel);border:1px solid var(--line);
border-radius:10px;padding:18px;margin:16px 0;}
.btn{display:inline-flex;align-items:center;gap:8px;background:var(--gold);
color:#0B1220;font-weight:600;font-size:14px;text-decoration:none;
padding:11px 16px;border:none;border-radius:6px;cursor:pointer;
margin:6px 6px 0 0;}
.btn.alt{background:var(--panel);color:var(--ink);border:1px solid var(--line);}
.btn.green{background:var(--green);}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
gap:14px;margin:18px 0 30px;}
.ccard{display:flex;align-items:center;gap:14px;background:var(--panel);
border:1px solid var(--line);border-left:4px solid var(--gold);
border-radius:12px;padding:16px;text-decoration:none;color:inherit;}
.ccard:hover{border-color:var(--gold);}
.ccard .icon{font-size:1.8em;width:50px;height:50px;flex-shrink:0;
display:flex;align-items:center;justify-content:center;
background:rgba(212,167,58,.12);border-radius:12px;}
.ccard .body{flex:1;min-width:0;}
.ccard .body h2{margin:0 0 3px;font-size:1.05em;}
.ccard .tag{font-size:.82em;color:var(--muted);margin:0 0 4px;}
.ccard .latest{font-size:.8em;margin:0;overflow:hidden;text-overflow:ellipsis;
white-space:nowrap;}
.ccard .arrow{font-size:1.5em;color:var(--muted);}
.plist a{display:block;background:var(--panel);border:1px solid var(--line);
border-radius:8px;padding:12px 14px;margin:8px 0;text-decoration:none;
color:var(--ink);}
.plist a:hover{border-color:var(--gold);}
.plist .d{color:var(--gold);font-size:.85em;margin-right:8px;}
.badge{display:inline-block;background:var(--gold);color:#0B1220;
font-size:.72em;font-weight:700;padding:2px 8px;border-radius:20px;
margin-bottom:8px;}
footer{color:var(--muted);font-size:12px;margin-top:40px;text-align:center;}
.brand-bar{display:flex;align-items:center;gap:12px;margin-bottom:18px;}
.brand-bar img{width:52px;height:52px;border-radius:50%;flex-shrink:0;
border:1px solid var(--line);}
.brand-bar .bname{font-family:'Fraunces',serif;font-weight:700;
color:var(--gold);font-size:1.15em;line-height:1.2;}
.brand-bar .btag{color:var(--muted);font-size:.82em;}
.brand-footer{border-top:1px solid var(--line);margin-top:34px;
padding-top:16px;display:flex;align-items:center;gap:12px;}
.brand-footer img{width:38px;height:38px;border-radius:50%;flex-shrink:0;}
.brand-footer .txt{font-size:.82em;color:var(--muted);line-height:1.5;}
.brand-footer .txt b{color:var(--ink);}
"""

HEAD = """<!DOCTYPE html>
<html lang="ur"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta property="og:title" content="{title}">
<meta property="og:description" content="{ogdesc}">
<meta property="og:image" content="{ogimage}">
<meta name="twitter:card" content="summary_large_image">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5639688573760714" crossorigin="anonymous"></script>
<link rel="icon" href="{logo_href}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{css}</style></head><body><div class="wrap">
<div class="brand-bar"><img src="{logo_href}" alt="{brand}">
<div><div class="bname">{brand}</div><div class="btag">Learn · Earn · Grow</div></div></div>
"""


def brand_footer_html(logo_href):
    privacy_href = logo_href.replace(BRAND_LOGO, "privacy.html")
    return (
        f'<div class="brand-footer"><img src="{logo_href}" alt="{BRAND_NAME}">'
        f'<div class="txt"><b>{html.escape(BRAND_NAME)}</b><br>'
        f'{html.escape(BRAND_LINE)}<br>'
        f'<a href="{privacy_href}">Privacy Policy</a></div></div>'
    )


FOOT_TAIL = "</div><footer>Skill Academy — daily lessons, automatically updated</footer></body></html>"


def md_lite(text):
    if not text:
        return ""
    return "".join(f"<p>{html.escape(p).replace(chr(10), '<br>')}</p>" for p in text.strip().split("\n\n") if p.strip())


def render_home(posts):
    cards = []
    for i, (slug, course) in enumerate(COURSES.items()):
        lessons = posts.get(slug, [])
        count = len(lessons)
        latest = lessons[-1]["title"] if lessons else "Pehla lesson jald aa raha hai"
        accent = ACCENTS[i % len(ACCENTS)]
        cards.append(f"""
    <a class="ccard" style="border-left-color:{accent}" href="courses/{slug}/index.html">
      <div class="icon">{course['icon']}</div>
      <div class="body">
        <h2>{html.escape(course['name'])}</h2>
        <p class="tag">{html.escape(course['tagline'])}</p>
        <p class="latest">📖 {html.escape(latest)}</p>
        <p class="muted">{count} daily lesson{'s' if count != 1 else ''} so far</p>
      </div>
      <div class="arrow">›</div>
    </a>""")

    logo_href = BRAND_LOGO
    body = f"""
    <div class="top"><span style="color:var(--gold);font-weight:700">{html.escape(BRAND_NAME)}</span>
    <span class="lbl">Digital Hub — apni pasand ka course chunein</span></div>
    <h1>🎓 Roz ek naya practical lesson</h1>
    <p class="muted">📅 Har course ka naya lesson roz <b>3:00 PM Pakistan time</b> par yahan post hota hai.
    Jis course mein interest ho us par tap karein — daily lesson step-by-step parhein aur practice karein.</p>
    <div class="grid">{''.join(cards)}</div>
    {brand_footer_html(logo_href)}
    """
    og_image = f"{SITE_URL}/{BRAND_LOGO}" if SITE_URL else BRAND_LOGO
    head = HEAD.format(
        title=f"{BRAND_NAME} — Daily Lessons",
        ogdesc="Har course ka daily lesson, step-by-step. Learn · Earn · Grow.",
        ogimage=og_image,
        logo_href=logo_href,
        brand=html.escape(BRAND_NAME),
        css=BASE_CSS,
    )
    return head + body + FOOT_TAIL


def render_course_page(slug, course, lessons):
    items = []
    for lesson in reversed(lessons):
        items.append(
            f'<a href="posts/{lesson["date"]}-{lesson["id"]}.html">'
            f'<span class="d">Day {lesson["day"]:02d}</span>{html.escape(lesson["title"])}</a>'
        )
    listing = "".join(items) if items else '<p class="muted">Abhi koi lesson nahi — pehla jald aayega.</p>'

    logo_href = f"../../{BRAND_LOGO}"
    body = f"""
    <div class="top"><a href="../../index.html">← {html.escape(BRAND_NAME)}</a></div>
    <h1>{course['icon']} {html.escape(course['name'])}</h1>
    <p class="muted">{html.escape(course['tagline'])}</p>
    <p class="muted">📅 Naya lesson roz 3:00 PM Pakistan time par yahan add hota hai.</p>
    <div class="plist">{listing}</div>
    {brand_footer_html(logo_href)}
    """
    og_image = f"{SITE_URL}/{BRAND_LOGO}" if SITE_URL else logo_href
    head = HEAD.format(
        title=f"{course['name']} — {BRAND_NAME}",
        ogdesc=course["tagline"],
        ogimage=og_image,
        logo_href=logo_href,
        brand=html.escape(BRAND_NAME),
        css=BASE_CSS,
    )
    return head + body + FOOT_TAIL


def render_lesson_page(slug, course, lesson, is_latest):
    lesson_html = md_lite(lesson["preamble"])
    for label, content in lesson["sections"]:
        lesson_html += f"<h3>{html.escape(label)}</h3>{md_lite(content)}"

    share_chunks = [f"📚 {BRAND_NAME} — {course['name']} (Day {lesson['day']:02d})", lesson["title"]]
    if lesson["preamble"]:
        share_chunks.append(lesson["preamble"])
    for label, content in lesson["sections"]:
        share_chunks.append(f"{label}:\n{content}")
    share_chunks.append(f"— {BRAND_LINE}")
    share_text = "\n\n".join(share_chunks)
    if SITE_URL:
        share_text += f"\n\n{SITE_URL}/courses/{slug}/posts/{lesson['date']}-{lesson['id']}.html"
    wa_link = f"https://wa.me/?text={urllib.parse.quote(share_text)}"
    fb_link = f"https://www.facebook.com/sharer/sharer.php?u={urllib.parse.quote(SITE_URL or '')}"
    tg_link = f"https://t.me/share/url?url={urllib.parse.quote(SITE_URL or '')}&text={urllib.parse.quote(lesson['title'] + ' — ' + BRAND_NAME)}"

    badge = '<span class="badge">Latest</span>' if is_latest else ""
    logo_href = f"../../../{BRAND_LOGO}"

    body = f"""
    <div class="top"><a href="../../../index.html">← {html.escape(BRAND_NAME)}</a>
    <a href="../index.html" class="course-back-link">/ {html.escape(course['name'])}</a></div>
    {badge}
    <p class="muted">{course['icon']} {html.escape(course['name'])} · Day {lesson['day']:02d}</p>
    <h1>{html.escape(lesson['title'])}</h1>
    <div class="card">
      {lesson_html}
      <div>
        <a class="btn" href="{wa_link}" target="_blank" rel="noopener">📲 WhatsApp par Share karein</a>
        <a class="btn alt" href="{tg_link}" target="_blank" rel="noopener">✈️ Telegram par Share karein</a>
        <a class="btn alt" href="{fb_link}" target="_blank" rel="noopener">📘 Facebook par Share karein</a>
      </div>
    </div>
    {brand_footer_html(logo_href)}
    """
    og_image = f"{SITE_URL}/{BRAND_LOGO}" if SITE_URL else logo_href
    head = HEAD.format(
        title=f"{lesson['title']} — {course['name']}",
        ogdesc=f"{BRAND_NAME} · {course['name']} · Day {lesson['day']:02d}",
        ogimage=og_image,
        logo_href=logo_href,
        brand=html.escape(BRAND_NAME),
        css=BASE_CSS,
    )
    return head + body + FOOT_TAIL


# ---------------------------------------------------------------------
# 5. Optional posting — Telegram + Facebook (best-effort, silent fail)
# ---------------------------------------------------------------------
def post_to_telegram(course, lesson):
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        return
    text = (
        f"📚 {BRAND_NAME}\n{course['icon']} {course['name']} — Day {lesson['day']:02d}\n\n"
        f"{lesson['title']}\n\n{lesson['preamble']}\n\n— {BRAND_LINE}"
    )
    logo_url = f"{SITE_URL}/{BRAND_LOGO}" if SITE_URL else ""
    try:
        if logo_url:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            data = urllib.parse.urlencode(
                {"chat_id": TELEGRAM_CHAT_ID, "photo": logo_url, "caption": text[:1024]}
            ).encode()
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = urllib.parse.urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": text}).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=20)
    except Exception as e:
        print(f"Telegram post fail ({course['name']}): {e}", file=sys.stderr)


def post_to_facebook(course, lesson):
    if not (FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN):
        return
    text = (
        f"📚 {BRAND_NAME}\n{course['icon']} {course['name']} — Day {lesson['day']:02d}\n\n"
        f"{lesson['title']}\n\n{lesson['preamble']}\n\n— {BRAND_LINE}"
    )
    logo_url = f"{SITE_URL}/{BRAND_LOGO}" if SITE_URL else ""
    try:
        if logo_url:
            url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
            data = urllib.parse.urlencode(
                {"url": logo_url, "caption": text, "access_token": FB_PAGE_ACCESS_TOKEN}
            ).encode()
        else:
            url = f"https://graph.facebook.com/{FB_PAGE_ID}/feed"
            data = urllib.parse.urlencode({"message": text, "access_token": FB_PAGE_ACCESS_TOKEN}).encode()
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=20)
    except Exception as e:
        print(f"Facebook post fail ({course['name']}): {e}", file=sys.stderr)


# ---------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------
def main():
    posts = load_posts()

    # Sirf ek course chalana ho to COURSE_SLUG env var ya CLI arg se slug lein.
    target_slug = os.environ.get("COURSE_SLUG") or (sys.argv[1] if len(sys.argv) > 1 else None)
    if target_slug:
        if target_slug not in COURSES:
            print(f"Course slug '{target_slug}' COURSES dictionary mein nahi mila.", file=sys.stderr)
            sys.exit(1)
        courses_to_run = {target_slug: COURSES[target_slug]}
    else:
        courses_to_run = COURSES

    for slug, course in courses_to_run.items():
        existing = posts.get(slug, [])
        next_day = len(existing) + 1
        previous_titles = [l["title"] for l in existing]

        lesson = get_or_generate_lesson(slug, course, next_day, previous_titles)
        if lesson is None:
            continue

        existing.append(lesson)
        posts[slug] = existing

        post_to_telegram(course, lesson)
        post_to_facebook(course, lesson)

        os.makedirs(os.path.join(DOCS_DIR, "courses", slug, "posts"), exist_ok=True)
        page = render_lesson_page(slug, course, lesson, is_latest=True)
        with open(
            os.path.join(DOCS_DIR, "courses", slug, "posts", f"{lesson['date']}-{lesson['id']}.html"),
            "w", encoding="utf-8",
        ) as f:
            f.write(page)

    save_posts(posts)

    # rebuild course pages (sirf jo is run mein chalay) + home page (hamesha
    # full posts.json se, taake home page sab courses ke sath up-to-date rahe)
    for slug, course in courses_to_run.items():
        lessons = posts.get(slug, [])
        os.makedirs(os.path.join(DOCS_DIR, "courses", slug), exist_ok=True)
        with open(os.path.join(DOCS_DIR, "courses", slug, "index.html"), "w", encoding="utf-8") as f:
            f.write(render_course_page(slug, course, lessons))
        # re-render every lesson page so only the newest carries "Latest"
        for i, lesson in enumerate(lessons):
            page = render_lesson_page(slug, course, lesson, is_latest=(i == len(lessons) - 1))
            with open(
                os.path.join(DOCS_DIR, "courses", slug, "posts", f"{lesson['date']}-{lesson['id']}.html"),
                "w", encoding="utf-8",
            ) as f:
                f.write(page)

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_home(posts))

    print("Done — site docs/ mein update ho gayi.")


if __name__ == "__main__":
    main()
