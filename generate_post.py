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
      btn.textContent = "🔕 Subscribed";
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
        btns[i].textContent = "🔕 Subscribed";
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


def pwa_head_extra(manifest_href, icon192_h
