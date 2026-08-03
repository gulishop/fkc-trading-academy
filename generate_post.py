#!/usr/bin/env python3
"""
Skill Academy — Multi-Course Daily Lesson Generator.

Har din (GitHub Action se, har course apne fixed time par — 9:00 AM se
hai aur COURSES dictionary mein diye gaye HAR course ke liye us course
ka "agla" daily lesson generate karta hai (Mistral AI se, agar lessons/
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
                                                    daal kar Mistral ko
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
        "post_time": "9:00 AM",
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
        "post_time": "9:10 AM",
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
        "post_time": "9:20 AM",
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
        "post_time": "9:30 AM",
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
        "post_time": "9:40 AM",
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
        "post_time": "9:50 AM",
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
        "post_time": "10:00 AM",
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
        "post_time": "10:10 AM",
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
        "post_time": "10:20 AM",
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
        "post_time": "10:30 AM",
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
        "post_time": "10:40 AM",
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
        "post_time": "10:50 AM",
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
        "post_time": "11:00 AM",
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
        "post_time": "11:10 AM",
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
        "post_time": "11:20 AM",
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
    "forex-trading": {
        "name": "Forex Trading",
        "icon": "💹",
        "post_time": "11:30 AM",
        "tagline": "Currency market mein trading karna sikhein — basics se lekar strategy tak",
        "topics": [
            "Forex market kya hai aur kaise kaam karta hai",
            "Currency pairs, pip, aur lot size samajhna",
            "Broker aur trading account (Exness) setup karna",
            "MetaTrader/platform use karna",
            "Leverage aur margin samajhna",
            "Technical analysis basics (charts, candlesticks)",
            "Fundamental analysis aur news ka asar",
            "Risk management aur stop-loss lagana",
            "Ek simple trading strategy banana",
            "Trading psychology aur discipline",
            "Demo se live trading tak jana",
            "Trades ka record aur performance track karna",
        ],
        "affiliate_url": "https://one.exnessonelink.com/a/buhyli14un",
        "affiliate_label": "💹 Exness Par Free Account Banayein",
    },
    "cpp-daily-coding": {
        "name": "C++ Daily Coding",
        "icon": "💻",
        "post_time": "12:00 PM",
        "tagline": "C++ zero se seekhein — roz ek naya coding lesson, practice ke sath",
        "topics": [
            "C++ setup karna (compiler, IDE) aur pehla program",
            "Variables, data types, aur input/output",
            "Operators aur type conversion",
            "Conditional statements (if/else, switch)",
            "Loops (for, while, do-while)",
            "Arrays samajhna aur use karna",
            "Strings aur string functions",
            "Functions banana aur parameter passing",
            "Pointers ki basics",
            "References aur pointers ka farak",
            "Structures (struct) banana",
            "Object-Oriented Programming — classes aur objects",
            "Constructors, destructors, aur encapsulation",
            "Inheritance aur polymorphism",
            "STL basics (vectors, maps, sets)",
            "Ek chhota project bana kar sab kuch practice karna",
        ],
    },
    "python-programming": {
        "name": "Python Programming",
        "icon": "🐍",
        "post_time": "1:00 PM",
        "tagline": "Python zero se seekhein — beginner-friendly, roz ek naya coding lesson",
        "topics": [
            "Python install karna aur pehla program",
            "Variables, data types, aur input/output",
            "Conditional statements aur loops",
            "Lists, tuples, aur dictionaries",
            "Functions banana",
            "String manipulation aur formatting",
            "File handling (read/write)",
            "Error handling (try/except)",
            "Modules aur libraries import karna",
            "Ek chhota automation script banana",
        ],
    },
    "web-development": {
        "name": "Web Development",
        "icon": "🌐",
        "post_time": "1:10 PM",
        "tagline": "HTML, CSS, aur JavaScript se apni pehli website banayein",
        "topics": [
            "HTML basics aur page structure",
            "CSS se styling aur layout",
            "Flexbox aur Grid samajhna",
            "Responsive design (mobile-friendly)",
            "JavaScript basics aur DOM",
            "Forms aur user input handle karna",
            "Buttons aur interactivity add karna",
            "Website ko GitHub Pages par free host karna",
            "Portfolio website banana",
            "Website ko client ke liye customize karna",
        ],
    },
    "excel-data-analysis": {
        "name": "Excel & Data Analysis",
        "icon": "📊",
        "post_time": "1:20 PM",
        "tagline": "Excel se data manage, analyze, aur professional reports banana seekhein",
        "topics": [
            "Excel interface aur basic formulas",
            "SUM, AVERAGE, COUNTIF jaise functions",
            "VLOOKUP aur XLOOKUP samajhna",
            "Data sorting aur filtering",
            "Pivot Tables banana",
            "Charts aur graphs banana",
            "Conditional formatting",
            "Data cleaning techniques",
            "Dashboard banana Excel mein",
            "Excel skills se freelance kaam dhoondna",
        ],
    },
    "crypto-blockchain": {
        "name": "Crypto & Blockchain Basics",
        "icon": "₿",
        "post_time": "1:30 PM",
        "tagline": "Cryptocurrency aur blockchain ki basics samajhein, safely invest karna seekhein",
        "topics": [
            "Blockchain kya hai aur kaise kaam karta hai",
            "Bitcoin aur Ethereum samajhna",
            "Crypto wallet banana aur secure karna",
            "Exchange par account banana (Binance, etc.)",
            "Buying/selling basics",
            "Scams aur fraud se bachna",
            "NFTs aur Web3 ki basics",
            "Long-term vs short-term investing",
            "Risk management crypto mein",
            "Taxes aur legal considerations Pakistan mein",
        ],
    },
    "psx-stock-trading": {
        "name": "Stock Market Trading (PSX)",
        "icon": "📈",
        "post_time": "1:40 PM",
        "tagline": "Pakistan Stock Exchange mein invest aur trade karna seekhein",
        "topics": [
            "PSX kya hai aur kaise kaam karta hai",
            "Trading account kholna (broker select karna)",
            "Shares, stocks, aur dividends samajhna",
            "Fundamental analysis basics",
            "Technical analysis aur charts",
            "Buy/sell order lagana",
            "Risk management aur diversification",
            "Long-term investing vs day trading",
            "PSX apps aur tools use karna",
            "Portfolio track karna",
        ],
    },
    "tiktok-growth": {
        "name": "TikTok Growth & Monetization",
        "icon": "🎵",
        "post_time": "1:50 PM",
        "tagline": "TikTok par followers badhayein aur content se paise kamayein",
        "topics": [
            "TikTok algorithm samajhna",
            "Niche select karna",
            "Viral content ke patterns",
            "Video editing TikTok ke liye",
            "Trending sounds aur hashtags use karna",
            "Consistency aur posting schedule",
            "Engagement badhana (comments, duets)",
            "TikTok Creator Fund aur monetization",
            "Brand deals dhoondna",
            "Account ko scale karna",
        ],
    },
    "blogging-adsense": {
        "name": "Blogging & Adsense",
        "icon": "✍️",
        "post_time": "2:00 PM",
        "tagline": "Blog shuru karein aur Google Adsense se passive income banayein",
        "topics": [
            "Niche select karna blog ke liye",
            "Blogger/WordPress par blog setup karna",
            "SEO-friendly article likhna",
            "Keyword research basics",
            "Images aur formatting",
            "Google Adsense approval lena",
            "Traffic badhane ke tarike (SEO, social)",
            "Affiliate links add karna blog mein",
            "Analytics samajhna (Google Analytics)",
            "Blog ko scale karna aur monetize karna",
        ],
    },
    "photography-editing": {
        "name": "Photography & Editing",
        "icon": "📷",
        "post_time": "2:10 PM",
        "tagline": "Mobile ya camera se professional photos lena aur Lightroom mein edit karna",
        "topics": [
            "Camera/phone settings samajhna",
            "Composition rules (rule of thirds, etc.)",
            "Lighting basics",
            "Portrait photography tips",
            "Lightroom mein basic editing",
            "Color grading aur presets",
            "Mobile editing apps (Snapseed, VSCO)",
            "Photos ko social media ke liye optimize karna",
            "Client shoots handle karna",
            "Photography se paise kamana (stock photos, clients)",
        ],
    },
    "voiceover-podcasting": {
        "name": "Voice Over & Podcasting",
        "icon": "🎙️",
        "post_time": "2:20 PM",
        "tagline": "Voice over skills seekhein aur apna podcast shuru karein",
        "topics": [
            "Voice over basics aur mic setup",
            "Script padhna aur tone control",
            "Recording software use karna (Audacity, etc.)",
            "Audio editing aur noise removal",
            "Podcast niche select karna",
            "Podcast recording aur structure",
            "Podcast ko Spotify/YouTube par publish karna",
            "Voice over gigs Fiverr/Upwork par dhoondna",
            "Consistency aur audience banana",
            "Monetization (sponsors, ads)",
        ],
    },
    "real-estate-business": {
        "name": "Real Estate Business",
        "icon": "🏠",
        "post_time": "2:30 PM",
        "tagline": "Pakistan mein real estate business shuru karna seekhein",
        "topics": [
            "Real estate market samajhna Pakistan mein",
            "Property dealer/agent kaise bante hain",
            "Property valuation basics",
            "Legal documents aur verification",
            "Clients dhoondna aur relationships banana",
            "Property marketing (online listings, social media)",
            "Negotiation skills",
            "Rental properties manage karna",
            "Property investment strategies",
            "Business ko scale karna (team, office)",
        ],
    },
    "mobile-repairing": {
        "name": "Mobile Repairing Business",
        "icon": "📱",
        "post_time": "2:40 PM",
        "tagline": "Mobile repairing seekh kar apna business shuru karein",
        "topics": [
            "Basic tools aur equipment",
            "Common mobile issues diagnose karna",
            "Screen aur battery replacement",
            "Software issues fix karna",
            "Water damage repair",
            "Soldering basics",
            "Spare parts kahan se lein",
            "Shop setup karna",
            "Pricing aur customer dealing",
            "Business ko online promote karna",
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
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")

POSTS_JSON = "posts.json"
LESSONS_DIR = "lessons"
DOCS_DIR = "docs"

ACCENTS = ["#0056D2", "#2BAF66", "#6D28D9", "#D9730D", "#0EA5A5", "#DB4C77"]

# Adsterra Direct Link / Smartlink — home page aur har lesson page par
# ek button ke tor par dikhta hai. Click = earning.
DIRECT_LINK_URL = "https://www.effectivecpmnetwork.com/vzqdxpbk97?key=699919418fe2b02eca0fb72d7ff95fea"


def direct_link_button_html(label="🚀 Aur Seekhein"):
    return (
        f'<a class="btn green" href="{DIRECT_LINK_URL}" target="_blank" '
        f'rel="noopener sponsored">{html.escape(label)}</a>'
    )


def course_affiliate_button_html(course):
    """Agar course ke sath koi affiliate link ho (jaise Forex Trading ke
    liye Exness), to ek alag button return karta hai — warna khaali string."""
    url = course.get("affiliate_url")
    if not url:
        return ""
    label = course.get("affiliate_label", "🚀 Account Banayein")
    return (
        f'<a class="btn alt" href="{url}" target="_blank" '
        f'rel="noopener sponsored">{html.escape(label)}</a>'
    )


# ---------------------------------------------------------------------
# 🔔 Notify Me — client-side reminder (browser Notification + beep tone).
# Kaam sirf tab tak karta hai jab site ka koi tab khula ho (background
# push ke liye backend/OneSignal chahiye hoga) — lekin jab bhi user site
# par ho, subscribe kiye hue courses ka scheduled time aane par ek beep
# tone + browser notification dikha deta hai.
# ---------------------------------------------------------------------
def notify_bell_html(slug):
    return (
        f'<button type="button" class="notify-btn" data-notify-slug="{slug}" '
        f'onclick="event.preventDefault();event.stopPropagation();'
        f'fkcToggleNotify(\'{slug}\', this);">🔔 Notify Me</button>'
    )


def notify_script_html():
    times = {slug: course.get("post_time", "") for slug, course in COURSES.items()}
    names = {slug: course["name"] for slug, course in COURSES.items()}
    return f"""<script>
(function(){{
  var COURSE_TIMES = {json.dumps(times, ensure_ascii=False)};
  var COURSE_NAMES = {json.dumps(names, ensure_ascii=False)};

  function parseTimeToday(t){{
    var m = /(\\d+):(\\d+)\\s*(AM|PM)/i.exec(t);
    if(!m) return null;
    var h = parseInt(m[1],10), min = parseInt(m[2],10);
    var ap = m[3].toUpperCase();
    if(ap==="PM" && h!==12) h+=12;
    if(ap==="AM" && h===12) h=0;
    var d = new Date();
    d.setHours(h, min, 0, 0);
    return d;
  }}

  function beep(){{
    try{{
      var ctx = new (window.AudioContext||window.webkitAudioContext)();
      var o = ctx.createOscillator(), g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.type = "sine";
      o.frequency.setValueAtTime(880, ctx.currentTime);
      o.frequency.setValueAtTime(660, ctx.currentTime+0.15);
      g.gain.setValueAtTime(0.001, ctx.currentTime);
      g.gain.exponentialRampToValueAtTime(0.25, ctx.currentTime+0.02);
      g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime+0.35);
      o.start(); o.stop(ctx.currentTime+0.4);
    }}catch(e){{}}
  }}

  function getSubs(){{
    try{{ return JSON.parse(localStorage.getItem("fkc_notify")||"{{}}"); }}catch(e){{ return {{}}; }}
  }}
  function isSub(slug){{ return !!getSubs()[slug]; }}
  function setSub(slug, val){{
    var obj = getSubs();
    if(val) obj[slug]=true; else delete obj[slug];
    localStorage.setItem("fkc_notify", JSON.stringify(obj));
  }}

  window.fkcToggleNotify = function(slug, btn){{
    if(isSub(slug)){{
      setSub(slug, false);
      btn.textContent = "🔔 Notify Me";
      btn.classList.remove("subscribed");
      return;
    }}
    function subscribe(){{
      setSub(slug, true);
      btn.textContent = "✅ Subscribed";
      btn.classList.add("subscribed");
      beep();
    }}
    if("Notification" in window && Notification.permission === "default"){{
      Notification.requestPermission().then(function(perm){{ subscribe(); }});
    }} else {{
      subscribe();
    }}
  }};

  document.addEventListener("DOMContentLoaded", function(){{
    var subs = getSubs();
    var btns = document.querySelectorAll("[data-notify-slug]");
    for(var i=0;i<btns.length;i++){{
      var slug = btns[i].getAttribute("data-notify-slug");
      if(subs[slug]){{
        btns[i].textContent = "✅ Subscribed";
        btns[i].classList.add("subscribed");
      }}
    }}
  }});

  function checkTimes(){{
    var now = new Date();
    var todayStr = now.toDateString();
    var fired = {{}};
    try{{ fired = JSON.parse(localStorage.getItem("fkc_notify_fired")||"{{}}"); }}catch(e){{}}
    var subs = getSubs();
    var changed = false;
    for(var slug in COURSE_TIMES){{
      if(!subs[slug]) continue;
      var t = parseTimeToday(COURSE_TIMES[slug]);
      if(!t) continue;
      var diff = now - t;
      if(diff >= 0 && diff < 90000 && fired[slug] !== todayStr){{
        beep();
        if("Notification" in window && Notification.permission === "granted"){{
          try{{
            new Notification("📚 " + COURSE_NAMES[slug] + " — Naya Lesson!", {{
              body: "Aaj ka naya lesson post ho gaya hai, abhi check karein!"
            }});
          }}catch(e){{}}
        }}
        fired[slug] = todayStr;
        changed = true;
      }}
    }}
    if(changed) localStorage.setItem("fkc_notify_fired", JSON.stringify(fired));
  }}
  setInterval(checkTimes, 30000);
  checkTimes();
}})();
</script>"""


# ---------------------------------------------------------------------
# PWA — installable app support ("Add to Home Screen" / Chrome install)
# ---------------------------------------------------------------------
MANIFEST_FILENAME = "manifest.json"
SW_FILENAME = "service-worker.js"
ICON_192 = "icons/icon-192.png"
ICON_512 = "icons/icon-512.png"


def pwa_head_extra(manifest_href, icon192_href):
    return (
        f'<link rel="manifest" href="{manifest_href}">'
        '<meta name="theme-color" content="#0B1220">'
        f'<link rel="apple-touch-icon" href="{icon192_href}">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">'
    )


def pwa_register_script(sw_href):
    return (
        "<script>if('serviceWorker' in navigator){"
        "window.addEventListener('load',function(){"
        f"navigator.serviceWorker.register('{sw_href}').catch(function(){{}});"
        "});}</script>"
    )


def build_manifest_json():
    manifest = {
        "name": BRAND_NAME,
        "short_name": BRAND_NAME[:12],
        "start_url": ".",
        "scope": ".",
        "display": "standalone",
        "background_color": "#0B1220",
        "theme_color": "#0B1220",
        "icons": [
            {"src": ICON_192, "sizes": "192x192", "type": "image/png"},
            {"src": ICON_512, "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    return json.dumps(manifest, ensure_ascii=False, indent=2)


def build_service_worker_js():
    return (
        "self.addEventListener('install',e=>self.skipWaiting());\n"
        "self.addEventListener('activate',e=>self.clients.claim());\n"
        "self.addEventListener('fetch',e=>{\n"
        "  e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));\n"
        "});\n"
    )


def pwa_extra_for(logo_href):
    if logo_href.endswith(BRAND_LOGO):
        prefix = logo_href[: -len(BRAND_LOGO)]
    else:
        prefix = ""
    manifest_href = prefix + MANIFEST_FILENAME
    icon_href = prefix + ICON_192
    sw_href = prefix + SW_FILENAME
    return (
        pwa_head_extra(manifest_href, icon_href)
        + pwa_register_script(sw_href)
    )


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
# 3. Lesson content — Mistral generate ya manual file parhein
# ---------------------------------------------------------------------
# Model fallback list — pehle wala try hota hai, agar wo 404 de (retire/
# not-found ho jaye) to script khud agla wala try karta hai. Naya model
# list mein upar add kar sakte hain jab Mistral koi naya release kare.
MODEL_NAMES = ["mistral-small-latest", "open-mistral-nemo", "mistral-large-latest"]

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"


def _mistral_call_once(model_name, prompt_text, max_retries=5):
    """Ek model ke sath chat completion call karta hai, 429/500/502/503
    (aur 403 jo account-block na ho) par retry karta hai. 404 (model not
    found) par turant raise karta hai taake caller agla model try kar sake."""
    body = json.dumps({
        "model": model_name,
        "messages": [{"role": "user", "content": prompt_text}],
    }).encode()

    wait = 20
    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(
            MISTRAL_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            # Body padho taake asli wajah pata chale (quota / permission /
            # invalid key) — sirf "403: Forbidden" kaafi nahi hota debug ke liye.
            try:
                err_body = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                err_body = "(body nahi mil saka)"
            print(f"Mistral {e.code} detail ({model_name}, attempt {attempt}): {err_body}", file=sys.stderr)

            if e.code == 403:
                print("Mistral 403 — ye account/key-level block ho sakta hai, retry se theek nahi hoga. Key check karein.", file=sys.stderr)
                raise

            if e.code in (429, 500, 502, 503) and attempt < max_retries:
                print(f"Mistral {e.code} mila ({model_name}, attempt {attempt}) — {wait}s ruk kar dobara koshish...", file=sys.stderr)
                time.sleep(wait)
                wait = min(wait * 2, 120)
                continue
            raise


def ai_generate(prompt_text, max_retries=5):
    if not MISTRAL_API_KEY:
        raise RuntimeError("MISTRAL_API_KEY set nahi hai.")

    data = None
    last_error = None
    for model_name in MODEL_NAMES:
        try:
            data = _mistral_call_once(model_name, prompt_text, max_retries=max_retries)
            break
        except urllib.error.HTTPError as e:
            last_error = e
            if e.code == 404:
                print(f"Model '{model_name}' 404 (not found/retired) — agla model try kar rahe hain...", file=sys.stderr)
                continue
            raise
    if data is None:
        raise last_error

    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        print("Mistral response se text nahi mila:", data, file=sys.stderr)
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
        print(f"[{slug}] Day {day_num} Mistral se generate ho raha hai...")
        prompt = build_prompt(slug, course, day_num, previous_titles)
        try:
            raw = ai_generate(prompt)
        except Exception as e:
            print(f"[{slug}] Mistral call fail ho gayi, aaj yeh course skip: {e}", file=sys.stderr)
            return None
        if not raw:
            print(f"[{slug}] Mistral se lesson nahi mila, aaj skip.", file=sys.stderr)
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
:root{--paper:#F7F9FA;--panel:#FFFFFF;--line:#E3E6E8;
--ink:#1C1D1F;--muted:#6A6F73;--primary:#0056D2;--primary-dark:#00419e;
--accent:#2BAF66;--purple:#6D28D9;}
*{box-sizing:border-box;}
@media (prefers-reduced-motion: no-preference){
  .fade-in{animation:fadeUp .45s ease both;}
  .fade-in.d2{animation-delay:.06s;} .fade-in.d3{animation-delay:.12s;}
  @keyframes fadeUp{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:translateY(0);}}
}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:'Inter','IBM Plex Sans',sans-serif;line-height:1.55;}
.wrap{max-width:720px;margin:0 auto;padding:24px 16px 70px;}
a{color:var(--primary);}
.top{display:flex;align-items:baseline;gap:10px;color:var(--ink);
font-weight:600;font-size:14px;border-bottom:1px solid var(--line);
padding-bottom:14px;margin-bottom:20px;}
.top .lbl{color:var(--muted);font-weight:400;}
h1{font-family:'Inter',sans-serif;font-weight:800;font-size:1.55em;
margin:.2em 0;letter-spacing:-.01em;color:var(--ink);}
h2{font-family:'Inter',sans-serif;font-weight:700;font-size:1.12em;
margin:1em 0 .35em;color:var(--ink);}
h3{color:var(--primary);font-size:.95em;margin:1.2em 0 .3em;font-weight:700;}
p{margin:.45em 0;}
.muted{color:var(--muted);font-size:.9em;}
.eyebrow{display:inline-block;color:var(--primary);font-size:.72em;
font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-bottom:6px;}
.card{background:var(--panel);border:1px solid var(--line);
border-radius:10px;padding:18px;margin:16px 0;
box-shadow:0 1px 3px rgba(20,23,28,.06);}
.btn{display:inline-flex;align-items:center;gap:8px;background:var(--primary);
color:#fff;font-weight:600;font-size:14px;text-decoration:none;
padding:11px 18px;border:none;border-radius:6px;cursor:pointer;
margin:6px 6px 0 0;}
.btn.alt{background:#fff;color:var(--ink);border:1px solid var(--line);}
.btn.green{background:var(--accent);}
.grid{display:flex;flex-direction:column;gap:12px;margin:18px 0 30px;}
.ccard{display:flex;align-items:center;gap:14px;background:var(--panel);
border:1px solid var(--line);border-radius:10px;padding:14px;
text-decoration:none;color:inherit;box-shadow:0 1px 3px rgba(20,23,28,.05);}
.ccard:hover{border-color:var(--primary);box-shadow:0 2px 8px rgba(0,86,210,.12);}
.ccard .stamp{width:52px;height:52px;flex-shrink:0;display:flex;
align-items:center;justify-content:center;font-size:1.5em;border-radius:10px;
background:var(--accent-bg,rgba(0,86,210,.08));}
.ccard .body{flex:1;min-width:0;}
.ccard .body h2{margin:0 0 3px;font-size:1.02em;}
.ccard .tag{font-size:.82em;color:var(--muted);margin:0 0 4px;}
.ccard .latest{font-size:.8em;margin:0;overflow:hidden;text-overflow:ellipsis;
white-space:nowrap;color:var(--ink);opacity:.75;}
.ccard .stub{flex-shrink:0;text-align:center;padding-left:10px;
border-left:1px solid var(--line);}
.ccard .stub-n{font-weight:800;font-size:1.15em;color:var(--primary);line-height:1;}
.ccard .stub-l{font-size:.62em;color:var(--muted);text-transform:uppercase;
letter-spacing:.03em;margin-top:2px;}
.plist a{display:flex;align-items:center;gap:12px;background:var(--panel);
border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:8px 0;
text-decoration:none;color:var(--ink);box-shadow:0 1px 2px rgba(20,23,28,.04);}
.plist a:hover{border-color:var(--primary);}
.plist .d{display:flex;align-items:center;justify-content:center;
flex-shrink:0;width:34px;height:34px;border-radius:50%;
background:rgba(0,86,210,.09);color:var(--primary);font-weight:700;
font-size:.72em;}
.badge{display:inline-block;background:var(--accent);color:#fff;
font-size:.7em;font-weight:700;padding:3px 10px;border-radius:20px;
margin-bottom:8px;text-transform:uppercase;letter-spacing:.04em;}
footer{color:var(--muted);font-size:12px;margin-top:40px;text-align:center;}
.brand-bar{display:flex;align-items:center;gap:12px;margin-bottom:6px;}
.brand-bar img{width:46px;height:46px;border-radius:10px;flex-shrink:0;
object-fit:cover;background:#fff;border:1px solid var(--line);}
.brand-bar .bname{font-family:'Inter',sans-serif;font-weight:800;
color:var(--ink);font-size:1.1em;line-height:1.25;}
.brand-bar .btag{color:var(--muted);font-size:.78em;}
.brand-footer{border-top:1px solid var(--line);margin-top:34px;
padding-top:16px;display:flex;align-items:center;gap:12px;}
.brand-footer img{width:36px;height:36px;border-radius:8px;flex-shrink:0;
object-fit:cover;background:#fff;border:1px solid var(--line);}
.brand-footer .txt{font-size:.8em;color:var(--muted);line-height:1.5;}
.brand-footer .txt b{color:var(--ink);}
.notify-btn{display:inline-flex;align-items:center;gap:6px;background:#fff;
color:var(--primary);border:1px solid var(--line);border-radius:20px;
font-size:.76em;font-weight:700;padding:5px 12px;cursor:pointer;
margin-top:6px;white-space:nowrap;}
.notify-btn.subscribed{background:var(--accent);color:#fff;border-color:var(--accent);}
.ccard .notify-btn{margin-top:8px;}
"""

HEAD = """<!DOCTYPE html>
<html lang="ur"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta property="og:title" content="{title}">
<meta property="og:description" content="{ogdesc}">
<meta property="og:image" content="{ogimage}">
<meta name="twitter:card" content="summary_large_image">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-Z5FV45KG2C"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-Z5FV45KG2C');
</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5639688573760714" crossorigin="anonymous"></script>
<script src="https://pl30647963.effectivecpmnetwork.com/35/50/90/355090180a90a458c3f1895b8e9f6607.js"></script>
<link rel="icon" href="{logo_href}">
{pwa_extra}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{css}</style></head><body><div class="wrap">
<div class="brand-bar fade-in"><img src="{logo_href}" alt="{brand}">
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


FOOT_TAIL = f"</div><footer>{BRAND_NAME} — daily lessons, automatically updated</footer></body></html>"


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
    <a class="ccard fade-in" href="courses/{slug}/index.html">
      <div class="stamp" style="--accent-bg:{accent}1a;color:{accent}">{course['icon']}</div>
      <div class="body">
        <h2>{html.escape(course['name'])}</h2>
        <p class="tag">{html.escape(course['tagline'])}</p>
        <p class="latest">📖 {html.escape(latest)}</p>
        <p class="tag" style="margin-top:4px">🕒 Roz {html.escape(course.get('post_time', ''))} PKT par naya lesson</p>
        {notify_bell_html(slug)}
      </div>
      <div class="stub" style="color:{accent}"><span class="stub-n" style="color:{accent}">{count:02d}</span><span class="stub-l">{'lesson' if count == 1 else 'lessons'}</span></div>
    </a>""")

    logo_href = BRAND_LOGO
    body = f"""
    <div class="top"><span>{html.escape(BRAND_NAME)}</span>
    <span class="lbl">Digital Hub — apni pasand ka course chunein</span></div>
    <span class="eyebrow fade-in">Course Library</span>
    <h1 class="fade-in">🎓 Roz ek naya practical lesson</h1>
    <p class="muted fade-in d2">📅 Har course ka naya lesson roz apne fixed time par (9:00 AM se 11:30 AM Pakistan time ke darmiyan) yahan post hota hai — har course card par uska waqt likha hai.
    Jis course mein interest ho us par tap karein — daily lesson step-by-step parhein aur practice karein.</p>
    <p class="fade-in d2">{direct_link_button_html("🚀 Start Learning")}</p>
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
        pwa_extra=pwa_extra_for(logo_href),
    )
    return head + body + FOOT_TAIL + notify_script_html()


def render_course_page(slug, course, lessons):
    items = []
    for lesson in reversed(lessons):
        items.append(
            f'<a href="posts/{lesson["date"]}-{lesson["id"]}.html">'
            f'<span class="d">{lesson["day"]:02d}</span>{html.escape(lesson["title"])}</a>'
        )
    listing = "".join(items) if items else '<p class="muted">Abhi koi lesson nahi — pehla jald aayega.</p>'
    affiliate_btn = course_affiliate_button_html(course)
    affiliate_block = f'<p>{affiliate_btn}</p>' if affiliate_btn else ""

    logo_href = f"../../{BRAND_LOGO}"
    body = f"""
    <div class="top"><a href="../../index.html">← {html.escape(BRAND_NAME)}</a></div>
    <h1>{course['icon']} {html.escape(course['name'])}</h1>
    <p class="muted">{html.escape(course['tagline'])}</p>
    <p class="muted">📅 Naya lesson roz <b>{html.escape(course.get('post_time', ''))} Pakistan time</b> par yahan add hota hai.</p>
    <p>{notify_bell_html(slug)}</p>
    {affiliate_block}
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
        pwa_extra=pwa_extra_for(logo_href),
    )
    return head + body + FOOT_TAIL + notify_script_html()


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
    affiliate_btn = course_affiliate_button_html(course)
    affiliate_block = f'<p>{affiliate_btn}</p>' if affiliate_btn else ""

    body = f"""
    <div class="top"><a href="../../../index.html">← {html.escape(BRAND_NAME)}</a>
    <a href="../index.html" class="course-back-link">/ {html.escape(course['name'])}</a></div>
    {badge}
    <p class="muted">{course['icon']} {html.escape(course['name'])} · Day {lesson['day']:02d}</p>
    <h1>{html.escape(lesson['title'])}</h1>
    <div class="card">
      {lesson_html}
      {affiliate_block}
      <div>
        <a class="btn" href="{wa_link}" target="_blank" rel="noopener">📲 WhatsApp par Share karein</a>
        <a class="btn alt" href="{tg_link}" target="_blank" rel="noopener">✈️ Telegram par Share karein</a>
        <a class="btn alt" href="{fb_link}" target="_blank" rel="noopener">📘 Facebook par Share karein</a>
      </div>
    </div>
    <p>{direct_link_button_html("🚀 Watch Next Lesson")}</p>
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
        pwa_extra=pwa_extra_for(logo_href),
    )
    return head + body + FOOT_TAIL


# ---------------------------------------------------------------------
# 5. Main
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

        os.makedirs(os.path.join(DOCS_DIR, "courses", slug, "posts"), exist_ok=True)
        page = render_lesson_page(slug, course, lesson, is_latest=True)
        with open(
            os.path.join(DOCS_DIR, "courses", slug, "posts", f"{lesson['date']}-{lesson['id']}.html"),
            "w", encoding="utf-8",
        ) as f:
            f.write(page)

    save_posts(posts)

    # rebuild course pages — HAMESHA sab COURSES ke liye (chahe generation
    # sirf ek course ke liye hui ho), taake har course ka page hamesha
    # maujood rahe (warna jin courses ka pehla run abhi nahi hua unke
    # courses/<slug>/index.html missing reh jate hain aur 404 aata hai)
    for slug, course in COURSES.items():
        lessons = posts.get(slug, [])
        os.makedirs(os.path.join(DOCS_DIR, "courses", slug, "posts"), exist_ok=True)
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

    # PWA files — har build par (taake naye icons/manifest changes turant
    # reflect hon). Icons khud PNG hain, unhe docs/icons/ mein manually
    # daalna hoga (script text files hi generate kar sakta hai).
    with open(os.path.join(DOCS_DIR, MANIFEST_FILENAME), "w", encoding="utf-8") as f:
        f.write(build_manifest_json())
    with open(os.path.join(DOCS_DIR, SW_FILENAME), "w", encoding="utf-8") as f:
        f.write(build_service_worker_js())

    print("Done — site docs/ mein update ho gayi.")


if __name__ == "__main__":
    main()
