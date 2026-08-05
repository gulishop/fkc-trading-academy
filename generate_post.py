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
import math
import shutil
import json
import html
import datetime
import subprocess
import urllib.request
import urllib.parse
import urllib.error

import requests  # Agnes AI video calls ke liye

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ---------------------------------------------------------------------
# 1. COURSES — yahan naya course add/hata/edit karein
# ---------------------------------------------------------------------
COURSES = {
    "youtube-automation": {
        "name": "YouTube Automation",
        "icon": "🎬",
        "post_time": "12:00 AM",
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
        "post_time": "12:10 AM",
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
        "post_time": "12:20 AM",
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
        "post_time": "12:30 AM",
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
        "post_time": "12:40 AM",
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
        "post_time": "12:50 AM",
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
        "post_time": "1:00 AM",
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
        "post_time": "1:10 AM",
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
        "post_time": "1:20 AM",
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
        "post_time": "1:30 AM",
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
        "post_time": "1:40 AM",
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
        "post_time": "1:50 AM",
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
        "post_time": "2:00 AM",
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
        "post_time": "2:10 AM",
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
        "post_time": "2:20 AM",
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
        "post_time": "2:30 AM",
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
    "kids-safety-education": {
        "name": "Bachon Ki Hifazat (Good Touch, Bad Touch)",
        "icon": "🛡️",
        "post_time": "2:40 AM",
        "for_kids": True,
        "certificate_fee": "Free",
        "tagline": "Bachon ko apni hifazat, apne jism ke huq, aur 'na' kehna sikhayein — asaan, pyaar bhare andaz mein. Ammi/Abbu ke sath milkar padhayein.",
        "topics": [
            "Mera jism sirf mera hai",
            "Achi choo aur buri choo mein farak",
            "Private parts private kyun hote hain (swimsuit rule)",
            "Jab koi ajeeb tarike se choo raha ho to 'NA' kehna aur door hatna",
            "Acha secret aur bura secret mein farak",
            "Trusted adult kaun hota hai aur unhe foran batana",
            "Jaan-pehchaan wale se bhi khabardar rehna",
            "Online/video-call par ajnabiyon se safety",
            "Apne jazbaat (dar, sharm, confusion) ko pehchanna — yeh sab normal hai",
            "Madad kaise mangein — baar baar batana, kisi ne na maane to doosre trusted adult ko batana",
        ],
    },
    "cpp-daily-coding": {
        "name": "C++ Daily Coding",
        "icon": "💻",
        "post_time": "2:50 AM",
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
        "post_time": "3:00 AM",
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
        "post_time": "3:10 AM",
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
        "post_time": "3:20 AM",
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
        "post_time": "3:30 AM",
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
        "post_time": "3:40 AM",
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
        "post_time": "3:50 AM",
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
        "post_time": "4:00 AM",
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
        "post_time": "4:10 AM",
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
        "post_time": "4:20 AM",
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
        "post_time": "4:30 AM",
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
        "post_time": "4:40 AM",
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
    "kids-pg": {
        "name": "Play Group (PG) Course",
        "icon": "🧸",
        "post_time": "4:50 AM",
        "for_kids": True,
        "certificate_fee": "Free",
        "tagline": "Chhote bachon (Play Group age) ke liye pehla seekhne ka safar — rang, shakalein, aawazein, aur pyaar bhare basics.",
        "topics": [
            "Rangon ki pehchan (laal, neela, peela, hara)",
            "Shaklein pehchanna (circle, square, triangle)",
            "Janwaron ki aawazein aur naam",
            "Jism ke hisse pehchanna (haath, pair, aankh, naak)",
            "Ginti 1 se 5 tak",
            "Chhote-bade, upar-neeche jaisay concepts",
            "Phalon aur sabziyon ki pehchan",
            "Ammi, Abbu, aur ghar walon ke naam",
            "Roz ki cheezein (cup, ball, kitab, khilona)",
            "Simple ishare aur alfaz (haan, na, please, shukriya)",
        ],
    },
    "kids-nursery": {
        "name": "Nursery Course",
        "icon": "🔤",
        "post_time": "5:00 AM",
        "for_kids": True,
        "certificate_fee": "Free",
        "tagline": "Nursery age ke bachon ke liye alphabets, ginti, aur bunyadi seekhne ki mazedaar lessons.",
        "topics": [
            "A se Z tak alphabets pehchanna",
            "Ginti 1 se 10 tak likhna aur bolna",
            "Rangon ke naam angrezi mein",
            "Shaklein aur unke naam (square, circle, star)",
            "Apna naam aur ghar ka pata bolna seekhna",
            "Din (Monday-Sunday) aur mausam (dhoop, baarish)",
            "Chhoti chhoti awazon se lafz banana (cat, dog, sun)",
            "Phal, sabzi, aur janwaron ki angrezi mein pehchan",
            "Adab: please, thank you, sorry kab bolein",
            "Pencil pakadna aur seedhi/terhi lakeerein banana",
        ],
    },
    "kids-kg": {
        "name": "Kindergarten (KG) Course",
        "icon": "📚",
        "post_time": "5:10 AM",
        "for_kids": True,
        "certificate_fee": "Free",
        "tagline": "KG level bachon ke liye padhai — chhote jumlay, ginti mein jama-tafreeq, aur seekhne ka agla qadam.",
        "topics": [
            "Chhote alfaz jorr kar padhna (cat, sun, bag)",
            "Ginti 1 se 50 tak",
            "Simple jama (addition) 1 se 10 tak",
            "Simple tafreeq (subtraction) 1 se 10 tak",
            "Chhoti jumlay banana (I am happy, This is a ball)",
            "Din, hafte, aur mahine ke naam",
            "Shaklein aur unki pehchan gehrai se (rectangle, oval)",
            "Apne baaray mein bolna (naam, umar, school)",
            "Kahani sunna aur us par sawal ka jawab dena",
            "Likhne ki practice — chhote alfaz aur numbers",
        ],
    },
    "kids-good-behavior": {
        "name": "Bachon Mein Achi Adaat (Good Behavior)",
        "icon": "🌟",
        "post_time": "5:20 AM",
        "for_kids": True,
        "certificate_fee": "Free",
        "tagline": "Bachon ko roz ek achi adaat sikhayein — adab, sachai, sharing, aur bado ki izzat, pyaar bhare andaz mein.",
        "topics": [
            "Please, Thank You, aur Sorry ka sahi waqt par istemal",
            "Bado ki izzat karna aur unki baat sunna",
            "Sach bolna kyun zaroori hai",
            "Apni cheezein doosron ke sath share karna",
            "Sabar rakhna aur baari ka intezar karna",
            "Apna saman khud sametna aur safai rakhna",
            "Dosti mein pyaar aur mil kar khelna",
            "Janwaron aur paudon se pyaar aur nazuk sulook",
            "Ghussa aane par khud ko sambhalna",
            "Shukar guzar hona — jo mila us par khush rehna",
        ],
    },
    "kids-educational-games": {
        "name": "Bachon Ke Educational Games",
        "icon": "🎮",
        "post_time": "5:30 AM",
        "for_kids": True,
        "certificate_fee": "Free",
        "tagline": "Khel khel mein seekhna — ammi/abbu ghar par bachon ke sath khel kar sikhane wale asaan games.",
        "topics": [
            "Yaadasht (memory) card matching game",
            "Alphabet hunt — ghar mein cheezein dhoondna jo us harf se shuru hon",
            "Ginti wala hopscotch (chalk se zameen par khel)",
            "Rang milaan (color sorting) game",
            "Shaklein chhupaao aur dhoondo",
            "Kahani banane ka game (baari baari ek jumla)",
            "Sound matching — aankhein band karke aawaz pehchanna",
            "Puzzle aur jigsaw se sabar aur soch badhana",
            "Role-play games (doctor-doctor, dukaan-dukaan)",
            "Family game night — bina screen ke khelay jaane wale games",
        ],
    },
}

BRAND_NAME = "FKC Trading Academy"
BRAND_LOGO = "logo.png"  # docs/logo.png — repo mein khud upload karein
BRAND_CONTACT_NAME = "Fazul Khan Chandio"
BRAND_CONTACT_TITLE = "Founder & CEO"
BRAND_CONTACT_PHONE = "+92 333 3909816"
BRAND_WHATSAPP_DIGITS = re.sub(r"\D", "", BRAND_CONTACT_PHONE)  # wa.me link ke liye sirf digits
BRAND_LINE = f"{BRAND_CONTACT_NAME} — {BRAND_CONTACT_TITLE} — {BRAND_CONTACT_PHONE}"
BRAND_NAME_TITLE_LINE = f"{BRAND_CONTACT_NAME} — {BRAND_CONTACT_TITLE}"

SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")  # Mistral fail ho to fallback
AGNES_API_KEY = os.environ.get("AGNES_API_KEY", "")  # Agnes AI video API key

POSTS_JSON = "posts.json"
LESSONS_DIR = "lessons"
DOCS_DIR = "docs"
IMAGES_DIR = "images"  # optional, manually-added lesson illustrations —
# admin khud is folder mein images/<slug>/day-XXX.(png|jpg|jpeg|webp) daal
# sakta hai; agar file maujood ho to woh lesson page par khud-b-khud
# lag jati hai (koi AI image generation nahi — sirf jo aap khud daalein).
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def find_lesson_image(slug, day_num):
    """Agar images/<slug>/day-XXX.<ext> maujood ho to uska path return karta
    hai, warna None. Isse admin har lesson ke sath apni illustration
    manually add kar sakta hai (khaas taur par kids courses ke liye)."""
    padded = f"{day_num:03d}"
    for ext in IMAGE_EXTS:
        src = os.path.join(IMAGES_DIR, slug, f"day-{padded}{ext}")
        if os.path.exists(src):
            return src
    return None


def publish_lesson_image(slug, day_num):
    """Agar us lesson ke liye images/<slug>/day-XXX.<ext> maujood ho, use
    docs/courses/<slug>/posts/images/ mein copy kar deta hai aur lesson
    page ke liye relative href (posts/ folder ke andar se) return karta
    hai — warna None."""
    src = find_lesson_image(slug, day_num)
    if not src:
        return None
    ext = os.path.splitext(src)[1]
    padded = f"{day_num:03d}"
    dest_dir = os.path.join(DOCS_DIR, "courses", slug, "posts", "images")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"day-{padded}{ext}")
    shutil.copyfile(src, dest)
    return f"images/day-{padded}{ext}"


# ---------------------------------------------------------------------
# 🛡️ Kids-safety course images — YEH KABHI bhi kisi AI/third-party image
# API se generate NAHI hoti. Sirf 10 FIXED, hand-drawn abstract symbols
# hain (shield, heart, umbrella, stop-sign, key, speech-bubble, star,
# compass, sun, house) — koi bacha/jism/touch scene kabhi nahi, sirf
# geometric shapes jo hum khud PIL se banate hain. Rule STRICT hai:
# is course ke liye koi bhi naya "AI-generated" ya "prompt se banaya"
# image path kabhi add nahi karna — hamesha isi fixed set se.
# ---------------------------------------------------------------------
KIDS_SYMBOL_PALETTE = [
    ("shield",        "#EAF2FF", "#0056D2"),
    ("heart",         "#FFF0F3", "#E1477E"),
    ("umbrella",      "#EFFBF3", "#2BAF66"),
    ("stop_hand",     "#FFF3E8", "#D97706"),
    ("key",           "#F5F0FF", "#6D28D9"),
    ("speech_bubble", "#EAFBFF", "#0891B2"),
    ("star",          "#FFFBEA", "#CA8A04"),
    ("compass",       "#EEF2FF", "#4338CA"),
    ("sun",           "#FFF7ED", "#EA580C"),
    ("house",         "#F0FDF4", "#16A34A"),
]


def _draw_shield(d, cx, cy, s, c):
    pts = [(cx, cy-s), (cx+s*0.8, cy-s*0.55), (cx+s*0.8, cy+s*0.15),
           (cx, cy+s), (cx-s*0.8, cy+s*0.15), (cx-s*0.8, cy-s*0.55)]
    d.polygon(pts, fill=c)


def _draw_heart(d, cx, cy, s, c):
    r = s*0.55
    d.ellipse([cx-s, cy-s*0.5-r*0.3, cx, cy-s*0.5+r*1.1], fill=c)
    d.ellipse([cx, cy-s*0.5-r*0.3, cx+s, cy-s*0.5+r*1.1], fill=c)
    d.polygon([(cx-s, cy), (cx+s, cy), (cx, cy+s*1.2)], fill=c)


def _draw_umbrella(d, cx, cy, s, c):
    d.pieslice([cx-s, cy-s, cx+s, cy+s*0.6], 180, 360, fill=c)
    d.line([cx, cy, cx, cy+s*1.1], fill=c, width=max(6, int(s*0.08)))
    d.arc([cx-s*0.15, cy+s*0.9, cx+s*0.15, cy+s*1.3], 0, 180, fill=c, width=max(6, int(s*0.08)))


def _draw_stop_hand(d, cx, cy, s, c):
    n = 8
    pts = [(cx + s*math.cos(math.radians(a)), cy + s*math.sin(math.radians(a)))
           for a in range(22, 360, 45)]
    d.polygon(pts, fill=c)


def _draw_key(d, cx, cy, s, c):
    d.ellipse([cx-s, cy-s*0.6, cx-s*0.2, cy+s*0.2], outline=c, width=max(8, int(s*0.14)))
    d.line([cx-s*0.35, cy-0.05*s, cx+s, cy-0.05*s], fill=c, width=max(6, int(s*0.1)))
    d.line([cx+s*0.6, cy-0.05*s, cx+s*0.6, cy+s*0.35], fill=c, width=max(6, int(s*0.1)))
    d.line([cx+s*0.85, cy-0.05*s, cx+s*0.85, cy+s*0.3], fill=c, width=max(6, int(s*0.1)))


def _draw_speech_bubble(d, cx, cy, s, c):
    d.rounded_rectangle([cx-s, cy-s*0.7, cx+s, cy+s*0.45], radius=int(s*0.3), fill=c)
    d.polygon([(cx-s*0.35, cy+s*0.4), (cx-s*0.05, cy+s*0.4), (cx-s*0.45, cy+s*0.95)], fill=c)


def _draw_star(d, cx, cy, s, c):
    pts = []
    for i in range(10):
        r = s if i % 2 == 0 else s*0.42
        a = math.radians(-90 + i*36)
        pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    d.polygon(pts, fill=c)


def _draw_compass(d, cx, cy, s, c):
    d.ellipse([cx-s, cy-s, cx+s, cy+s], outline=c, width=max(8, int(s*0.12)))
    d.polygon([(cx, cy-s*0.75), (cx+s*0.22, cy), (cx, cy+s*0.75), (cx-s*0.22, cy)], fill=c)
    d.ellipse([cx-s*0.08, cy-s*0.08, cx+s*0.08, cy+s*0.08], fill=c)


def _draw_sun(d, cx, cy, s, c):
    d.ellipse([cx-s*0.55, cy-s*0.55, cx+s*0.55, cy+s*0.55], fill=c)
    for i in range(8):
        a = math.radians(i*45)
        x1, y1 = cx + s*0.75*math.cos(a), cy + s*0.75*math.sin(a)
        x2, y2 = cx + s*1.05*math.cos(a), cy + s*1.05*math.sin(a)
        d.line([x1, y1, x2, y2], fill=c, width=max(6, int(s*0.1)))


def _draw_house(d, cx, cy, s, c):
    d.polygon([(cx-s, cy+s*0.1), (cx, cy-s*0.6), (cx+s, cy+s*0.1)], fill=c)
    d.rectangle([cx-s*0.7, cy+s*0.1, cx+s*0.7, cy+s], fill=c)


_KIDS_SYMBOL_DRAWERS = {
    "shield": _draw_shield, "heart": _draw_heart, "umbrella": _draw_umbrella,
    "stop_hand": _draw_stop_hand, "key": _draw_key, "speech_bubble": _draw_speech_bubble,
    "star": _draw_star, "compass": _draw_compass, "sun": _draw_sun, "house": _draw_house,
}


def generate_kids_safety_symbol_image(slug, day_num, topic_index):
    """Sirf FIXED abstract symbols draw karta hai (upar dekhein) — koi AI
    generation, koi network call, koi free-form prompt kabhi nahi. Agar
    PIL maujood na ho to chup chaap skip (lesson generation nahi rukti)."""
    if not PIL_AVAILABLE:
        return
    name, bg, fg = KIDS_SYMBOL_PALETTE[topic_index % len(KIDS_SYMBOL_PALETTE)]
    padded = f"{day_num:03d}"
    dest_dir = os.path.join(IMAGES_DIR, slug)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"day-{padded}.png")
    try:
        w, h = 1024, 576
        img = Image.new("RGB", (w, h), bg)
        d = ImageDraw.Draw(img)
        d.ellipse([w/2-170, h/2-170, w/2+170, h/2+170], fill="#FFFFFF")
        _KIDS_SYMBOL_DRAWERS[name](d, w/2, h/2, 100, fg)
        img.save(dest, "PNG")
        print(f"[{slug}] Day {day_num} symbol image ban gayi ({name}).")
    except Exception as e:
        print(f"[{slug}] Day {day_num} symbol image nahi ban saki, skip: {e}", file=sys.stderr)


# ---------------------------------------------------------------------
# 🖼️ Automatic lesson images — Pollinations (https://pollinations.ai),
# bilkul FREE aur bina API key ke, sirf ek URL fetch karke image milti
# hai. Yeh sirf normal (non-kids) courses ke liye chalta hai — kids
# safety course ke liye images upar wale FIXED symbol set se bantay
# hain, kabhi AI/network se nahi.
# ---------------------------------------------------------------------
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"


def generate_lesson_image(slug, course, day_num, title, topic_hint=None, concept_text=None):
    """Agar is lesson ke liye pehle se image nahi hai (manual ya purani
    generated), naya image bana kar images/<slug>/day-XXX.png mein save
    kar deta hai. Kids-safety course ke liye sirf fixed abstract symbol
    use hota hai; baaki sab courses ke liye Pollinations se AI image.
    Mismatch kam karne ke liye: (1) prompt mein us din ka exact topic +
    lesson ke Concept se ek snippet bhi diya jata hai (sirf course ka
    naam kaafi generic hota hai), (2) response ko basic sanity-check
    karte hain (khaali/chhota/corrupt na ho), (3) agar pehli koshish
    fail/kharab lage to ek simpler fallback prompt se dobara try hota
    hai. Fail ho jaye to chup chaap skip — lesson generation kabhi
    iski wajah se nahi rukni chahiye."""
    if find_lesson_image(slug, day_num):
        return True  # already maujood (manual ya pehle se generate ki hui)

    if course.get("for_kids"):
        topic_index = (day_num - 1) % len(course["topics"])
        generate_kids_safety_symbol_image(slug, day_num, topic_index)
        return True

    padded = f"{day_num:03d}"
    dest_dir = os.path.join(IMAGES_DIR, slug)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"day-{padded}.png")

    focus = (topic_hint or title or course["name"]).strip()
    concept_snippet = re.sub(r"\s+", " ", (concept_text or "")).strip()[:160]

    primary_prompt = (
        f"flat-illustration style educational thumbnail that CLEARLY and LITERALLY "
        f"depicts this exact topic: '{focus}'. "
        + (f"Context/details to depict: {concept_snippet}. " if concept_snippet else "")
        + f"Course subject: {course['name']}. One clear focal subject directly showing "
        "the topic above — no random unrelated objects, no generic stock-photo people, "
        "no text, no watermark, clean modern vibrant colors, professional."
    )
    fallback_prompt = (
        f"simple flat icon illustration representing '{course['name']}' — "
        f"specifically about {focus}, minimal, vibrant colors, no text, no watermark"
    )

    # 3 attempts ab: primary prompt 2 baar (chhota backoff ke sath, kyunke
    # zyadatar fail sirf Pollinations ka aani-jaani rate-limit/timeout hota
    # hai — dobara try karne se hi mil jata hai) aur aakhir mein simpler
    # fallback prompt. Har attempt ke darmiyan thoda sleep taake ek hi run
    # mein bohot saare courses ke peeche-peeche calls se rate-limit na lage.
    attempts_plan = [primary_prompt, primary_prompt, fallback_prompt]
    last_err = None
    for attempt, prompt in enumerate(attempts_plan, start=1):
        seed = str(abs(hash(slug + padded + str(attempt))) % 100000)
        url = POLLINATIONS_BASE + urllib.parse.quote(prompt) + (
            f"?width=1024&height=576&nologo=true&seed={seed}"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            # Sanity check: khaali/bohot chhoti (error page) ya bina valid
            # image-magic-bytes ke response ko reject kar dete hain.
            looks_like_image = data[:8].startswith(b"\x89PNG") or data[:3] == b"\xff\xd8\xff"
            if not data or len(data) < 3000 or not looks_like_image:
                raise ValueError(f"response image jaisa nahi lagta (size={len(data) if data else 0})")
            with open(dest, "wb") as f:
                f.write(data)
            print(f"[{slug}] Day {day_num} image generate ho gayi (Pollinations, attempt {attempt}).")
            return True
        except Exception as e:
            last_err = e
            print(f"[{slug}] Day {day_num} image attempt {attempt} fail ho gayi: {e}", file=sys.stderr)
            if attempt < len(attempts_plan):
                time.sleep(4)
    msg = f"[{slug}] Day {day_num} image generate nahi ho saki ({len(attempts_plan)} attempts fail), skip kar rahe hain: {last_err}"
    print(msg, file=sys.stderr)
    log_error(msg)
    return False


# ---------------------------------------------------------------------
# 🎬 AI video explanation — YEH 100% FREE hai, avatar/chehra NAHI hota
# (koi paid avatar API kabhi automate ke liye free nahi milti). Iski
# jagah: (1) Microsoft Edge ka free "edge-tts" awaaz (koi API key
# nahi chahiye) lesson ko bolta hai, (2) wahi awaaz lesson ki
# already-generated image/slide ke sath ffmpeg se mila kar ek chhota
# .mp4 ban jata hai. Awaaz HAMESHA pure Urdu, FEMALE voice
# (ur-PK-UzmaNeural) hoti hai — koi English/male fallback voice kabhi
# use nahi hoti.
#
# SIRF asal Urdu-script translation (["ur"]) se bola jata hai — Roman
# Urdu (Latin letters) text is voice se ab kabhi nahi bola jata, kyunki
# edge-tts Roman Urdu ko sahi tarah nahi padh pata (kabhi English jaisa,
# kabhi ajeeb accent) aur awaaz saaf/samajh mein na aane wali ban jati
# hai. Isliye agar us lesson ka Urdu-script translation abhi tak nahi
# bana, to video is dafa skip ho jati hai aur translation ban te hi
# (heal_degenerate_translations ke agle run mein) khud-b-khud ban jati
# hai — is se awaaz hamesha saaf, khaalis, bolchaal wali Urdu rehti hai.
# Thodi slow speech rate (-8%) bhi set hai taake alfaz zyada saaf/clear
# sunayi dein.
#
# System mein "edge-tts" (pip) aur "ffmpeg" (apt) dono maujood hone
# chahiye — GitHub Actions workflow mein add karne honge (neeche
# instructions). Agar koi bhi step fail ho (tool missing, TTS error,
# ffmpeg error), video sirf chup chaap skip ho jata hai — lesson ka
# baaki sab (text, image, translations) kabhi iski wajah se nahi
# rukta. Ek dafa video ban jaye to cache ho jata hai (dobara nahi
# banta), bilkul images ki tarah.
# ---------------------------------------------------------------------
VIDEOS_DIR = "videos"
NARRATION_VOICE_UR = "ur-PK-UzmaNeural"  # pure Urdu, FEMALE awaaz — hamesha yehi use hoti hai, kabhi English/male nahi
NARRATION_RATE_UR = "-8%"  # thodi slow — behtar, saaf-suthri clarity ke liye
NARRATION_MAX_CHARS = 1600  # video zyada lamba na ho, isliye script yahan tak cap hoti hai


def find_lesson_video(slug, day_num):
    padded = f"{day_num:03d}"
    src = os.path.join(VIDEOS_DIR, slug, f"day-{padded}.mp4")
    return src if os.path.exists(src) else None


def _build_narration_text(title, preamble, sections):
    parts = [title or ""]
    if preamble:
        parts.append(preamble)
    for label, content in sections:
        if not content:
            continue
        parts.append(f"{label}. {content}")
    text = "\n".join(p for p in parts if p)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)   # code blocks hata do
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # markdown links -> sirf text
    text = re.sub(r"[#>*_]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:NARRATION_MAX_CHARS]


def _run_edge_tts(text_file_path, voice, out_mp3, rate=None, attempts=2):
    # edge-tts kabhi-kabhi network hiccup se fail hota hai — ek dobara
    # koshish (chhote wait ke sath) zyadatar cases mein kaafi hoti hai.
    last_err = None
    cmd = ["edge-tts", "--voice", voice, "--file", text_file_path, "--write-media", out_mp3]
    if rate:
        cmd += ["--rate", rate]
    for attempt in range(1, attempts + 1):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True, timeout=120,
            )
            if result.returncode != 0:
                last_err = result.stderr.decode(errors="ignore")[:300]
                print(f"edge-tts error (attempt {attempt}): {last_err}", file=sys.stderr)
            elif os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 1000:
                return True
            else:
                last_err = "output mp3 khaali/chhota nikla"
        except Exception as e:
            last_err = str(e)
            print(f"edge-tts call fail (attempt {attempt}): {e}", file=sys.stderr)
        if attempt < attempts:
            time.sleep(5)
    return False


def _get_audio_duration(mp3_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", mp3_path],
            capture_output=True, timeout=30, text=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def _srt_timestamp(seconds):
    ms = max(0, int(round(seconds * 1000)))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _build_caption_srt(script_text, duration, srt_path, words_per_caption=6):
    """Narration text ko chhote-chhote caption chunks mein baant kar ek
    .srt file banata hai, duration ke hisaab se barabar time diya jata
    hai (real speech-alignment nahi — sirf estimate — lekin free jugaad
    ke liye kaafi accha lagta hai)."""
    words = (script_text or "").split()
    if not words or not duration or duration <= 0:
        return False
    chunks = [words[i:i + words_per_caption] for i in range(0, len(words), words_per_caption)]
    per_chunk = duration / len(chunks)
    lines = []
    for i, chunk in enumerate(chunks):
        start, end = i * per_chunk, min((i + 1) * per_chunk, duration)
        lines += [str(i + 1), f"{_srt_timestamp(start)} --> {_srt_timestamp(end)}", " ".join(chunk), ""]
    try:
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return True
    except Exception:
        return False


def _run_ffmpeg_kenburns_captions(image_path, audio_path, srt_path, out_mp4):
    """Free 'jugaad' — asal video-generation AI (Veo/Sora waghera) paid
    hoti hai, is liye iski jagah slow zoom (Ken Burns effect) + neeche
    animated captions burn karte hain, taake ek static slide bhi ek
    'zinda' explainer video jaisi lage — bilkul free, sirf ffmpeg se."""
    vf = (
        "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
        "zoompan=z='min(zoom+0.0006,1.18)':d=9999:s=1280x720:fps=25"
    )
    if srt_path and os.path.exists(srt_path):
        escaped = srt_path.replace("\\", "/").replace(":", "\\:")
        vf += (
            f",subtitles='{escaped}':force_style="
            "'FontSize=20,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,"
            "BorderStyle=3,Outline=2,Shadow=0,Alignment=2,MarginV=40'"
        )
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
        "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p", "-shortest", "-vf", vf, out_mp4,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=240)
        if result.returncode != 0:
            print(f"ffmpeg (Ken Burns+captions) error: {result.stderr.decode(errors='ignore')[:300]}", file=sys.stderr)
            return False
        return os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 5000
    except Exception as e:
        print(f"ffmpeg (Ken Burns+captions) call fail: {e}", file=sys.stderr)
        return False


def _run_ffmpeg_image_audio(image_path, audio_path, out_mp4):
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path, "-i", audio_path,
        "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p", "-shortest",
        "-vf", "scale=1024:576:force_original_aspect_ratio=decrease,pad=1024:576:(ow-iw)/2:(oh-ih)/2",
        out_mp4,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=180)
        if result.returncode != 0:
            print(f"ffmpeg error: {result.stderr.decode(errors='ignore')[:300]}", file=sys.stderr)
            return False
        return os.path.exists(out_mp4) and os.path.getsize(out_mp4) > 5000
    except Exception as e:
        print(f"ffmpeg call fail: {e}", file=sys.stderr)
        return False


def generate_lesson_narration_video(slug, course, lesson, image_source_path):
    day_num = lesson["day"]
    if find_lesson_video(slug, day_num):
        return  # already ban chuka hai, dobara nahi banana

    if not image_source_path or not os.path.exists(image_source_path):
        return  # koi slide/image nahi mili, video ke liye kuch nahi hai

    translations = lesson.get("translations") or {}
    ur = translations.get("ur")
    if not (ur and ur.get("sections")):
        # Asal Urdu-script translation abhi tak nahi bani — is dafa video
        # skip karte hain (Roman Urdu text ko Urdu voice se ab kabhi nahi
        # bulwate, kyunki uski pronunciation saaf/samajh mein nahi aati).
        # Jaise hi translation ban jayegi (heal ya agle din ke lesson ke
        # sath), yeh video khud-b-khud agli build par ban jayegi.
        msg = f"[{slug}] Day {day_num} video skip: Urdu-script translation abhi maujood nahi (saaf awaaz ke liye zaroori)."
        print(msg, file=sys.stderr)
        return
    title = ur.get("title", lesson["title"])
    preamble = ur.get("preamble", "")
    sections = [(s.get("label", ""), s.get("content", "")) for s in ur.get("sections", [])]

    voice = NARRATION_VOICE_UR  # hamesha pure Urdu, female awaaz

    script_text = _build_narration_text(title, preamble, sections)
    if not script_text:
        return

    padded = f"{day_num:03d}"
    work_dir = os.path.join(VIDEOS_DIR, slug)
    os.makedirs(work_dir, exist_ok=True)
    txt_path = os.path.join(work_dir, f"day-{padded}.narration.txt")
    mp3_path = os.path.join(work_dir, f"day-{padded}.mp3")
    mp4_path = os.path.join(work_dir, f"day-{padded}.mp4")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(script_text)

    if not _run_edge_tts(txt_path, voice, mp3_path, rate=NARRATION_RATE_UR):
        # Koi English/male fallback nahi — TTS fail ho to video is baar
        # sirf skip hoti hai (agli build par phir try hogi), Urdu female
        # awaaz ke ilawa kabhi kisi aur voice par switch nahi hota.
        msg = f"[{slug}] Day {day_num} video skip: Urdu TTS ({voice}) fail."
        print(msg, file=sys.stderr)
        log_error(msg)
        return

    # Pehle behtar "Ken Burns zoom + captions" wala free jugaad try karo
    # (asal AI video generation paid hoti hai, yeh iski jagah). Fail ho
    # jaye (ffmpeg build mein subtitles/zoompan support na ho waghera)
    # to purane simple still-image version par fallback ho jata hai —
    # video kabhi bhi banna band nahi hota.
    srt_path = os.path.join(work_dir, f"day-{padded}.srt")
    duration = _get_audio_duration(mp3_path)
    has_srt = duration and _build_caption_srt(script_text, duration, srt_path)
    made = False
    if _run_ffmpeg_kenburns_captions(image_source_path, mp3_path, srt_path if has_srt else None, mp4_path):
        made = True
        print(f"[{slug}] Day {day_num} AI video explanation ban gayi (Ken Burns zoom + captions).")
    elif _run_ffmpeg_image_audio(image_source_path, mp3_path, mp4_path):
        made = True
        print(f"[{slug}] Day {day_num} AI video explanation ban gayi (free, voice+slide — fallback).")

    if not made:
        msg = f"[{slug}] Day {day_num} video skip: ffmpeg dono attempts fail."
        print(msg, file=sys.stderr)
        log_error(msg)


def publish_lesson_video(slug, day_num):
    """Agar us lesson ka video maujood ho, docs/courses/<slug>/posts/videos/
    mein copy kar deta hai aur lesson page ke liye relative href return
    karta hai — warna None."""
    padded = f"{day_num:03d}"
    src = os.path.join(VIDEOS_DIR, slug, f"day-{padded}.mp4")
    if not os.path.exists(src):
        return None
    dest_dir = os.path.join(DOCS_DIR, "courses", slug, "posts", "videos")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"day-{padded}.mp4")
    shutil.copyfile(src, dest)
    return f"videos/day-{padded}.mp4"


# =====================================================================
# 🎬 AGNES AI VIDEO GENERATION — Mentor-style AI explainer videos
# =====================================================================
AGNES_API_URL = "https://apihub.agnes-ai.com/v1/videos"
AGNES_STATUS_URL = "https://apihub.agnes-ai.com/v1/videos/{job_id}/status"


def generate_agnes_video(slug, lesson, course_name, max_attempts=10):
    """
    Agnes AI se mentor-style video generate karta hai.
    Har lesson ke liye professional avatar-based explainer video.
    """
    if not AGNES_API_KEY:
        print(f"[{slug}] Agnes API key missing, video skip.")
        return None

    # Lesson content ko script mein convert karein
    script_parts = [lesson['title']]
    if lesson.get('preamble'):
        script_parts.append(lesson['preamble'])
    for label, content in lesson.get('sections', []):
        if content:
            script_parts.append(f"{label}: {content}")
    script = "\n\n".join(script_parts)

    # Limit script length (Agnes has limits)
    if len(script) > 2000:
        script = script[:2000]

    # Agnes API payload
    payload = {
        "script": script,
        "language": "ur",          # Urdu explanation
        "speaker_id": "mentor",    # Professional mentor avatar
        "duration": 60,            # 1 minute video
        "style": "educational"     # Mentor-style
    }

    headers = {
        "Authorization": f"Bearer {AGNES_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # 1. Submit video generation request
        print(f"[{slug}] Day {lesson['day']}: Agnes video generation start...")
        response = requests.post(AGNES_API_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        job_data = response.json()
        job_id = job_data.get("job_id") or job_data.get("id")

        if not job_id:
            print(f"[{slug}] No job_id in response: {job_data}")
            return None

        # 2. Poll for completion
        for attempt in range(max_attempts):
            status_response = requests.get(
                AGNES_STATUS_URL.format(job_id=job_id),
                headers=headers,
                timeout=30
            )
            status_data = status_response.json()
            status = status_data.get("status", "")

            if status == "completed":
                # Download video
                video_url = status_data.get("video_url") or status_data.get("output_url")
                if not video_url:
                    print(f"[{slug}] No video_url in response")
                    return None

                video_data = requests.get(video_url, timeout=60).content

                # Save locally
                padded = f"{lesson['day']:03d}"
                video_dir = os.path.join(VIDEOS_DIR, slug)
                os.makedirs(video_dir, exist_ok=True)
                video_path = os.path.join(video_dir, f"day-{padded}.mp4")

                with open(video_path, "wb") as f:
                    f.write(video_data)

                print(f"[{slug}] Day {lesson['day']} ✅ Agnes video ban gayi!")
                return video_path

            elif status in ["failed", "error"]:
                error_msg = status_data.get("error", "Unknown error")
                print(f"[{slug}] Agnes video failed: {error_msg}")
                return None

            else:
                print(f"[{slug}] Day {lesson['day']} Processing... ({attempt+1}/{max_attempts})")
                time.sleep(10)  # Wait 10 seconds between checks

        print(f"[{slug}] Day {lesson['day']} Timeout after {max_attempts} attempts")
        return None

    except requests.exceptions.Timeout:
        print(f"[{slug}] Day {lesson['day']} Agnes API timeout")
        return None
    except Exception as e:
        print(f"[{slug}] Day {lesson['day']} Agnes API error: {e}")
        return None


# =====================================================================
# 💬 GISCUS COMMENTS — GitHub Discussions par based, 100% free.
# Setup (ek dafa): 1) repo Settings → General → Discussions ON karein.
# 2) https://giscus.app par jaa kar apna repo enter karein, mapping/theme
# choose karein — page us script tag mein aapko REPO_ID aur CATEGORY_ID
# de gi. Neeche 4 constants fill kar dein — khaali hon to comments box
# khud show nahi hota.
# =====================================================================
GISCUS_REPO = os.environ.get("GISCUS_REPO", "")            # e.g. "gulishop/fkc-trading"
GISCUS_REPO_ID = os.environ.get("GISCUS_REPO_ID", "")
GISCUS_CATEGORY = os.environ.get("GISCUS_CATEGORY", "General")
GISCUS_CATEGORY_ID = os.environ.get("GISCUS_CATEGORY_ID", "")
GISCUS_ENABLED = bool(GISCUS_REPO and GISCUS_REPO_ID and GISCUS_CATEGORY_ID)


def giscus_comments_html():
    """Lesson page ke neeche GitHub-Discussions-based comment box — sirf
    tab render hota hai jab GISCUS_* config poori fill ho."""
    if not GISCUS_ENABLED:
        return ""
    return f"""
    <div class="card no-print" style="margin-top:16px;">
      <p class="muted" style="margin:0 0 8px;">💬 Sawal ya comment likhein</p>
      <script src="https://giscus.app/client.js"
        data-repo="{html.escape(GISCUS_REPO)}"
        data-repo-id="{html.escape(GISCUS_REPO_ID)}"
        data-category="{html.escape(GISCUS_CATEGORY)}"
        data-category-id="{html.escape(GISCUS_CATEGORY_ID)}"
        data-mapping="pathname"
        data-strict="0"
        data-reactions-enabled="1"
        data-emit-metadata="0"
        data-input-position="top"
        data-theme="preferred_color_scheme"
        data-lang="ur"
        crossorigin="anonymous"
        async>
      </script>
    </div>"""


# Har build ka apna unique stamp — version.json mein likha jata hai taake
# khuli hui tabs/PWA khud check kar sakein ke naya build aaya hai ya nahi
# (live-update mechanism, neeche live_update_script_html dekhein).
BUILD_STAMP = datetime.datetime.utcnow().isoformat()

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
# 🎓 Certificates — progress tracking (localStorage, static site — koi
# login/database zaroori nahi), WhatsApp par apply, aur (optional)
# Firebase backend jisse aap (Fazul Khan) admin panel se requests dekh
# kar auto-signature wala certificate generate kar saken.
# ---------------------------------------------------------------------
CERTIFICATE_FEE_DEFAULT = "Rs. 500"


def course_certificate_fee(course):
    """Har course ka apna certificate fee ho sakta hai — COURSES dictionary
    mein us course ke andar "certificate_fee": "Rs. 800" jaisi key add
    karke override kar dein, warna CERTIFICATE_FEE_DEFAULT use hoga."""
    return course.get("certificate_fee", CERTIFICATE_FEE_DEFAULT)


# Firebase sirf admin certificate-panel (docs/admin-certificates.html) ke
# liye use hota hai — jab tak neeche config khaali hai, WhatsApp wala
# apply-flow bilkul normal chalta rahega (Firebase yahan optional hai).
# Setup ke steps is response ke aakhir mein diye hain.
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyA-HvEX3q6QChPRPJsuKZg6CYL6cYo5jd0",
    "authDomain": "fkc-trading--certificate.firebaseapp.com",
    "projectId": "fkc-trading--certificate",
    "storageBucket": "fkc-trading--certificate.firebasestorage.app",
    "messagingSenderId": "657947527934",
    "appId": "1:657947527934:web:5671cf0cf8b52603c3b3af",
}
FIREBASE_ENABLED = bool(FIREBASE_CONFIG.get("apiKey"))


def firebase_init_html():
    """Firebase compat SDK load + init — sirf tab jab FIREBASE_CONFIG fill
    ho. window.fkcSaveCertRequest() define karta hai jise certificate
    apply-flow call karta hai taake request Firestore mein bhi save ho
    jaye (admin panel ke liye), WhatsApp message ke sath-sath.
    Progress-sync ke liye do functions bhi: fkcSyncProgressUp(code) —
    is device ka localStorage progress ek 6-digit code ke sath Firestore
    mein save karta hai; fkcSyncProgressDown(code) — doosri device par
    wahi code daal kar progress wapas le aata hai."""
    if not FIREBASE_ENABLED:
        return ""
    return f"""
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore-compat.js"></script>
<script>
(function(){{
  try{{
    firebase.initializeApp({json.dumps(FIREBASE_CONFIG)});
    window.fkcDb = firebase.firestore();
    window.fkcSaveCertRequest = function(data){{
      try{{
        window.fkcDb.collection("certificate_requests").add({{
          slug: data.slug, course: data.course, name: data.name,
          fee: data.fee, status: "pending",
          created: firebase.firestore.FieldValue.serverTimestamp()
        }});
      }}catch(e){{}}
    }};

    window.fkcSyncProgressUp = function(code, onDone){{
      try{{
        var data = localStorage.getItem("fkc_progress") || "{{}}";
        window.fkcDb.collection("progress_sync").doc(code).set({{
          progress: data, updated: firebase.firestore.FieldValue.serverTimestamp()
        }}).then(function(){{ if(onDone) onDone(true); }})
          .catch(function(){{ if(onDone) onDone(false); }});
      }}catch(e){{ if(onDone) onDone(false); }}
    }};

    window.fkcSyncProgressDown = function(code, onDone){{
      try{{
        window.fkcDb.collection("progress_sync").doc(code).get().then(function(doc){{
          if(doc.exists && doc.data().progress){{
            localStorage.setItem("fkc_progress", doc.data().progress);
            if(onDone) onDone(true);
          }} else {{ if(onDone) onDone(false); }}
        }}).catch(function(){{ if(onDone) onDone(false); }});
      }}catch(e){{ if(onDone) onDone(false); }}
    }};
  }}catch(e){{}}
}})();
</script>"""


def certificate_progress_script_html():
    """Lesson-complete tracking + course progress bar + certificate-apply
    button — sab kuch localStorage ("fkc_progress") mein, kyunki site
    static hai (bina login/database ke). Jab student certificate ke liye
    apply karta hai, naam poochta hai aur WhatsApp khol deta hai jisme
    course ka naam + student ka naam + fee pehle se likha hota hai."""
    return f"""<script>
(function(){{
  function getProgress(){{
    try{{ return JSON.parse(localStorage.getItem("fkc_progress")||"{{}}"); }}catch(e){{ return {{}}; }}
  }}
  function setProgress(obj){{ localStorage.setItem("fkc_progress", JSON.stringify(obj)); }}
  function isDone(slug, lessonId){{
    var p = getProgress();
    return !!(p[slug] && p[slug].indexOf(lessonId) !== -1);
  }}

  window.fkcToggleComplete = function(btn){{
    var slug = btn.getAttribute("data-slug");
    var lessonId = btn.getAttribute("data-lesson");
    var p = getProgress();
    if(!p[slug]) p[slug] = [];
    var idx = p[slug].indexOf(lessonId);
    if(idx === -1){{
      p[slug].push(lessonId);
      btn.textContent = "✅ Complete Ho Gaya";
      btn.classList.add("done");
    }} else {{
      p[slug].splice(idx,1);
      btn.textContent = "✅ Complete Mark Karein";
      btn.classList.remove("done");
    }}
    setProgress(p);
  }};

  window.fkcApplyCertificate = function(slug, courseName, fee){{
    var name = prompt("Apna poora naam likhein (certificate par yahi naam print hoga):");
    if(!name || !name.trim()) return;
    name = name.trim();
    var text = "🎓 Certificate Application\\n\\nCourse: " + courseName +
      "\\nStudent Name: " + name + "\\nCertificate Fee: " + fee;
    if(window.fkcSaveCertRequest){{
      window.fkcSaveCertRequest({{slug: slug, course: courseName, name: name, fee: fee}});
    }}
    var wa = "https://wa.me/{BRAND_WHATSAPP_DIGITS}?text=" + encodeURIComponent(text);
    window.open(wa, "_blank");
  }};

  window.fkcShowSyncCode = function(){{
    if(!window.fkcSyncProgressUp){{ alert("Sync abhi ready nahi (Firebase load ho raha hai), thodi dair mein try karein."); return; }}
    var code = Math.random().toString(36).substring(2,8).toUpperCase();
    window.fkcSyncProgressUp(code, function(ok){{
      if(ok) alert("Yeh code doosri device par 'Code Se Wapas Layein' mein daalein:\\n\\n" + code);
      else alert("Sync fail ho gaya, dobara try karein.");
    }});
  }};

  window.fkcEnterSyncCode = function(){{
    if(!window.fkcSyncProgressDown){{ alert("Sync abhi ready nahi (Firebase load ho raha hai), thodi dair mein try karein."); return; }}
    var code = prompt("Wo code daalein jo pehli device par bana tha:");
    if(!code || !code.trim()) return;
    window.fkcSyncProgressDown(code.trim().toUpperCase(), function(ok){{
      if(ok){{ alert("Progress wapas aa gayi ✅"); location.reload(); }}
      else alert("Yeh code nahi mila, dobara check karein.");
    }});
  }};

  document.addEventListener("DOMContentLoaded", function(){{
    var btn = document.getElementById("fkc-complete-btn");
    if(btn){{
      var slug = btn.getAttribute("data-slug");
      var lessonId = btn.getAttribute("data-lesson");
      if(isDone(slug, lessonId)){{
        btn.textContent = "✅ Complete Ho Gaya";
        btn.classList.add("done");
      }}
    }}
    var wrap = document.getElementById("fkc-progress-wrap");
    if(wrap){{
      var slug = wrap.getAttribute("data-slug");
      var total = parseInt(wrap.getAttribute("data-total"),10) || 0;
      var p = getProgress();
      var done = (p[slug]||[]).length;
      if(done > total) done = total;
      var pct = total > 0 ? Math.round((done/total)*100) : 0;
      var fill = document.getElementById("fkc-progress-fill");
      var txt = document.getElementById("fkc-progress-text");
      if(fill) fill.style.width = pct + "%";
      if(txt) txt.textContent = done + "/" + total + " lessons complete";

      // Certificate ab lesson-count par nahi, TIME par unlock hota hai:
      // jis din student pehli baar is course ka page kholta hai, uski
      // date "fkc_start" mein save ho jati hai; usse 60 din (~2 months)
      // baad certificate button apne aap dikh jata hai — chahe naye
      // lessons roz aate rehte hain, course kabhi "khatam" nahi hota.
      var CERT_UNLOCK_DAYS = 60;
      var starts = {{}};
      try{{ starts = JSON.parse(localStorage.getItem("fkc_start")||"{{}}"); }}catch(e){{}}
      if(!starts[slug]){{
        starts[slug] = new Date().toISOString();
        localStorage.setItem("fkc_start", JSON.stringify(starts));
      }}
      var startDate = new Date(starts[slug]);
      var daysSinceStart = (Date.now() - startDate.getTime()) / 86400000;
      var daysLeft = Math.max(0, Math.ceil(CERT_UNLOCK_DAYS - daysSinceStart));

      var certBtn = document.getElementById("fkc-cert-btn");
      if(certBtn){{
        if(daysSinceStart >= CERT_UNLOCK_DAYS){{
          certBtn.style.display = "inline-flex";
        }} else if(txt){{
          txt.textContent = done + "/" + total + " lessons complete — certificate " +
            daysLeft + " din mein unlock hoga";
        }}
      }}
    }}
  }});
}})();
</script>"""


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
        f"navigator.serviceWorker.register('{sw_href}').then(function(reg){{"
        "reg.update();"
        "setInterval(function(){reg.update();},20000);"
        # app background se wapas khulte hi turant naya version check karo,
        # taake 20s wait na karna pade
        "document.addEventListener('visibilitychange',function(){"
        "if(!document.hidden){reg.update();}"
        "});"
        "window.addEventListener('focus',function(){reg.update();});"
        "}}).catch(function(){});"
        "var fkcReloaded=false;"
        "navigator.serviceWorker.addEventListener('controllerchange',function(){"
        "if(fkcReloaded)return;fkcReloaded=true;window.location.reload();"
        "});"
        "});}</script>"
    )


def build_manifest_json():
    manifest = {
        "name": BRAND_NAME,
        "short_name": BRAND_NAME[:12],
        "start_url": ".",
        "scope": ".",
        "display": "fullscreen",
        "display_override": ["fullscreen", "standalone"],
        "background_color": "#0B1220",
        "theme_color": "#0B1220",
        "icons": [
            {"src": ICON_192, "sizes": "192x192", "type": "image/png"},
            {"src": ICON_512, "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ],
    }
    return json.dumps(manifest, ensure_ascii=False, indent=2)


def build_service_worker_js():
    # Build timestamp is a comment (not code) so it changes every run —
    # browser sirf byte-for-byte diff check karta hai naya SW detect
    # karne ke liye. Bina isके, agar SW file ka logic kabhi na badle,
    # to browser kabhi update hi nahi samjhega.
    build_stamp = datetime.datetime.utcnow().isoformat()
    return (
        f"// build: {build_stamp}\n"
        "self.addEventListener('install',e=>self.skipWaiting());\n"
        "self.addEventListener('activate',e=>self.clients.claim());\n"
        "self.addEventListener('fetch',e=>{\n"
        "  e.respondWith(fetch(e.request,{cache:'no-store'}).catch(()=>caches.match(e.request)));\n"
        "});\n"
    )


def ensure_pwa_icons():
    """PWA install icon ke liye docs/icons/icon-192.png aur icon-512.png
    chahiye. Agar koi already (manually) upload ki hui ho to usay chorr
    dete hain. Missing size ke liye pehle asal brand logo (docs/logo.png)
    se hi icon banate hain — sirf agar wo logo bhi na mile to fallback
    ke tor par generic initials wala icon banta hai (taake install
    button par icon hamesha kuch na kuch dikhe, khaali na rahe)."""
    if not PIL_AVAILABLE:
        return
    icons_dir = os.path.join(DOCS_DIR, "icons")
    os.makedirs(icons_dir, exist_ok=True)
    logo_path = os.path.join(DOCS_DIR, BRAND_LOGO)
    logo_img = None
    if os.path.exists(logo_path):
        try:
            logo_img = Image.open(logo_path).convert("RGBA")
        except Exception as e:
            print(f"Logo ({logo_path}) icon ke liye load nahi ho saka: {e}", file=sys.stderr)

    initials = "".join(w[0] for w in BRAND_NAME.split()[:3]).upper() or "F"
    for rel_path, size in ((ICON_192, 192), (ICON_512, 512)):
        full_path = os.path.join(DOCS_DIR, rel_path)
        if os.path.exists(full_path):
            continue  # already manually uploaded — mat overwrite karo

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        if logo_img is not None:
            # asal logo ko square canvas ke beech mein fit karte hain
            # (aspect ratio kharab kiye bagair), taake install icon
            # bilkul wahi dikhe jo brand ka asal logo hai
            canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            fitted = logo_img.copy()
            fitted.thumbnail((size, size), Image.LANCZOS)
            x = (size - fitted.width) // 2
            y = (size - fitted.height) // 2
            canvas.paste(fitted, (x, y), fitted if fitted.mode == "RGBA" else None)
            canvas.convert("RGB").save(full_path, "PNG")
            continue

        img = Image.new("RGB", (size, size), "#0B1220")
        draw = ImageDraw.Draw(img)
        pad = int(size * 0.08)
        draw.rounded_rectangle(
            [pad, pad, size - pad, size - pad], radius=int(size * 0.16), fill="#0056D2"
        )
        font_size = int(size * 0.4)
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size
            )
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), initials, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(
            ((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
            initials, fill="#FFFFFF", font=font,
        )
        img.save(full_path, "PNG")


def pwa_install_prompt_html():
    """Naye visitors ko 'Add to Home Screen' ka nudge deta hai — Android
    par native install prompt trigger karta hai, iOS Safari par manual
    instructions dikhata hai (kyunki iOS beforeinstallprompt support
    nahi karta). Agar already installed (standalone mode) ho to kabhi
    nahi dikhta. Ek baar band karne par 7 din tak dobara nahi aata."""
    return """
<style>
#pwa-install-banner{position:fixed;left:12px;right:12px;bottom:12px;
background:#0B1220;color:#fff;border-radius:14px;padding:14px 16px;
display:none;align-items:center;gap:12px;box-shadow:0 8px 24px rgba(0,0,0,.25);
z-index:9999;font-size:.88em;}
#pwa-install-banner.show{display:flex;}
#pwa-install-banner .txt{flex:1;line-height:1.4;}
#pwa-install-banner .txt b{display:block;margin-bottom:2px;}
#pwa-install-banner button{background:#0056D2;color:#fff;border:none;
border-radius:10px;padding:8px 14px;font-weight:600;font-size:.92em;
flex-shrink:0;}
#pwa-install-banner .close-x{background:transparent;color:#9aa4b2;
padding:4px 6px;font-size:1.1em;}
</style>
<div id="pwa-install-banner">
  <div class="txt"><b>📲 App install karein</b><span id="pwa-install-txt">Fullscreen experience aur roz ke reminders ke liye Home Screen par add karein.</span></div>
  <button id="pwa-install-btn" type="button">Install</button>
  <button class="close-x" type="button" id="pwa-install-close" aria-label="Band karein">✕</button>
</div>
<script>
(function(){
  var KEY = "fkc_install_dismissed_until";
  var banner = document.getElementById("pwa-install-banner");
  if(!banner) return;

  function isStandalone(){
    return window.matchMedia("(display-mode: standalone)").matches
      || window.matchMedia("(display-mode: fullscreen)").matches
      || window.navigator.standalone === true;
  }
  function dismissedRecently(){
    var until = parseInt(localStorage.getItem(KEY) || "0", 10);
    return Date.now() < until;
  }
  function dismiss(){
    localStorage.setItem(KEY, String(Date.now() + 7*24*60*60*1000));
    banner.classList.remove("show");
  }
  document.getElementById("pwa-install-close").addEventListener("click", dismiss);

  if(isStandalone() || dismissedRecently()) return;

  var isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent) && !window.MSStream;

  if(isIOS){
    document.getElementById("pwa-install-txt").textContent =
      "Safari ke Share ⬆️ button se 'Add to Home Screen' choose karein.";
    banner.classList.add("show");
    document.getElementById("pwa-install-btn").style.display = "none";
    return;
  }

  var deferredPrompt = null;
  window.addEventListener("beforeinstallprompt", function(e){
    e.preventDefault();
    deferredPrompt = e;
    banner.classList.add("show");
  });
  document.getElementById("pwa-install-btn").addEventListener("click", function(){
    if(!deferredPrompt) return;
    deferredPrompt.prompt();
    deferredPrompt.userChoice.finally(function(){
      banner.classList.remove("show");
      deferredPrompt = null;
    });
  });
  window.addEventListener("appinstalled", function(){ banner.classList.remove("show"); });
})();
</script>"""


VERSION_FILENAME = "version.json"


def live_update_script_html(version_href):
    """Har {LIVE_UPDATE_INTERVAL}ms mein version.json check karta hai
    (cache:no-store se, taake browser/CDN cache kabhi beech mein na aaye).
    Naya build detect hote hi page khud reload ho jata hai — normal
    browser tab ho ya installed PWA, dono mein kaam karta hai, aur
    service worker update se bhi zyada tez hai."""
    return f"""<script>
(function(){{
  var FKC_BUILD = {json.dumps(BUILD_STAMP)};
  function fkcCheckVersion(){{
    fetch("{version_href}?t=" + Date.now(), {{cache:"no-store"}})
      .then(function(r){{ return r.json(); }})
      .then(function(data){{
        if(data && data.build && data.build !== FKC_BUILD){{
          window.location.reload();
        }}
      }})
      .catch(function(){{}});
  }}
  setInterval(fkcCheckVersion, 8000);
  document.addEventListener("visibilitychange", function(){{
    if(!document.hidden) fkcCheckVersion();
  }});
  window.addEventListener("focus", fkcCheckVersion);
}})();
</script>"""


def pwa_extra_for(logo_href):
    if logo_href.endswith(BRAND_LOGO):
        prefix = logo_href[: -len(BRAND_LOGO)]
    else:
        prefix = ""
    manifest_href = prefix + MANIFEST_FILENAME
    icon_href = prefix + ICON_192
    sw_href = prefix + SW_FILENAME
    version_href = prefix + VERSION_FILENAME
    return (
        pwa_head_extra(manifest_href, icon_href)
        + pwa_register_script(sw_href)
        + live_update_script_html(version_href)
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


# ---------------------------------------------------------------------
# Gemini fallback — jab Mistral (translation ke liye khaaskar Urdu/Sindhi
# jaise scripts mein) baar-baar degenerate/khaali output de, to isko
# dusra AI provider ke tor par try karte hain taake lesson skip na ho.
# ---------------------------------------------------------------------
GEMINI_MODEL_NAMES = ["gemini-flash-latest", "gemini-flash-lite-latest"]
GEMINI_URL_TMPL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _gemini_call_once(model_name, prompt_text, max_retries=3):
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt_text}]}],
    }).encode()
    url = GEMINI_URL_TMPL.format(model=model_name)

    wait = 15
    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                err_body = "(body nahi mil saka)"
            print(f"Gemini {e.code} detail ({model_name}, attempt {attempt}): {err_body}", file=sys.stderr)

            if e.code == 403:
                print("Gemini 403 — key/permission issue, retry se theek nahi hoga.", file=sys.stderr)
                raise
            if e.code == 404:
                raise  # caller agla model try karega
            if e.code in (429, 500, 502, 503) and attempt < max_retries:
                print(f"Gemini {e.code} mila ({model_name}, attempt {attempt}) — {wait}s ruk kar dobara koshish...", file=sys.stderr)
                time.sleep(wait)
                wait = min(wait * 2, 90)
                continue
            raise


def gemini_generate(prompt_text, max_retries=3):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY set nahi hai.")

    data = None
    last_error = None
    for model_name in GEMINI_MODEL_NAMES:
        try:
            data = _gemini_call_once(model_name, prompt_text, max_retries=max_retries)
            break
        except urllib.error.HTTPError as e:
            last_error = e
            if e.code == 404:
                print(f"Gemini model '{model_name}' 404 — agla model try kar rahe hain...", file=sys.stderr)
                continue
            raise
    if data is None:
        raise last_error

    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError):
        print("Gemini response se text nahi mila:", data, file=sys.stderr)
        return ""


def build_kids_safety_prompt(course, day_num, topic_hint, prev):
    """Bachon ki hifazat wale course ke liye alag, nazuk andaz ka prompt —
    koi 'practice/mini-project' jo bacha akela kare nahi (is jagah
    ammi/abbu ke sath baat karne ki activity), koi graphic/explicit
    detail nahi, sirf warm, simple, age 5-10 ke liye samajh aane wali
    zaban, aur hamesha trusted adult ko batane ka message."""
    return (
        f"Tum bachon (age 5-10) ke liye 'Bachon Ki Hifazat' course ke ek pyaar bhare, "
        f"nazuk andaz wale teacher ho, Roman Urdu mein — is tarah likho ke ek parent apne "
        f"bachay ko zor se padh kar sunaye. Yeh Day {day_num} hai. "
        f"Aaj ka topic: '{topic_hint}'. "
        f"Pichle dinon ke titles (dobara mat likhna): {prev}. "
        "Zaruri usool: koi graphic ya explicit tafseel bilkul mat likho, sirf general/safe "
        "zaban use karo (jaise school mein sikhaya jata hai). Hamesha yeh message rakho ke "
        "bachay ka jism sirf uska hai, use 'na' kehne ka pura huq hai, aur agar kuch bhi ajeeb "
        "ya uncomfortable lage to foran ammi/abbu ya kisi trusted bade insaan ko batana chahiye "
        "— chahe kisi ne kaha ho ke yeh 'secret' rakho. Tone hamesha reassuring aur pyaar bhara "
        "rakho, dara wala nahi. "
        "Format bilkul yeh follow karo, aur kuch mat likho: "
        f"'# Day {day_num} — <chhota, pyaara title>' phir "
        "'**Concept:**' (2-3 simple lines mein aaj ka safety point samjhao, seedha bachay se baat karte hue), "
        "'**Chhoti Kahani:**' (ek chhoti, reassuring misal ya scenario jisse bacha samajh sake — koi graphic detail nahi), "
        "'**Ammi Abbu Ke Sath Baat Karein:**' (1 simple sawal jo parent bachay se poochein taake woh khul kar baat kare), "
        "'**Yaad Rakhein:**' (1 chhota, positive safety reminder). "
        "Total length chhoti rakho (max ~200 words), simple alfaz, koi 'Mini Project' ya 'Answer Key' section mat likho."
    )


def build_prompt(slug, course, day_num, previous_titles):
    topics = course["topics"]
    topic_hint = topics[(day_num - 1) % len(topics)]
    prev = "; ".join(previous_titles[-6:]) if previous_titles else "(koi nahi, yeh pehla lesson hai)"
    if course.get("for_kids"):
        return build_kids_safety_prompt(course, day_num, topic_hint, prev)
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


# ---------------------------------------------------------------------
# 🌐 Lesson translations — Roman Urdu (jo already har lesson ka default
# hai) ke sath-sath, Urdu aur Sindhi script mein bhi lesson generate
# hota hai. Cache ki jati hai (day-XXX.ur.json / day-XXX.sd.json) taake
# dobara build hone par translation dobara na maangni pade. Fail ho
# jaye to sirf wo zaban skip hoti hai — Roman Urdu wala lesson kabhi
# iski wajah se nahi rukta.
# ---------------------------------------------------------------------
TRANSLATION_LANGS = {
    "ur": "Urdu (Nastaliq/Urdu script mein)",
}


def build_translation_prompt(lang_label, title, preamble, sections, other_lang_label=None):
    sections_text = "\n".join(f"- {label}: {content}" for label, content in sections)
    extra_distinctness_rule = ""
    if other_lang_label:
        extra_distinctness_rule = (
            f"0) DHYAAN RAHE: {lang_label} aur {other_lang_label} dono Arabic-based "
            "script use karte hain lekin yeh do ALAG zabanein hain, ek dusre se "
            f"mukhtalif grammar/alfaz ke sath. Sirf {other_lang_label} wala matn copy "
            f"karke {lang_label} ka label lagana BILKUL mana hai — asli {lang_label} "
            "zaban ke apne alfaz aur jumla-saazi (sentence structure) use karo, jo "
            f"{other_lang_label} se clearly mukhtalif lage. "
        )
    preamble_rule = (
        "6) Original Preamble khaali/empty hai to translation ka 'preamble' field bhi "
        'BILKUL khaali string ("") rakho — khud se koi intro/summary line mat likho, '
        "chahe kitna bhi chhota kyun na ho. "
    ) if not (preamble or "").strip() else ""
    return (
        f"Neeche diya gaya ek lesson hai, Roman Urdu mein likha hua. Isay poora "
        f"{lang_label} translate karo — matlab, tone, aur structure bilkul wahi rakho, "
        "sirf zaban/script badlo, kuch add ya remove mat karo. "
        f"Zaroori rules: {extra_distinctness_rule}"
        "1) Poora jawab Arabic/Nastaliq huroof (جیسے: ا، ب، پ، ت، ٹ، ث، ج، چ، ح، خ، د، "
        "ڈ، ر، ڑ، ز، ژ، س، ش، ص، ض، ط، ظ، ع، غ، ف، ق، ک، گ، ل، م، ن، و، ہ، ی، ے) mein "
        "likho — Roman/Latin alphabet (a, b, c...) mein HARGIZ kuch mat likho, khaas "
        "naam (jaise Midjourney, ChatGPT, YouTube) chhod kar. "
        "2) HAR sentence ko poora script mein likho — koi bhi English ya Roman Urdu "
        "sentence jaise-taise (untranslated) mat chhodo. "
        "3) 'preamble' aur har section ka 'content' ek dusre se ALAG aur UNIQUE hona "
        "chahiye — koi bhi paragraph ya jumla do jagah repeat/copy-paste mat karo. "
        "4) Kisi bhi field ke andar ek hi jumla ya phrase baar baar loop mein mat likho. "
        "5) Agar matn mein koi code block ho (```...``` ke andar), usay BILKUL "
        "waisa ka waisa (as-is) rehne do — code, variable names, keywords (for, "
        "int, print, etc.) translate mat karo, sirf agar code ke andar koi "
        "English comment ho to wo translate kar sakte ho. "
        f"{preamble_rule}"
        "SIRF valid JSON return karo, koi extra text, koi markdown code-fence nahi, "
        "bilkul is shape mein: "
        '{"title": "...", "preamble": "...", "sections": [{"label": "...", "content": "..."}]}. '
        f"Original Title: {title}\n"
        f"Original Preamble: {preamble}\n"
        f"Original Sections:\n{sections_text}"
    )


def _parse_translation_json(raw):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"```\s*$", "", cleaned)
    data = json.loads(cleaned.strip())
    if not isinstance(data, dict) or "sections" not in data:
        raise ValueError("translation JSON ka shape galat hai")
    return data


def _is_degenerate_text(text, min_len=40):
    """AI kabhi kabhi ek chhota word/phrase loop mein baar baar repeat kar
    deta hai (jaise 'jaa'oon jaa'oon jaa'oon...'). Yeh function aisa
    repetitive/garbled output detect karta hai taake wo cache na ho."""
    if not text:
        return False
    words = text.split()
    if len(words) < 8 or len(text) < min_len:
        return False
    unique_ratio = len(set(words)) / len(words)
    if unique_ratio < 0.35:
        return True
    # ek hi word ka lagataar 5+ dafa repeat hona bhi degenerate output hai
    run = 1
    for i in range(1, len(words)):
        if words[i] == words[i - 1]:
            run += 1
            if run >= 5:
                return True
        else:
            run = 1
    return False


def _normalize_for_compare(text):
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _texts_are_near_duplicate(a, b, min_len=40):
    """Detect jab do fields (jaise preamble aur pehla section) mein bilkul
    ya lagbhag wahi paragraph repeat ho jaye — jaise 'Concept' wala matn
    preamble mein bhi aa gaya aur uske section content mein bhi dobara aa
    gaya (screenshot wala Sindhi bug)."""
    na, nb = _normalize_for_compare(a), _normalize_for_compare(b)
    if len(na) < min_len or len(nb) < min_len:
        return False
    if na == nb:
        return True
    shorter, longer = (na, nb) if len(na) <= len(nb) else (nb, na)
    # agar chhota text lagbhag pura bade text ke andar hi mil jaye, to yeh
    # copy-paste duplication hai, alag translation nahi
    return shorter in longer and len(shorter) / len(longer) > 0.6


def _script_ratio(text):
    """Text mein Arabic-script (Urdu/Sindhi) letters ka ratio nikalta hai,
    Latin letters ke muqable mein — taake pata chale ke translation asal
    mein Urdu/Sindhi script mein hai ya sirf Roman/Latin text hai jo copy
    karke thoda idhar-udhar kar diya gaya."""
    arabic = len(re.findall(r"[\u0600-\u06FF\u0750-\u077F]", text or ""))
    latin = len(re.findall(r"[A-Za-z]", text or ""))
    total = arabic + latin
    if total == 0:
        return None  # sirf numbers/symbols — kuch nahi bata sakte
    return arabic / total


def _strip_code_blocks(text):
    """Script-ratio check se pehle fenced code (```...```) hata do — code
    hamesha English/Latin mein rehta hai (jaisa hona bhi chahiye), isay
    'Urdu script kam hai' samajh kar translation reject nahi honi chahiye."""
    return re.sub(r"```.*?```", " ", text or "", flags=re.DOTALL)


def _script_matches_lang(data, code):
    """ur translation mein zyada tar matn Arabic/Urdu script mein hona
    chahiye. Agar AI ne sirf Roman Urdu jaisa Latin text de diya (screenshot
    wala bug — 'اردو' tab pe bhi Latin text dikh raha tha), to isay bhi
    garbled/bad translation samjho aur dobara generate karwao. Code blocks
    (jaise C++/Python examples) is calculation mein shaamil nahi hote —
    warna code-heavy lessons (jaise Python course) har baar fail ho jate."""
    if code != "ur":
        return True
    parts = [data.get("title", ""), data.get("preamble", "")]
    for sec in data.get("sections", []) or []:
        if isinstance(sec, dict):
            parts.append(sec.get("label", ""))
            parts.append(_strip_code_blocks(sec.get("content", "")))
    combined = " ".join(p for p in parts if p)
    ratio = _script_ratio(combined)
    if ratio is None:
        return True
    return ratio >= 0.6


def _word_overlap_ratio(a, b, min_len=40):
    """Jaccard-style overlap — jab do paragraphs alfaz thoda idhar-udhar
    karke bhi wahi baat dobara keh rahe hon (jaise preamble ne 'Concept'
    section wali baat apne alfaz mein dobara likh di), to substring wala
    check miss kar sakta hai, isliye ye zyada lenient duplicate-detector
    hai."""
    na, nb = _normalize_for_compare(a), _normalize_for_compare(b)
    if len(na) < min_len or len(nb) < min_len:
        return 0.0
    wa, wb = set(na.split()), set(nb.split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _flatten_translation_text(data):
    """Ek translation dict (title/preamble/sections) ko ek single string mein
    jod deta hai, taake do languages ke poore content ko compare kiya ja
    sake (cross-language duplicate check ke liye)."""
    if not data:
        return ""
    parts = [data.get("title", ""), data.get("preamble", "")]
    for sec in data.get("sections", []) or []:
        if isinstance(sec, dict):
            parts.append(_strip_code_blocks(sec.get("content", "")))
    return " ".join(p for p in parts if p)


def _translation_sanity_issues(data, code=None, orig_preamble=None, other_lang_data=None):
    """_translation_is_sane jaisa hi, lekin sirf True/False ki jagah
    exact wajah (reason strings) wapas karta hai — taake logs mein pata
    chal sake AI ka output KAUN se rule par reject hua (guessing na
    karni pade)."""
    issues = []
    preamble = data.get("preamble", "") or ""
    if _is_degenerate_text(preamble):
        issues.append("preamble degenerate/repetitive hai")
    if orig_preamble is not None and not orig_preamble.strip() and len(preamble.strip()) > 30:
        issues.append("original preamble khaali tha lekin translation ne naya preamble bana diya")
    sections = data.get("sections", []) or []
    contents = []
    for idx, sec in enumerate(sections):
        content = sec.get("content", "") if isinstance(sec, dict) else ""
        if _is_degenerate_text(content):
            issues.append(f"section {idx + 1} ('{sec.get('label', '')}') degenerate/repetitive hai")
        contents.append(content)
    for idx, content in enumerate(contents):
        if _texts_are_near_duplicate(preamble, content):
            issues.append(f"preamble section {idx + 1} ke content se near-duplicate hai")
        ratio = _word_overlap_ratio(preamble, content)
        if ratio > 0.7:
            issues.append(f"preamble/section {idx + 1} word-overlap {ratio:.2f} (>0.70)")
    for i in range(len(contents)):
        for j in range(i + 1, len(contents)):
            if _texts_are_near_duplicate(contents[i], contents[j]):
                issues.append(f"section {i + 1} aur section {j + 1} near-duplicate hain")
            ratio = _word_overlap_ratio(contents[i], contents[j])
            if ratio > 0.7:
                issues.append(f"section {i + 1}/section {j + 1} word-overlap {ratio:.2f} (>0.70)")
    if not _script_matches_lang(data, code):
        ratio = _script_ratio(_strip_code_blocks(_flatten_translation_text(data)))
        issues.append(f"Arabic-script ratio kaafi kam hai ({ratio})" if ratio is not None else "script ratio nahi napi ja saki")
    if other_lang_data:
        this_text = _flatten_translation_text(data)
        other_text = _flatten_translation_text(other_lang_data)
        if _texts_are_near_duplicate(this_text, other_text, min_len=60):
            issues.append("doosri zaban (ur/sd) ke translation se near-exact duplicate hai")
        else:
            ratio = _word_overlap_ratio(this_text, other_text, min_len=60)
            if ratio > 0.85:
                issues.append(f"doosri zaban (ur/sd) ke translation se word-overlap {ratio:.2f} (>0.85)")
    return issues


def _translation_is_sane(data, code=None, orig_preamble=None, other_lang_data=None):
    return not _translation_sanity_issues(data, code, orig_preamble, other_lang_data)


def get_or_generate_translations(slug, day_num, title, preamble, sections):
    padded = f"{day_num:03d}"
    course_dir = os.path.join(LESSONS_DIR, slug)
    os.makedirs(course_dir, exist_ok=True)
    translations = {}
    # "ur" pehle process hota hai (dict order), is liye jab "sd" ki baari aaye
    # tab tak translations["ur"] maujood hota hai — us se compare karke pata
    # chal jata hai ke Sindhi translation asal mein Urdu ka copy-paste to
    # nahi hai (screenshot wala bug).
    for code, lang_label in TRANSLATION_LANGS.items():
        other_code = next((c for c in TRANSLATION_LANGS if c != code), None)
        other_lang_label = TRANSLATION_LANGS.get(other_code) if other_code else None

        cache_path = os.path.join(course_dir, f"day-{padded}.{code}.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, encoding="utf-8") as f:
                    cached = json.load(f)
                if _translation_is_sane(cached, code, preamble, translations.get(other_code)):
                    translations[code] = cached
                    continue
                print(f"[{slug}] Day {day_num} {lang_label} cache garbled (repetitive/duplicate) mila, dobara generate ho raha hai.")
            except Exception:
                pass  # cache file kharab, neeche dobara generate karte hain

        last_err = None
        max_attempts = 5
        gemini_attempts = 2 if GEMINI_API_KEY else 0
        total_attempts = max_attempts + gemini_attempts
        for attempt in range(1, total_attempts + 1):
            use_gemini = attempt > max_attempts  # pehle Mistral, phir fallback Gemini
            try:
                prompt = build_translation_prompt(lang_label, title, preamble, sections, other_lang_label)
                if use_gemini:
                    print(f"[{slug}] Day {day_num} {lang_label}: Mistral {max_attempts} attempts fail, "
                          f"Gemini fallback try kar rahe hain (attempt {attempt - max_attempts})...")
                    raw = gemini_generate(prompt)
                else:
                    raw = ai_generate(prompt)
                data = _parse_translation_json(raw)
                # Original preamble khaali ho (jo 94% lessons mein hota hai,
                # kyunke lesson format mein intro paragraph hota hi nahi) aur
                # AI ne phir bhi ek chhoti si preamble likh di, to use turant
                # reject/retry karne ki bajaye khud khaali kar dete hain —
                # itni si baat par translation waste karna sahi nahi.
                if not (preamble or "").strip() and (data.get("preamble") or "").strip():
                    data["preamble"] = ""
                issues = _translation_sanity_issues(data, code, preamble, translations.get(other_code))
                if issues:
                    raise ValueError("AI output reject: " + "; ".join(issues))
                translations[code] = data
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"[{slug}] Day {day_num} {lang_label} translation ban gayi (attempt {attempt}).")
                last_err = None
                break
            except Exception as e:
                last_err = e
                print(f"[{slug}] Day {day_num} {lang_label} attempt {attempt} fail: {e}", file=sys.stderr)
            # exponential-ish backoff (3s, 6s, 9s...) — rate-limit se turant
            # dobara maarne ke bajaye thoda ruk kar retry karta hai.
            time.sleep(3 * attempt)
        if last_err is not None:
            msg = (f"[{slug}] Day {day_num} {lang_label} translation {total_attempts} attempts "
                   f"(Mistral + Gemini fallback) ke baad bhi fail, skip: {last_err}")
            print(msg, file=sys.stderr)
            log_error(msg)
    return translations


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
    translations = get_or_generate_translations(slug, day_num, title, preamble, sections)
    today = datetime.date.today().isoformat()
    return {
        "day": day_num,
        "id": f"day-{padded}",
        "date": today,
        "title": title,
        "preamble": preamble,
        "sections": sections,
        "answer_key": answer_key,
        "translations": translations,
    }


# ---------------------------------------------------------------------
# 4. HTML rendering — shared style
# ---------------------------------------------------------------------
BASE_CSS = """
:root{--paper:#F7F9FA;--panel:#FFFFFF;--line:#E3E6E8;
--ink:#1C1D1F;--muted:#6A6F73;--primary:#0056D2;--primary-dark:#00419e;
--accent:#2BAF66;--purple:#6D28D9;}
html[data-theme="dark"]{--paper:#14161A;--panel:#1D2025;--line:#2C3038;
--ink:#EDEFF2;--muted:#9AA1AB;--primary:#5B9DFF;--primary-dark:#3D7DE0;
--accent:#3FCB7E;--purple:#A78BFA;}
html[data-theme="dark"] img{opacity:.92;}
.theme-toggle{position:fixed;bottom:16px;right:16px;z-index:999;
width:44px;height:44px;border-radius:50%;border:1px solid var(--line);
background:var(--panel);color:var(--ink);font-size:19px;cursor:pointer;
box-shadow:0 2px 8px rgba(0,0,0,.15);display:flex;align-items:center;
justify-content:center;}
*{box-sizing:border-box;}
@media (prefers-reduced-motion: no-preference){
  .fade-in{animation:fadeUp .45s ease both;}
  .fade-in.d2{animation-delay:.06s;} .fade-in.d3{animation-delay:.12s;}
  @keyframes fadeUp{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:translateY(0);}}
}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:'Inter','IBM Plex Sans',sans-serif;line-height:1.55;
transition:background .2s ease,color .2s ease;}
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
.wa-btn{display:inline-flex;align-items:center;gap:6px;background:#25D366;
color:#fff!important;border-radius:16px;padding:4px 12px;font-size:.85em;
font-weight:600;margin:4px 0;text-decoration:none;}
.notify-btn{display:inline-flex;align-items:center;gap:6px;background:#fff;
color:var(--primary);border:1px solid var(--line);border-radius:20px;
font-size:.76em;font-weight:700;padding:5px 12px;cursor:pointer;
margin-top:6px;white-space:nowrap;}
.notify-btn.subscribed{background:var(--accent);color:#fff;border-color:var(--accent);}
.ccard .notify-btn{margin-top:8px;}
.progress-wrap{margin:14px 0 22px;}
.progress-track{background:var(--line);border-radius:20px;height:10px;
overflow:hidden;}
.progress-fill{background:var(--accent);height:100%;width:0%;
transition:width .4s ease;}
.complete-btn.done{background:var(--accent);}
#fkc-cert-btn{background:var(--purple);}
.lang-tabs{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;}
.lang-tab{background:var(--paper);border:1px solid var(--line);color:var(--muted);
border-radius:20px;font-size:.82em;font-weight:700;padding:6px 16px;cursor:pointer;}
.lang-tab.active{background:var(--primary);color:#fff;border-color:var(--primary);}
.lang-content[dir="rtl"]{font-family:'Noto Nastaliq Urdu',serif;line-height:2.1;
font-size:1.05em;text-align:right;}
pre{background:#0b1220;color:#e6edf3;padding:12px 14px;border-radius:10px;
overflow-x:auto;font-family:Consolas,'Fira Code',monospace;font-size:.85em;
line-height:1.5;direction:ltr;text-align:left;unicode-bidi:isolate;margin:12px 0;}
pre code{font-family:inherit;background:none;padding:0;}
.fkc-search{width:100%;padding:12px 14px;border:1px solid var(--line);
border-radius:8px;font-size:15px;margin:10px 0 4px;box-sizing:border-box;
font-family:inherit;}
.streak-badge{display:none;background:#EA580C;color:#fff;font-size:.72em;
font-weight:700;padding:3px 10px;border-radius:20px;margin-left:8px;
vertical-align:middle;}
.lesson-nav{display:flex;justify-content:space-between;gap:8px;
flex-wrap:wrap;margin-top:14px;}
.lesson-nav a{flex:1;min-width:120px;text-align:center;}
.section-title{font-family:'Inter',sans-serif;font-weight:800;
font-size:1.2em;margin:30px 0 2px;padding-top:18px;
border-top:1px solid var(--line);display:flex;align-items:center;gap:8px;}
.section-title.adults{color:var(--primary);}
.section-title.kids{color:#DB4C77;}
.quiz-box{margin-top:16px;border-top:1px dashed var(--line);padding-top:14px;}
.quiz-box textarea{width:100%;min-height:60px;border:1px solid var(--line);
border-radius:8px;padding:10px;font-family:inherit;font-size:14px;
box-sizing:border-box;margin:6px 0;}
.quiz-result{font-size:.88em;margin-top:6px;font-weight:600;}
.puzzle-box{margin-top:16px;border-top:1px dashed var(--line);padding-top:14px;}
.puzzle-box h3{margin-top:0;}
.puzzle-status{font-size:.85em;color:var(--muted);margin:0 0 10px;}
.puzzle-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;
max-width:340px;margin:0 auto;}
.puzzle-card{aspect-ratio:1/1;border-radius:10px;border:none;
background:var(--primary);color:#fff;font-size:1.6em;cursor:pointer;
display:flex;align-items:center;justify-content:center;
transition:transform .25s ease,background .25s ease;padding:0;}
.puzzle-card.flipped,.puzzle-card.matched{background:#fff;
border:1px solid var(--line);color:var(--ink);}
.puzzle-card.matched{background:#EAFBF0;border-color:var(--accent);
opacity:.85;cursor:default;}
.puzzle-card:disabled{cursor:default;}
.puzzle-win{display:none;text-align:center;margin-top:12px;
background:#EAFBF0;border-radius:10px;padding:12px;font-weight:700;color:#15803d;}
@media print{
  .top,.notify-btn,.lang-tabs,.btn,.brand-footer,.lesson-nav,footer,
  .quiz-box,.puzzle-box,.badge,#fkc-complete-btn,.no-print{display:none!important;}
  body{background:#fff;}
  .card{box-shadow:none;border:none;}
}
"""

HEAD = """<!DOCTYPE html>
<html lang="ur"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>{title}</title>
<meta property="og:title" content="{title}">
<meta property="og:description" content="{ogdesc}">
<meta property="og:image" content="{ogimage}">
<meta name="twitter:card" content="summary_large_image">
<script>
// Dark mode — theme paint se pehle set karte hain taake flash na ho.
(function(){{
  try{{
    var t = localStorage.getItem("fkc_theme") ||
      (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", t);
  }}catch(e){{}}
}})();
</script>
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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Nastaliq+Urdu:wght@400;600;700&display=swap" rel="stylesheet">
<style>{css}</style></head><body><div class="wrap">
<div class="brand-bar fade-in"><img src="{logo_href}" alt="{brand}">
<div><div class="bname">{brand}</div><div class="btag">Learn · Earn · Grow</div></div></div>
<button type="button" class="theme-toggle" id="fkcThemeToggle" title="Dark/Light mode" onclick="fkcToggleTheme()">🌓</button>
<script>
function fkcToggleTheme(){{
  var cur = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", cur);
  try{{ localStorage.setItem("fkc_theme", cur); }}catch(e){{}}
}}
</script>
"""


ADSENSE_CLIENT = "ca-pub-5639688573760714"
# "Fkc Trading Academy" ad unit (AdSense dashboard se liya gaya).
ADSENSE_SLOT = "2517808504"


def adsense_unit_html():
    """Page ke content ke neeche ek display ad unit dikhata hai."""
    return f"""
    <div class="no-print" style="margin:18px 0;text-align:center;">
      <ins class="adsbygoogle" style="display:block" data-ad-client="{ADSENSE_CLIENT}"
        data-ad-slot="{ADSENSE_SLOT}" data-ad-format="auto" data-full-width-responsive="true"></ins>
      <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
    </div>"""


def brand_footer_html(logo_href):
    privacy_href = logo_href.replace(BRAND_LOGO, "privacy.html")
    wa_link = f"https://wa.me/{BRAND_WHATSAPP_DIGITS}"
    return (
        f'<div class="brand-footer"><img src="{logo_href}" alt="{BRAND_NAME}">'
        f'<div class="txt"><b>{html.escape(BRAND_NAME)}</b><br>'
        f'{html.escape(BRAND_NAME_TITLE_LINE)}<br>'
        f'<a class="wa-btn" href="{wa_link}" target="_blank" rel="noopener">'
        f'💬 WhatsApp par Contact karein</a><br>'
        f'<a href="{privacy_href}">Privacy Policy</a></div></div>'
    )


FOOT_TAIL = f"</div><footer>{BRAND_NAME} — daily lessons, automatically updated</footer></body></html>"


# ---------------------------------------------------------------------
# 🔥 Daily streak — localStorage mein track hota hai (koi login/database
# nahi chahiye). Jab bhi student koi lesson page kholta hai, aaj ki date
# record hoti hai; agar kal bhi khola tha to streak +1, warna 1 se restart.
# Home page isi value ko parh kar badge mein dikhata hai.
# ---------------------------------------------------------------------
def streak_tracker_script_html():
    """Lesson page par lagta hai — har visit par streak update karta hai."""
    return """<script>
(function(){
  try{
    var today = new Date().toISOString().slice(0,10);
    var s = JSON.parse(localStorage.getItem("fkc_streak")||"null") || {last:null,count:0};
    if(s.last !== today){
      var y = new Date(Date.now()-86400000).toISOString().slice(0,10);
      s.count = (s.last === y) ? s.count + 1 : 1;
      s.last = today;
      localStorage.setItem("fkc_streak", JSON.stringify(s));
    }
  }catch(e){}
})();
</script>"""


def streak_badge_script_html():
    """Home page par lagta hai — agar streak > 1 din ho to badge dikhata hai."""
    return """<script>
(function(){
  try{
    var s = JSON.parse(localStorage.getItem("fkc_streak")||"null");
    var el = document.getElementById("fkc-streak-badge");
    if(s && s.count > 1 && el){
      el.textContent = "🔥 " + s.count + " din streak";
      el.style.display = "inline-block";
    }
  }catch(e){}
})();
</script>"""


def home_search_script_html():
    """Home page ke course cards ko search box se filter karta hai
    (sirf client-side JS, koi backend/tool nahi chahiye)."""
    return """<script>
(function(){
  var box = document.getElementById("fkc-course-search");
  if(!box) return;
  box.addEventListener("input", function(){
    var q = this.value.trim().toLowerCase();
    document.querySelectorAll(".ccard").forEach(function(card){
      card.style.display = card.textContent.toLowerCase().indexOf(q) !== -1 ? "" : "none";
    });
  });
})();
</script>"""


def pdf_download_button_html():
    """Browser ka apna free 'Print to PDF' use karta hai — koi extra
    library/service nahi chahiye. Print CSS (BASE_CSS mein @media print)
    buttons/nav chhupa deta hai taake sirf lesson content PDF mein aaye."""
    return (
        '<button type="button" class="btn alt no-print" onclick="window.print()">'
        '🖨️ PDF Download / Print</button>'
    )


def quiz_check_html(answer_key):
    """Existing 'Answer Key' keywords (already Mistral se milte hain, koi
    nayi AI call nahi) se ek self-check quiz box banata hai — student
    apna jawab likhta hai aur JS check karta hai kitne keywords match hue.
    Sab kuch client-side hai, kisi cost/limit ka khatra nahi."""
    if not answer_key:
        return ""
    keys_js = json.dumps(answer_key, ensure_ascii=False)
    return f"""
      <div class="quiz-box no-print">
        <p><b>📝 Apna Practice Check Karein</b></p>
        <p class="muted" style="font-size:.85em;">Upar ka "Practice" step apne alfaaz mein neeche likhein, phir check karein.</p>
        <textarea id="fkc-quiz-answer" placeholder="Apna jawab yahan likhein..."></textarea>
        <button type="button" class="btn" onclick="fkcCheckQuiz(this)" data-keys='{keys_js}'>✅ Check Karein</button>
        <div class="quiz-result" id="fkc-quiz-result"></div>
      </div>
      <script>
      function fkcCheckQuiz(btn){{
        var keys = JSON.parse(btn.getAttribute("data-keys"));
        var ans = (document.getElementById("fkc-quiz-answer").value || "").toLowerCase();
        var hit = 0;
        keys.forEach(function(k){{ if(k && ans.indexOf(k) !== -1) hit++; }});
        var el = document.getElementById("fkc-quiz-result");
        if(hit === 0){{
          el.textContent = "Koi keyword match nahi hua — dobara try karein ya lesson dobara parhein.";
          el.style.color = "#D97706";
        }} else {{
          el.textContent = "✅ " + hit + "/" + keys.length + " keywords match hue — shabaash!";
          el.style.color = "var(--accent)";
        }}
      }}
      </script>"""


# ---------------------------------------------------------------------
# 🧩 Puzzle game — chhota "yaadasht" (memory match) game, bilkul free,
# koi AI/network call nahi, sirf emojis ke jode milane hain. Har lesson
# page par aur games hub par dikhta hai — students (bade ho ya bachay)
# thodi der khelte hain, isi dauran page par pehle se laga hua AdSense
# unit dikhta rehta hai (impression), aur jeetne par "Aur Seekhein"
# CTA reveal hota hai. Koi "click karo reward ke liye" wala button nahi
# — AdSense policy ke against hota, isliye sirf natural CTA hai.
# ---------------------------------------------------------------------
PUZZLE_EMOJI_SETS = [
    ["🎯", "📚", "⭐", "🚀", "💡", "🏆"],
    ["🍎", "🐶", "🌙", "🎨", "🔑", "🌸"],
    ["🎈", "🧩", "🎵", "🐢", "🌈", "⚽"],
    ["🍉", "🐱", "☀️", "🖊️", "🎁", "🐝"],
    ["🚗", "🌟", "📖", "🐦", "🍩", "🔔"],
    ["🐘", "🎪", "🍓", "🧠", "🌻", "🎲"],
]


def puzzle_game_html(uid, seed=0):
    """Self-contained memory-match (jode milao) game — koi external
    library nahi, sirf vanilla JS. `uid` unique honi chahiye taake ek
    hi page par 2+ instances ho to takra na jayein (games hub page)."""
    emojis = PUZZLE_EMOJI_SETS[seed % len(PUZZLE_EMOJI_SETS)]
    emojis_js = json.dumps(emojis, ensure_ascii=False)
    return f"""
      <div class="puzzle-box no-print" id="{uid}">
        <h3>🧩 Dimaghi Kasrat — Jode Milayein</h3>
        <p class="puzzle-status" id="{uid}-status">Cards par tap karke jode (pairs) milayein.</p>
        <div class="puzzle-grid" id="{uid}-grid"></div>
        <div class="puzzle-win" id="{uid}-win">🎉 Shabaash! Sab jode mil gaye — thodi der aur seekhne ke liye tayyar?</div>
      </div>
      <script>
      (function(){{
        var emojis = {emojis_js};
        var deck = emojis.concat(emojis);
        for (var i = deck.length - 1; i > 0; i--) {{
          var j = Math.floor(Math.random() * (i + 1));
          var t = deck[i]; deck[i] = deck[j]; deck[j] = t;
        }}
        var grid = document.getElementById("{uid}-grid");
        var statusEl = document.getElementById("{uid}-status");
        var winEl = document.getElementById("{uid}-win");
        var flipped = [], matchedCount = 0, moves = 0, lock = false;
        deck.forEach(function(val){{
          var b = document.createElement("button");
          b.type = "button";
          b.className = "puzzle-card";
          b.setAttribute("data-val", val);
          b.textContent = "❓";
          b.onclick = function(){{
            if (lock || b.classList.contains("matched") || b.classList.contains("flipped")) return;
            b.classList.add("flipped");
            b.textContent = val;
            flipped.push(b);
            if (flipped.length === 2) {{
              moves++;
              lock = true;
              var a = flipped[0], c = flipped[1];
              if (a.getAttribute("data-val") === c.getAttribute("data-val")) {{
                a.classList.add("matched"); c.classList.add("matched");
                matchedCount += 2;
                flipped = []; lock = false;
                statusEl.textContent = "Moves: " + moves + " · " + matchedCount + "/" + deck.length + " match hue";
                if (matchedCount === deck.length) {{
                  winEl.style.display = "block";
                  statusEl.textContent = "Complete! Total moves: " + moves;
                }}
              }} else {{
                setTimeout(function(){{
                  a.classList.remove("flipped"); a.textContent = "❓";
                  c.classList.remove("flipped"); c.textContent = "❓";
                  flipped = []; lock = false;
                }}, 700);
              }}
            }}
          }};
          grid.appendChild(b);
        }});
      }})();
      </script>"""


def log_error(message):
    """Errors ko error_log.txt mein bhi append karta hai (console print ke
    ilawa) — taake GitHub Actions run history khatam hone ke baad bhi
    dekh sakein kaunse courses/lessons fail hue."""
    try:
        with open("error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.utcnow().isoformat()}] {message}\n")
    except Exception:
        pass


def build_sitemap_xml(posts):
    """Google Search Console ke liye sitemap.xml — SITE_URL env var set
    hona zaroori hai (warna absolute URLs nahi ban sakte), agar khaali ho
    to None return karta hai aur sitemap simply nahi likhi jati."""
    if not SITE_URL:
        return None
    urls = [f"{SITE_URL}/", f"{SITE_URL}/games.html"]
    for slug, course in COURSES.items():
        urls.append(f"{SITE_URL}/courses/{slug}/index.html")
        for lesson in posts.get(slug, []):
            urls.append(f"{SITE_URL}/courses/{slug}/posts/{lesson['date']}-{lesson['id']}.html")
    body = "".join(f"<url><loc>{html.escape(u)}</loc></url>" for u in urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>'
    )


def build_robots_txt():
    """robots.txt — sab search engines ko crawl karne dete hain, aur agar
    SITE_URL set ho to sitemap.xml ka link bhi shaamil karte hain."""
    lines = ["User-agent: *", "Allow: /"]
    if SITE_URL:
        lines.append(f"Sitemap: {SITE_URL}/sitemap.xml")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------
# 🔔 IndexNow — naye/updated lessons ka fast indexing ping (free).
# NOTE: Google Indexing API ise support nahi karta (sirf Bing/Yandex/
# Seznam/Naver), aur Google ka purana sitemap-ping endpoint 2023 mein
# hamesha ke liye band ho chuka hai (ab 404 deta hai). Google ke liye
# already sitemap.xml maujood hai — Google usay khud periodically crawl
# karta hai, yehi is waqt sabse reliable free tareeqa hai.
# INDEXNOW_KEY env var mein ek random hex string set karein (khud bana
# kar, e.g. `openssl rand -hex 16`) — key set na ho to yeh step khud
# skip ho jata hai.
# ---------------------------------------------------------------------
INDEXNOW_KEY = os.environ.get("INDEXNOW_KEY", "")


def write_indexnow_key_file():
    """docs/<key>.txt banata hai jisme sirf key likhi hoti hai — IndexNow
    isay ownership-verification ke liye fetch karta hai."""
    if not INDEXNOW_KEY:
        return
    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


def ping_indexnow(urls):
    """IndexNow API ko naye/updated URLs batata hai (Bing/Yandex fast-index
    kar sakein). Fail ho jaye to chup chaap skip — site build kabhi iski
    wajah se nahi rukni chahiye."""
    if not (INDEXNOW_KEY and SITE_URL and urls):
        return
    host = SITE_URL.split("//", 1)[-1].split("/", 1)[0]
    payload = {
        "host": host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": urls[:10000],
    }
    try:
        resp = requests.post(
            "https://api.indexnow.org/indexnow",
            json=payload, timeout=20,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        print(f"IndexNow: {len(urls)} URL(s) submit hui, status {resp.status_code}.")
    except Exception as e:
        print(f"IndexNow ping fail: {e}", file=sys.stderr)


# AdSense ka anti-fraud verification string — publisher ID ke aakhir mein
# jo "pub-..." number hota hai wahi ADSENSE_CLIENT mein bhi hai
# ("ca-pub-..." mein se "ca-" hata kar). Yeh sirf ek dafa set karni hoti
# hai, badalti nahi rehti.
ADS_TXT_LINE = "google.com, pub-5639688573760714, DIRECT, f08c47fec0942fa0"


def build_ads_txt():
    """ads.txt — Google AdSense ke liye zaroori hai (isay verify karta hai
    ke ads sirf authorized sellers se aa rahi hain). Agar yeh file
    missing ho to AdSense earnings kam ya bilkul band bhi ho sakti hain,
    is liye docs/ads.txt mein root par hona zaroori hai."""
    return ADS_TXT_LINE + "\n"


def build_rss_feed(posts):
    """feed.xml — RSS reader se site follow karne ke liye. SITE_URL zaroori
    hai (links absolute hone chahiye), warna None return karta hai."""
    if not SITE_URL:
        return None
    all_lessons = []
    for slug, course in COURSES.items():
        for lesson in posts.get(slug, []):
            all_lessons.append((slug, course, lesson))
    all_lessons.sort(key=lambda t: t[2].get("date", ""), reverse=True)
    items = []
    for slug, course, lesson in all_lessons[:60]:
        link = f"{SITE_URL}/courses/{slug}/posts/{lesson['date']}-{lesson['id']}.html"
        desc = html.escape((lesson.get("preamble", "") or "")[:300])
        items.append(
            f"<item><title>{html.escape(lesson['title'])}</title>"
            f"<link>{html.escape(link)}</link><guid>{html.escape(link)}</guid>"
            f"<description>{desc}</description></item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
        f"<title>{html.escape(BRAND_NAME)}</title><link>{html.escape(SITE_URL)}</link>"
        "<description>Daily lessons — Learn, Earn, Grow.</description>"
        + "".join(items) + "</channel></rss>"
    )


def md_lite(text):
    if not text:
        return ""
    out = []
    # pehle fenced code blocks (```lang ... ```) alag nikalte hain, taake
    # unhein <pre dir="ltr"> mein rakha ja sake — warna RTL (Urdu/Sindhi)
    # container ke andar English/code punctuation ulta (reversed) dikhta
    # hai (jaise "#include <iostream>" ban jata hai "<include <iostream#")
    parts = re.split(r"```(\w*)\n?(.*?)```", text, flags=re.DOTALL)
    for i, part in enumerate(parts):
        if i % 3 == 0:
            if part.strip():
                out.append("".join(
                    f"<p>{html.escape(p).replace(chr(10), '<br>')}</p>"
                    for p in part.strip().split("\n\n") if p.strip()
                ))
        elif i % 3 == 2:
            code = part.strip("\n")
            out.append(f'<pre dir="ltr"><code>{html.escape(code)}</code></pre>')
        # i % 3 == 1 -> yeh sirf language name hai (jaise "cpp"), skip
    return "".join(out)


def render_home(posts):
    adult_cards = []
    kids_cards = []
    for i, (slug, course) in enumerate(COURSES.items()):
        lessons = posts.get(slug, [])
        count = len(lessons)
        latest = lessons[-1]["title"] if lessons else "Pehla lesson jald aa raha hai"
        accent = ACCENTS[i % len(ACCENTS)]
        card = f"""
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
    </a>"""
        if course.get("for_kids"):
            kids_cards.append(card)
        else:
            adult_cards.append(card)

    logo_href = BRAND_LOGO
    body = f"""
    <div class="top"><span>{html.escape(BRAND_NAME)}</span>
    <span class="lbl">Digital Hub — apni pasand ka course chunein</span></div>
    <span class="eyebrow fade-in">Course Library</span>
    <h1 class="fade-in">🎓 Roz ek naya practical lesson<span class="streak-badge" id="fkc-streak-badge"></span></h1>
    <p class="muted fade-in d2">📅 Har course ka naya lesson roz raat 12:00 AM se subah 5:30 AM Pakistan time ke darmiyan yahan post hota hai — har course card par uska waqt likha hai.
    Jis course mein interest ho us par tap karein — daily lesson step-by-step parhein aur practice karein.</p>
    <div id="fkc-continue-card" style="display:none;"></div>
    <input type="text" id="fkc-course-search" class="fkc-search" placeholder="🔍 Course dhoondein...">
    <p class="fade-in d2"><a class="btn alt" href="games.html">🎮 Games Zone — Khel Khel Mein Seekhein</a></p>
    <p class="fade-in d2">{direct_link_button_html("🚀 Start Learning")}</p>

    <h2 class="section-title adults fade-in">💼 Bado Ke Liye Courses</h2>
    <p class="muted fade-in" style="margin-top:-6px;">Skills, business, aur earning ke daily courses.</p>
    <div class="grid">{''.join(adult_cards)}</div>

    <h2 class="section-title kids fade-in">🧸 Bachon Ke Liye Courses</h2>
    <p class="muted fade-in" style="margin-top:-6px;">Nursery, KG, Play Group, achi adaatein, aur educational games — sab free.</p>
    <div class="grid">{''.join(kids_cards)}</div>

    {adsense_unit_html()}
    {brand_footer_html(logo_href)}
    <p style="text-align:center;margin-top:8px;">
      <a href="admin-certificates.html" style="color:var(--muted);font-size:11px;text-decoration:none;">⚙️ Admin</a>
    </p>
    <script>
    (function(){{
      try {{
        var raw = localStorage.getItem('fkc_last_lesson');
        if (!raw) return;
        var d = JSON.parse(raw);
        var box = document.getElementById('fkc-continue-card');
        if (!box || !d.href || !d.title) return;
        box.style.display = 'block';
        box.style.margin = '0 0 16px';
        box.innerHTML = '<a href="' + d.href + '" style="display:block;background:linear-gradient(135deg,#eef4ff,#f7f0ff);' +
          'border-radius:14px;padding:14px 16px;text-decoration:none;color:inherit;">' +
          '<div style="font-size:12px;color:var(--muted);margin-bottom:4px;">▶️ Jahan chhoda tha wahan se jaari rakhein</div>' +
          '<div style="font-weight:600;">' + (d.courseIcon || '') + ' ' + d.courseName + ' — Day ' + d.day + '</div>' +
          '<div style="font-size:13px;color:var(--muted);margin-top:2px;">' + d.title + '</div></a>';
      }} catch (e) {{}}
    }})();
    </script>
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
    return head + body + FOOT_TAIL + notify_script_html() + pwa_install_prompt_html() + home_search_script_html() + streak_badge_script_html()


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

    total_lessons = len(lessons)
    course_name_js = json.dumps(course["name"], ensure_ascii=False)
    fee_js = json.dumps(course_certificate_fee(course), ensure_ascii=False)
    progress_block = ""
    if total_lessons > 0:
        sync_block = ""
        if FIREBASE_ENABLED:
            sync_block = """
      <div class="no-print" style="margin-top:10px;border-top:1px solid var(--line);padding-top:10px;">
        <p class="muted" style="margin:0 0 6px;font-size:13px;">🔄 Progress doosri device par le jayein</p>
        <button type="button" class="btn alt" onclick="fkcShowSyncCode()">📤 Code Banayein</button>
        <button type="button" class="btn alt" onclick="fkcEnterSyncCode()">📥 Code Se Wapas Layein</button>
      </div>"""
        progress_block = f"""
    <div class="card progress-wrap" id="fkc-progress-wrap" data-slug="{slug}" data-total="{total_lessons}">
      <div class="progress-track"><div class="progress-fill" id="fkc-progress-fill"></div></div>
      <p class="muted" id="fkc-progress-text">0/{total_lessons} lessons complete</p>
      <button type="button" class="btn" id="fkc-cert-btn" style="display:none"
        onclick="fkcApplyCertificate('{slug}', {course_name_js}, {fee_js})">
        🎓 Certificate ke liye Apply Karein
      </button>
      {sync_block}
    </div>"""

    logo_href = f"../../{BRAND_LOGO}"
    _provider = {"@type": "Organization", "name": BRAND_NAME}
    if SITE_URL:
        _provider["sameAs"] = SITE_URL
    course_schema = json.dumps({k: v for k, v in {
        "@context": "https://schema.org",
        "@type": "Course",
        "name": course["name"],
        "description": course["tagline"],
        "provider": _provider,
        "numberOfCredits": len(lessons),
        "inLanguage": "ur",
        "url": (f"{SITE_URL}/courses/{slug}/index.html" if SITE_URL else None),
    }.items() if v is not None}, ensure_ascii=False)
    course_schema_block = f'<script type="application/ld+json">{course_schema}</script>'

    body = f"""
    {course_schema_block}
    <div class="top"><a href="../../index.html">← {html.escape(BRAND_NAME)}</a></div>
    <h1>{course['icon']} {html.escape(course['name'])}</h1>
    <p class="muted">{html.escape(course['tagline'])}</p>
    <p class="muted">📅 Naya lesson roz <b>{html.escape(course.get('post_time', ''))} Pakistan time</b> par yahan add hota hai.</p>
    <p>{notify_bell_html(slug)}</p>
    {affiliate_block}
    {progress_block}
    <div class="plist">{listing}</div>
    {adsense_unit_html()}
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
    return (
        head + body + FOOT_TAIL + notify_script_html()
        + certificate_progress_script_html() + firebase_init_html()
        + pwa_install_prompt_html()
    )


def render_games_page():
    """Ek dedicated 'Games Zone' page (docs/games.html, root-level jaisa
    index.html) — 3 puzzle levels ek sath, taake koi bhi (bacha ho ya
    bada) sirf khelne ke liye bhi aaye. Har lesson page par bhi wahi
    game hai, lekin yeh ek standalone hub hai jo home page se link hota
    hai — repeat visits aur ad impressions dono badhta hai."""
    levels = "".join(
        f'<div class="card">{puzzle_game_html(f"pz-hub-{i}", seed=i)}</div>'
        for i in range(3)
    )
    logo_href = BRAND_LOGO
    body = f"""
    <div class="top"><a href="index.html">← {html.escape(BRAND_NAME)}</a></div>
    <span class="eyebrow fade-in">Games Zone</span>
    <h1 class="fade-in">🎮 Khel Khel Mein Seekhein</h1>
    <p class="muted fade-in d2">Yaadasht (memory) games — bacchay ho ya bade, sab ke liye. Har level mein naye emoji jode hain, dimagh tez karein!</p>
    {levels}
    {adsense_unit_html()}
    <p class="fade-in">{direct_link_button_html("🚀 Ab Ek Course Shuru Karein")}</p>
    {brand_footer_html(logo_href)}
    """
    og_image = f"{SITE_URL}/{BRAND_LOGO}" if SITE_URL else BRAND_LOGO
    head = HEAD.format(
        title=f"Games Zone — {BRAND_NAME}",
        ogdesc="Khel khel mein seekhein — free memory/puzzle games, bacchon aur bado dono ke liye.",
        ogimage=og_image,
        logo_href=logo_href,
        brand=html.escape(BRAND_NAME),
        css=BASE_CSS,
        pwa_extra=pwa_extra_for(logo_href),
    )
    return head + body + FOOT_TAIL + pwa_install_prompt_html()


def render_translation_html(data):
    out = md_lite(data.get("preamble", ""))
    for sec in data.get("sections", []):
        label = sec.get("label", "")
        content = sec.get("content", "")
        out += f"<h3>{html.escape(label)}</h3>{md_lite(content)}"
    return out


LANG_TAB_LABELS = {"rm": "Roman Urdu", "ur": "اردو", "sd": "سنڌي"}


def lang_tabs_script_html():
    return """<script>
(function(){
  window.fkcSwitchLang = function(btn){
    var lang = btn.getAttribute("data-lang");
    var tabs = document.querySelectorAll(".lang-tab");
    var blocks = document.querySelectorAll(".lang-content");
    for(var i=0;i<tabs.length;i++){
      tabs[i].classList.toggle("active", tabs[i].getAttribute("data-lang")===lang);
    }
    for(var j=0;j<blocks.length;j++){
      blocks[j].style.display = (blocks[j].getAttribute("data-lang")===lang) ? "" : "none";
    }
  };
})();
</script>"""


def render_lesson_page(slug, course, lesson, is_latest, image_href=None, video_href=None,
                        prev_href=None, prev_title=None, next_href=None, next_title=None):
    lesson_html = md_lite(lesson["preamble"])
    for label, content in lesson["sections"]:
        lesson_html += f"<h3>{html.escape(label)}</h3>{md_lite(content)}"

    translations = lesson.get("translations") or {}
    lang_blocks = [("rm", lesson_html, False)]
    for code in ("ur", "sd"):
        if code in translations:
            lang_blocks.append((code, render_translation_html(translations[code]), True))

    if len(lang_blocks) > 1:
        tab_buttons = "".join(
            f'<button type="button" class="lang-tab{" active" if code=="rm" else ""}" '
            f'data-lang="{code}" onclick="fkcSwitchLang(this)">{LANG_TAB_LABELS[code]}</button>'
            for code, _, _ in lang_blocks
        )
        tabs_html = f'<div class="lang-tabs">{tab_buttons}</div>'
    else:
        tabs_html = ""

    content_html = "".join(
        f'<div class="lang-content" data-lang="{code}"'
        + (' dir="rtl"' if rtl else "")
        + (' style="display:none"' if code != "rm" else "")
        + f'>{block}</div>'
        for code, block, rtl in lang_blocks
    )

    image_block = ""
    if image_href:
        image_block = (
            f'<img src="{image_href}" alt="{html.escape(lesson["title"])}" '
            'style="width:100%;border-radius:12px;margin-bottom:14px;">'
        )

    video_block = ""
    if video_href:
        poster_attr = f' poster="{image_href}"' if image_href else ""
        video_block = (
            '<p class="muted" style="margin:0 0 6px;">🎬 AI Video Explanation</p>'
            f'<video src="{video_href}" controls preload="metadata"{poster_attr} '
            'style="width:100%;border-radius:12px;margin-bottom:14px;background:#000;"></video>'
        )

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

    badge = '<span class="badge">Latest</span>' if is_latest else ""
    logo_href = f"../../../{BRAND_LOGO}"
    affiliate_btn = course_affiliate_button_html(course)
    affiliate_block = f'<p>{affiliate_btn}</p>' if affiliate_btn else ""
    quiz_block = quiz_check_html(lesson.get("answer_key", ""))
    puzzle_block = puzzle_game_html(f"pz-{slug}-{lesson['day']}", seed=lesson["day"])

    # "Kal ka recap" — chhoti si continuity line, taake student ko yaad
    # rahe pichla lesson kya tha. Sirf 1 line, koi extra AI call nahi
    # (bilkul free) — bas prev_title jo pehle se maujood hai use karte hain.
    recap_block = ""
    if prev_title:
        recap_block = (
            f'<p class="muted" style="margin:0 0 10px;">↩️ Pichla lesson: '
            f'<strong>{html.escape(prev_title)}</strong> — aaj is se aage badhte hain.</p>'
        )

    # Bachon (kids-safety course) ke liye ek chhota parent-note — is course
    # mein content jaan-boojh kar simple/audio-heavy hai, parents ko yaad
    # dilate hain ke bache ke sath baith kar sunein.
    kids_parent_note = ""
    if course.get("for_kids"):
        kids_parent_note = (
            '<p class="muted" style="background:#fff7e6;padding:10px 12px;'
            'border-radius:10px;margin:0 0 12px;">👨‍👩‍👧 Walidain ke liye: '
            'bachay ke sath baith kar ye lesson sunein/dekhein, aur upar wala '
            '🎬 audio zaroor lagayein — chhotay bachay padhne se zyada sun kar '
            'behtar samajhte hain.</p>'
        )

    # Personal notes — student apni note likh sake, har device/browser mein
    # localStorage se save hoti hai (bilkul free, koi server/database nahi
    # chahiye). Print mein shaamil nahi (no-print) taake PDF saaf rahe.
    notes_block = f"""
      <div class="no-print" style="margin-top:14px;">
        <label for="fkc-notes" class="muted" style="display:block;margin-bottom:4px;">📝 Apni Note (sirf aapke is browser mein save hoti hai):</label>
        <textarea id="fkc-notes" data-slug="{slug}" data-lesson="{lesson['id']}"
          placeholder="Yahan apni note likhein..." rows="3"
          style="width:100%;border-radius:10px;border:1px solid #ddd;padding:8px;font-family:inherit;"
          oninput="fkcSaveNote(this)"></textarea>
      </div>
    """

    nav_block = ""
    if prev_href or next_href:
        prev_link = f'<a class="btn alt" href="{prev_href}">← {html.escape(prev_title)}</a>' if prev_href else "<span></span>"
        next_link = f'<a class="btn alt" href="{next_href}">{html.escape(next_title)} →</a>' if next_href else "<span></span>"
        nav_block = f'<div class="lesson-nav">{prev_link}{next_link}</div>'

    lesson_url = f"{SITE_URL}/courses/{slug}/posts/{lesson['date']}-{lesson['id']}.html" if SITE_URL else ""

    def _no_nulls(d):
        return {k: v for k, v in d.items() if v is not None}

    schema_dict = _no_nulls({
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "headline": lesson["title"],
        "name": lesson["title"],
        "description": (lesson.get("preamble") or "")[:200],
        "url": lesson_url or None,
        "image": (f"{SITE_URL}/{image_href.replace('../../../','')}" if (SITE_URL and image_href) else None),
        "learningResourceType": "Lesson",
        "educationalLevel": "Beginner",
        "inLanguage": "ur",
        "isPartOf": _no_nulls({
            "@type": "Course",
            "name": course["name"],
            "url": (f"{SITE_URL}/courses/{slug}/index.html" if SITE_URL else None),
        }),
        "datePublished": lesson.get("date"),
        "publisher": {"@type": "Organization", "name": BRAND_NAME},
    })
    schema_ld = json.dumps(schema_dict, ensure_ascii=False)
    schema_block = f'<script type="application/ld+json">{schema_ld}</script>'

    body = f"""
    {schema_block}
    <div class="top"><a href="../../../index.html">← {html.escape(BRAND_NAME)}</a>
    <a href="../index.html" class="course-back-link">/ {html.escape(course['name'])}</a></div>
    {badge}
    <p class="muted">{course['icon']} {html.escape(course['name'])} · Day {lesson['day']:02d}</p>
    <h1>{html.escape(lesson['title'])}</h1>
    {recap_block}
    <div class="card">
      {kids_parent_note}
      {image_block}
      {video_block}
      {tabs_html}
      {content_html}
      {affiliate_block}
      {quiz_block}
      {puzzle_block}
      {notes_block}
      <div class="no-print">
        <a class="btn" href="{wa_link}" target="_blank" rel="noopener">📲 WhatsApp par Share karein</a>
        <a class="btn alt" href="{fb_link}" target="_blank" rel="noopener">📘 Facebook par Share karein</a>
        {pdf_download_button_html()}
      </div>
      <div class="no-print">
        <button type="button" class="btn complete-btn" id="fkc-complete-btn"
          data-slug="{slug}" data-lesson="{lesson['id']}"
          onclick="fkcToggleComplete(this)">✅ Complete Mark Karein</button>
      </div>
    </div>
    {nav_block}
    <p class="no-print">{direct_link_button_html("🚀 Watch Next Lesson")}</p>
    {giscus_comments_html()}
    {adsense_unit_html()}
    {brand_footer_html(logo_href)}
    <script>
    (function(){{
      try {{
        localStorage.setItem('fkc_last_lesson', JSON.stringify({{
          slug: {json.dumps(slug)},
          courseName: {json.dumps(course['name'])},
          courseIcon: {json.dumps(course.get('icon',''))},
          title: {json.dumps(lesson['title'])},
          href: 'courses/{slug}/posts/{lesson['date']}-{lesson['id']}.html',
          day: {lesson['day']}
        }}));
      }} catch (e) {{}}
      var ta = document.getElementById('fkc-notes');
      if (ta) {{
        try {{
          var saved = localStorage.getItem('fkc_note_' + ta.dataset.slug + '_' + ta.dataset.lesson);
          if (saved) ta.value = saved;
        }} catch (e) {{}}
      }}
    }})();
    function fkcSaveNote(el) {{
      try {{
        localStorage.setItem('fkc_note_' + el.dataset.slug + '_' + el.dataset.lesson, el.value);
      }} catch (e) {{}}
    }}
    </script>
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
    return (
        head + body + FOOT_TAIL + certificate_progress_script_html()
        + lang_tabs_script_html() + firebase_init_html() + pwa_install_prompt_html()
        + streak_tracker_script_html()
    )


def render_admin_certificates_page():
    """docs/admin-certificates.html — sirf aap (Fazul Khan) ke liye. Firebase
    email/password se login karke certificate-requests ki list dikhata
    hai; har request ke liye ek click mein PNG certificate generate hota
    hai jis par student ka naam, course ka naam, date, aur automatic
    signature stamp (docs/signature.png agar upload ki ho, warna ek
    script-font wala fallback signature) laga hota hai. Ye page tabhi
    kaam karega jab FIREBASE_CONFIG (upar Python file mein) fill ho."""
    logo_href = BRAND_LOGO
    if not FIREBASE_ENABLED:
        body = f"""
    <div class="top"><a href="index.html">← {html.escape(BRAND_NAME)}</a></div>
    <h1>🎓 Certificate Admin Panel</h1>
    <div class="card">
      <p>Ye panel Firebase ke bina kaam nahi karega. <code>generate_post.py</code>
      mein <code>FIREBASE_CONFIG</code> fill karein aur site dobara build karein.
      Steps neeche chat mein diye gaye hain.</p>
    </div>
    {brand_footer_html(logo_href)}
    """
        head = HEAD.format(
            title=f"Admin — {BRAND_NAME}", ogdesc="Certificate admin panel",
            ogimage=f"{SITE_URL}/{BRAND_LOGO}" if SITE_URL else logo_href,
            logo_href=logo_href, brand=html.escape(BRAND_NAME), css=BASE_CSS,
            pwa_extra="",
        )
        return head + body + FOOT_TAIL

    fb_cfg_json = json.dumps(FIREBASE_CONFIG)
    extra_css = """
    #admin-login{max-width:340px;margin:40px auto;}
    #admin-login input{width:100%;padding:10px;margin:6px 0;
      border:1px solid var(--line);border-radius:6px;font-size:14px;}
    table.req{width:100%;border-collapse:collapse;font-size:.88em;margin-top:10px;}
    table.req th,table.req td{border-bottom:1px solid var(--line);
      padding:8px 6px;text-align:left;vertical-align:middle;}
    .status-pill{padding:2px 9px;border-radius:20px;font-size:.75em;font-weight:700;}
    .status-pending{background:#FFF4E5;color:#B45309;}
    .status-issued{background:#E7F8EE;color:#0F7A3D;}
    #cert-modal{position:fixed;inset:0;background:rgba(0,0,0,.55);
      display:none;align-items:center;justify-content:center;z-index:999;padding:16px;}
    #cert-modal.show{display:flex;}
    #cert-modal .box{background:#fff;border-radius:12px;padding:16px;
      max-width:100%;max-height:90vh;overflow:auto;text-align:center;}
    #cert-canvas{max-width:100%;height:auto;border:1px solid var(--line);}
    """
    body = f"""
    <div class="top"><a href="index.html">← {html.escape(BRAND_NAME)}</a></div>
    <h1>🎓 Certificate Admin Panel</h1>
    <p class="muted">Sirf {html.escape(BRAND_CONTACT_NAME)} ke liye — certificate requests dekhein aur issue karein.</p>

    <div id="admin-login" class="card">
      <h3>Login</h3>
      <input type="email" id="admin-email" placeholder="Email">
      <input type="password" id="admin-pass" placeholder="Password">
      <button type="button" class="btn" onclick="fkcAdminLogin()">Login</button>
      <p class="muted" id="admin-login-err"></p>
    </div>

    <div id="admin-panel" style="display:none">
      <p><button type="button" class="btn alt" onclick="fkcAdminLogout()">Logout</button></p>
      <div class="card">
        <h3>Certificate Requests</h3>
        <table class="req" id="req-table"><thead>
          <tr><th>Date</th><th>Student</th><th>Course</th><th>Fee</th><th>Status</th><th></th></tr>
        </thead><tbody id="req-tbody"></tbody></table>
        <p class="muted" id="req-empty">Loading...</p>
      </div>
    </div>

    <div id="cert-modal">
      <div class="box">
        <canvas id="cert-canvas" width="1600" height="1131"></canvas><br>
        <button type="button" class="btn" onclick="fkcDownloadCert()">⬇️ Download Certificate (PNG)</button>
        <button type="button" class="btn alt" onclick="document.getElementById('cert-modal').classList.remove('show')">Band Karein</button>
      </div>
    </div>
    {brand_footer_html(logo_href)}

<script>
firebase.initializeApp({fb_cfg_json});
var auth = firebase.auth();
var db = firebase.firestore();
var currentReq = null;

function fkcAdminLogin(){{
  var email = document.getElementById("admin-email").value;
  var pass = document.getElementById("admin-pass").value;
  auth.signInWithEmailAndPassword(email, pass).catch(function(err){{
    document.getElementById("admin-login-err").textContent = err.message;
  }});
}}
function fkcAdminLogout(){{ auth.signOut(); }}

auth.onAuthStateChanged(function(user){{
  document.getElementById("admin-login").style.display = user ? "none" : "block";
  document.getElementById("admin-panel").style.display = user ? "block" : "none";
  if(user) loadRequests();
}});

function loadRequests(){{
  db.collection("certificate_requests").orderBy("created", "desc").limit(200)
    .onSnapshot(function(snap){{
      var tbody = document.getElementById("req-tbody");
      tbody.innerHTML = "";
      document.getElementById("req-empty").style.display = snap.empty ? "block" : "none";
      document.getElementById("req-empty").textContent = "Abhi koi certificate request nahi aayi.";
      snap.forEach(function(doc){{
        var d = doc.data();
        var dt = d.created && d.created.toDate ? d.created.toDate().toLocaleDateString() : "-";
        var statusClass = d.status === "issued" ? "status-issued" : "status-pending";
        var tr = document.createElement("tr");
        tr.innerHTML =
          "<td>" + dt + "</td>" +
          "<td>" + (d.name||"") + "</td>" +
          "<td>" + (d.course||"") + "</td>" +
          "<td>" + (d.fee||"") + "</td>" +
          "<td><span class='status-pill " + statusClass + "'>" + (d.status||"pending") + "</span></td>" +
          "<td><button type='button' class='btn' style='margin:0;padding:6px 12px;font-size:.8em;'>Generate</button></td>";
        tr.querySelector("button").addEventListener("click", function(){{
          currentReq = {{ id: doc.id, name: d.name, course: d.course, date: dt }};
          openCertModal(currentReq);
        }});
        tbody.appendChild(tr);
      }});
    }}, function(err){{
      var empty = document.getElementById("req-empty");
      empty.style.display = "block";
      empty.style.color = "#B45309";
      empty.textContent = "⚠️ Data load nahi ho saka: " + err.message +
        " — Firestore Database bana hai ya nahi, aur security rules check karein.";
    }});
}}

function drawCircularText(ctx, text, cx, cy, radius, startAngle, arcSpan, color, fontPx, fontFamily){{
  ctx.save();
  ctx.fillStyle = color;
  ctx.font = "bold " + fontPx + "px " + fontFamily;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.translate(cx, cy);
  ctx.rotate(startAngle);
  var step = text.length > 1 ? arcSpan / (text.length - 1) : 0;
  ctx.rotate(-arcSpan/2);
  for(var i=0;i<text.length;i++){{
    ctx.save();
    ctx.rotate(step * i);
    ctx.translate(0, -radius);
    ctx.fillText(text[i], 0, 0);
    ctx.restore();
  }}
  ctx.restore();
}}

function drawSeal(ctx, cx, cy){{
  var gold = "#B8860B", goldLight = "#D4AF37";
  ctx.save();
  ctx.strokeStyle = goldLight; ctx.lineWidth = 5;
  ctx.beginPath(); ctx.arc(cx, cy, 95, 0, Math.PI*2); ctx.stroke();
  ctx.strokeStyle = gold; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(cx, cy, 80, 0, Math.PI*2); ctx.stroke();
  ctx.fillStyle = "rgba(212,175,55,.08)";
  ctx.beginPath(); ctx.arc(cx, cy, 78, 0, Math.PI*2); ctx.fill();

  drawCircularText(ctx, {json.dumps(BRAND_NAME.upper())}, cx, cy, 68, -Math.PI/2, Math.PI*1.15, gold, 13, "Arial");
  drawCircularText(ctx, "★ VERIFIED ★ CERTIFIED", cx, cy, 68, Math.PI/2 + 0.35, Math.PI*0.85, gold, 12, "Arial");

  ctx.fillStyle = goldLight;
  ctx.font = "40px Arial";
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText("🎓", cx, cy - 2);

  // neeche ribbon tails
  ctx.fillStyle = gold;
  ctx.beginPath();
  ctx.moveTo(cx-30, cy+72); ctx.lineTo(cx-45, cy+140); ctx.lineTo(cx-14, cy+118); ctx.closePath(); ctx.fill();
  ctx.beginPath();
  ctx.moveTo(cx+30, cy+72); ctx.lineTo(cx+45, cy+140); ctx.lineTo(cx+14, cy+118); ctx.closePath(); ctx.fill();
  ctx.restore();
}}

function drawCorner(ctx, x, y, sx, sy){{
  ctx.save();
  ctx.translate(x, y); ctx.scale(sx, sy);
  ctx.strokeStyle = "#B8860B"; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(0,60); ctx.lineTo(0,0); ctx.lineTo(60,0); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(0,40); ctx.lineTo(40,0); ctx.stroke();
  ctx.beginPath(); ctx.arc(14,14,5,0,Math.PI*2); ctx.fill();
  ctx.restore();
}}

function openCertModal(req){{
  var canvas = document.getElementById("cert-canvas");
  var ctx = canvas.getContext("2d");
  var w = canvas.width, h = canvas.height;

  Promise.all([
    document.fonts.load("italic 90px 'Great Vibes'"),
    document.fonts.load("900 46px 'Playfair Display'"),
    document.fonts.load("700 30px 'Playfair Display'"),
    document.fonts.load("400 22px 'Playfair Display'")
  ]).catch(function(){{}}).then(function(){{ paint(); }});

  function paint(){{
    ctx.fillStyle = "#FFFDF8"; ctx.fillRect(0,0,w,h);

    ctx.strokeStyle = "#0B1220"; ctx.lineWidth = 8;
    ctx.strokeRect(28,28,w-56,h-56);
    ctx.strokeStyle = "#D4AF37"; ctx.lineWidth = 3;
    ctx.strokeRect(44,44,w-88,h-88);
    ctx.strokeStyle = "#0B1220"; ctx.lineWidth = 1;
    ctx.strokeRect(56,56,w-112,h-112);

    drawCorner(ctx, 56, 56, 1, 1);
    drawCorner(ctx, w-56, 56, -1, 1);
    drawCorner(ctx, 56, h-56, 1, -1);
    drawCorner(ctx, w-56, h-56, -1, -1);

    ctx.textAlign = "center";
    ctx.fillStyle = "#0B1220";
    ctx.font = "700 24px 'Playfair Display', Georgia";
    ctx.fillText({json.dumps(BRAND_NAME.upper())}, w/2, 128);

    ctx.font = "900 54px 'Playfair Display', Georgia";
    ctx.fillStyle = "#0B1220";
    ctx.fillText("CERTIFICATE", w/2, 205);
    ctx.font = "700 26px 'Playfair Display', Georgia";
    ctx.fillStyle = "#B8860B";
    ctx.save(); ctx.letterSpacing = "6px";
    ctx.fillText("O F   A C H I E V E M E N T", w/2, 245);
    ctx.restore();

    ctx.strokeStyle = "#D4AF37"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(w/2-90, 270); ctx.lineTo(w/2-14, 270); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(w/2+14, 270); ctx.lineTo(w/2+90, 270); ctx.stroke();
    ctx.fillStyle = "#D4AF37";
    ctx.beginPath(); ctx.moveTo(w/2,262); ctx.lineTo(w/2+8,270); ctx.lineTo(w/2,278); ctx.lineTo(w/2-8,270); ctx.closePath(); ctx.fill();

    ctx.font = "italic 22px 'Playfair Display', Georgia";
    ctx.fillStyle = "#4A4F55";
    ctx.fillText("This certificate is proudly presented to", w/2, 335);

    ctx.font = "italic 90px 'Great Vibes', cursive";
    ctx.fillStyle = "#0B1220";
    ctx.fillText(req.name || "", w/2, 440);
    ctx.strokeStyle = "#D4AF37"; ctx.lineWidth = 1.5;
    var nameWidth = Math.min(ctx.measureText(req.name||"").width + 40, 900);
    ctx.beginPath(); ctx.moveTo(w/2-nameWidth/2, 465); ctx.lineTo(w/2+nameWidth/2, 465); ctx.stroke();

    ctx.font = "22px 'Playfair Display', Georgia";
    ctx.fillStyle = "#4A4F55";
    ctx.fillText("for successfully completing the course", w/2, 515);

    ctx.font = "700 34px 'Playfair Display', Georgia";
    ctx.fillStyle = "#0056D2";
    ctx.fillText(req.course || "", w/2, 565);

    drawSeal(ctx, w/2, 780);

    ctx.textAlign = "left";
    ctx.font = "16px Arial"; ctx.fillStyle = "#6A6F73";
    ctx.fillText("Date: " + (req.date || ""), 130, h-190);
    ctx.fillText("Certificate ID: " + (req.id ? req.id.slice(0,8).toUpperCase() : ""), 130, h-165);

    drawSignature(ctx, canvas);
  }}
}}

function drawSignature(ctx, canvas){{
  var w = canvas.width, h = canvas.height;
  var sigImg = new Image();
  sigImg.crossOrigin = "anonymous";
  sigImg.onload = function(){{
    var sw = 260, sh = sw * (sigImg.height/sigImg.width);
    ctx.drawImage(sigImg, w-sw-160, h-sh-215, sw, sh);
    finishSignatureBlock(ctx, canvas);
  }};
  sigImg.onerror = function(){{
    ctx.font = "italic 46px 'Great Vibes', cursive";
    ctx.fillStyle = "#0B1220";
    ctx.textAlign = "center";
    ctx.fillText({json.dumps(BRAND_CONTACT_NAME)}, w-290, h-155);
    finishSignatureBlock(ctx, canvas);
  }};
  sigImg.src = "signature.png";
}}
function finishSignatureBlock(ctx, canvas){{
  var w = canvas.width, h = canvas.height;
  ctx.strokeStyle = "#0B1220"; ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(w-420, h-140); ctx.lineTo(w-160, h-140); ctx.stroke();
  ctx.font = "700 20px 'Playfair Display', Georgia"; ctx.fillStyle = "#0B1220"; ctx.textAlign = "center";
  ctx.fillText({json.dumps(BRAND_CONTACT_NAME)}, w-290, h-115);
  ctx.font = "16px Arial"; ctx.fillStyle = "#6A6F73";
  ctx.fillText({json.dumps(BRAND_CONTACT_TITLE)}, w-290, h-92);
  document.getElementById("cert-modal").classList.add("show");
}}

function fkcDownloadCert(){{
  if(!currentReq) return;
  var canvas = document.getElementById("cert-canvas");
  var link = document.createElement("a");
  link.download = "Certificate-" + (currentReq.name||"student").replace(/\\s+/g,"_") + ".png";
  link.href = canvas.toDataURL("image/png");
  link.click();
  db.collection("certificate_requests").doc(currentReq.id).update({{ status: "issued" }});
}}
</script>
    """
    head_html = f"""<!DOCTYPE html>
<html lang="ur"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Admin — {html.escape(BRAND_NAME)}</title>
<meta name="robots" content="noindex, nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Great+Vibes&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore-compat.js"></script>
<style>{BASE_CSS}{extra_css}</style></head><body><div class="wrap">
"""
    return head_html + body + FOOT_TAIL


# ---------------------------------------------------------------------
# 4b. Self-heal — pehle se published lessons mein agar koi translation
# degenerate/repetitive nikle (jaise "jaa'oon jaa'oon..." wala Sindhi
# bug), to sirf usi lang ko dobara generate karo. Baaki sab (jin
# lessons mein translations hain hi nahi, ya theek hain) bilkul chhoo
# nahi mate — sirf broken cheez fix hoti hai.
# ---------------------------------------------------------------------
def _purge_lesson_video_cache(slug, day_num):
    """Lesson ka cached narration video/audio/captions hata deta hai, taake
    agli build mein wo dobara (sahi awaaz/zaban ke sath) generate ho.
    Zaroori hai jab translations heal hoti hain — warna purana video
    (jo galat/fallback awaaz se bana tha) hamesha ke liye cached reh
    jata, kyunke generate_lesson_narration_video sirf missing file par
    hi kaam karta hai."""
    padded = f"{day_num:03d}"
    work_dir = os.path.join(VIDEOS_DIR, slug)
    for ext in ("mp4", "mp3", "srt", "narration.txt"):
        p = os.path.join(work_dir, f"day-{padded}.{ext}")
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


def heal_missing_images(posts, only_slug=None):
    """generate_lesson_image() sirf lesson ke PEHLE build par call hoti hai
    (main() ki pehli loop mein) — agar us waqt Pollinations fail ho jaye
    (network/rate-limit/timeout), to us lesson ki image kabhi dobara try
    nahi hoti thi, permanently missing reh jati thi — aur usi wajah se
    video bhi kabhi nahi ban pata (video ko image chahiye hoti hai).
    Ye function har build ke shuru mein EXISTING lessons check karta hai
    aur jin ki image abhi tak nahi bani, un par generate_lesson_image
    dobara try karta hai — taake ek transient fail hamesha ke liye missing
    na reh jaye.

    only_slug diya ho (COURSE_SLUG se scheduled run) to SIRF usi course ke
    lessons heal hote hain — poore site (29 courses) ko har raat har
    workflow mein heal karna 3+ ghante tak le jata tha, jis se saare
    workflows overlap ho kar git push par takra jate the aur merge-conflict
    storm ban jata tha. only_slug None ho (manual/heal-all run) to purana
    (sab courses) behavior chalta hai.

    Circuit breaker: agar Pollinations hi down/blocked ho (jaisa 04-05 Aug
    ki raat hua — har single request 500 de rahi thi), to lagatar retry
    karte rehna sirf waqt zaya karta hai. 6 lagatar images fail hon to ye
    maan lete hain ke API filhaal down hai aur is run ke liye heal rok dete
    hain — agli baar phir try hoga."""
    slugs = [only_slug] if only_slug else list(posts.keys())
    consecutive_fails = 0
    CIRCUIT_LIMIT = 6
    for slug in slugs:
        lessons = posts.get(slug, [])
        course = COURSES.get(slug)
        if not course:
            continue
        for lesson in lessons:
            if consecutive_fails >= CIRCUIT_LIMIT:
                msg = (f"heal_missing_images: {CIRCUIT_LIMIT} images lagatar fail hui — "
                       f"Pollinations shayad down/blocked hai, is run ke liye image healing "
                       f"rok rahe hain (agli baar phir try hoga).")
                print(msg, file=sys.stderr)
                log_error(msg)
                return
            if find_lesson_image(slug, lesson["day"]):
                continue  # already maujood, kuch karne ki zaroorat nahi
            print(f"[{slug}] Day {lesson['day']} ki image missing hai, dobara try ho raha hai...")
            topic_hint = course["topics"][(lesson["day"] - 1) % len(course["topics"])]
            concept_text = lesson["sections"][0][1] if lesson["sections"] else lesson.get("preamble", "")
            ok = generate_lesson_image(
                slug, course, lesson["day"], lesson["title"],
                topic_hint=topic_hint, concept_text=concept_text,
            )
            consecutive_fails = 0 if ok else consecutive_fails + 1
            time.sleep(2)  # thoda space, taake peeche-peeche courses ke beech rate-limit na lage


def heal_degenerate_translations(posts, only_slug=None):
    """... (purana docstring). Circuit breaker: 04-05 Aug ki raat Mistral
    lagatar English/corrupt output de raha tha (quota-exhaustion jaisa
    lagta hai) — 6 lagatar translation-attempts fail hon to ye maan lete
    hain ke API filhaal down/quota-khatam hai aur is run ke liye translation
    healing rok dete hain (agli baar phir try hoga, waqt zaya nahi hota)."""
    changed = False
    consecutive_fails = 0
    CIRCUIT_LIMIT = 6
    slugs = [only_slug] if only_slug else list(posts.keys())
    for slug in slugs:
        lessons = posts.get(slug, [])
        course = COURSES.get(slug)
        if not course:
            continue
        for lesson in lessons:
            if consecutive_fails >= CIRCUIT_LIMIT:
                msg = (f"heal_degenerate_translations: {CIRCUIT_LIMIT} translations lagatar "
                       f"fail hui — Mistral API shayad down/quota-exhausted hai, is run ke "
                       f"liye translation healing rok rahe hain (agli baar phir try hoga).")
                print(msg, file=sys.stderr)
                log_error(msg)
                return changed
            translations = lesson.get("translations") or {}
            missing_codes = set(TRANSLATION_LANGS) - set(translations)
            bad_codes = set()
            for c, d in translations.items():
                other_code = next((oc for oc in translations if oc != c), None)
                other_data = translations.get(other_code) if other_code else None
                if not _translation_is_sane(d, c, lesson.get("preamble", ""), other_data):
                    bad_codes.add(c)
            # missing_codes = translation kabhi bani hi nahi (us din generation
            # fail ho gaya tha) — bad_codes = translation bani lekin
            # corrupt/duplicate nikli. Dono cases mein regenerate karna hai.
            if not missing_codes and not bad_codes:
                continue
            if bad_codes:
                print(f"[{slug}] Day {lesson['day']} mein degenerate/duplicate translation mili ({', '.join(sorted(bad_codes))}), heal ho raha hai...")
            if missing_codes:
                print(f"[{slug}] Day {lesson['day']} mein translation missing hai ({', '.join(sorted(missing_codes))}), generate ho raha hai...")
            padded = f"{lesson['day']:03d}"
            for code in bad_codes:
                cache_path = os.path.join(LESSONS_DIR, slug, f"day-{padded}.{code}.json")
                if os.path.exists(cache_path):
                    try:
                        os.remove(cache_path)
                    except Exception:
                        pass
                translations.pop(code, None)
            needed_codes = bad_codes | missing_codes
            fresh = get_or_generate_translations(
                slug, lesson["day"], lesson["title"], lesson["preamble"], lesson["sections"]
            )
            consecutive_fails = 0 if set(fresh) & needed_codes else consecutive_fails + 1
            translations.update(fresh)
            lesson["translations"] = translations
            # "ur" (missing ya bad, dono cases) heal/generate hui ho to video
            # ka cached voiceover bhi purani/fallback awaaz mein ho sakta hai
            # — usay hata do taake sahi Urdu awaaz (NARRATION_VOICE_UR) ke
            # sath dobara ban jaye.
            if "ur" in bad_codes or "ur" in missing_codes:
                _purge_lesson_video_cache(slug, lesson["day"])
            changed = True
    return changed


# ---------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------
def main():
    posts = load_posts()

    # Sirf ek course chalana ho to COURSE_SLUG env var ya CLI arg se slug lein.
    target_slug = os.environ.get("COURSE_SLUG") or (sys.argv[1] if len(sys.argv) > 1 else None)
    if target_slug and target_slug not in COURSES:
        print(f"Course slug '{target_slug}' COURSES dictionary mein nahi mila.", file=sys.stderr)
        sys.exit(1)

    # Heal sirf isi run ke target course tak scope hai (COURSE_SLUG set ho
    # to) — poore 29-course site ko har raat har workflow mein heal karna
    # ghanton leta tha aur saare workflows ek dusre se git push par takra
    # kar merge-conflict storm bana dete the. Manual full run (COURSE_SLUG
    # khaali) mein purana "heal everything" behavior chalta hai.
    # 👉 Image healing DISABLED — purane lessons ki missing image ab retry
    # nahi hoti, time bachane ke liye. Aisi image/video hamesha missing
    # rahegi jab tak manually add na ki jaye. Wapas chalu karna ho to
    # neeche wali line se '#' hata dein.
    # heal_missing_images(posts, only_slug=target_slug)
    if heal_degenerate_translations(posts, only_slug=target_slug):
        save_posts(posts)

    courses_to_run = {target_slug: COURSES[target_slug]} if target_slug else COURSES
    new_lesson_urls = []  # is run mein bane naye lessons — IndexNow ping ke liye

    for slug, course in courses_to_run.items():
        try:
            existing = posts.get(slug, [])
            next_day = len(existing) + 1
            previous_titles = [l["title"] for l in existing]

            lesson = get_or_generate_lesson(slug, course, next_day, previous_titles)
            if lesson is None:
                continue

            existing.append(lesson)
            posts[slug] = existing
            if SITE_URL:
                new_lesson_urls.append(
                    f"{SITE_URL}/courses/{slug}/posts/{lesson['date']}-{lesson['id']}.html"
                )

            topic_hint = course["topics"][(lesson["day"] - 1) % len(course["topics"])]
            concept_text = lesson["sections"][0][1] if lesson["sections"] else lesson.get("preamble", "")
            generate_lesson_image(
                slug, course, lesson["day"], lesson["title"],
                topic_hint=topic_hint, concept_text=concept_text,
            )
            # Pehle Agnes AI try karein (mentor-style video)
            video_path = None
            if AGNES_API_KEY:
                video_path = generate_agnes_video(slug, lesson, course['name'])

            # Agar Agnes fail ho to existing free method try karein (edge-tts + ffmpeg)
            if not video_path:
                generate_lesson_narration_video(
                    slug, course, lesson, image_source_path=find_lesson_image(slug, lesson["day"])
                )

            os.makedirs(os.path.join(DOCS_DIR, "courses", slug, "posts"), exist_ok=True)
            image_href = publish_lesson_image(slug, lesson["day"])
            video_href = publish_lesson_video(slug, lesson["day"])
            prev_lesson = existing[-2] if len(existing) > 1 else None
            prev_href = f"{prev_lesson['date']}-{prev_lesson['id']}.html" if prev_lesson else None
            prev_title = prev_lesson["title"] if prev_lesson else None
            page = render_lesson_page(
                slug, course, lesson, is_latest=True, image_href=image_href, video_href=video_href,
                prev_href=prev_href, prev_title=prev_title,
            )
            with open(
                os.path.join(DOCS_DIR, "courses", slug, "posts", f"{lesson['date']}-{lesson['id']}.html"),
                "w", encoding="utf-8",
            ) as f:
                f.write(page)

        except Exception as e:
            msg = f"[{slug}] lesson generation is baar fail hui, agla course try ho raha hai: {e}"
            print(msg, file=sys.stderr)
            log_error(msg)
            continue

    save_posts(posts)

    # rebuild course pages — index.html HAMESHA sab COURSES ke liye likha
    # jata hai (chahe generation sirf ek course ke liye hui ho), taake har
    # course ka page hamesha maujood rahe. Lekin per-lesson kaam (image
    # check, video generation, poori lesson-page re-render) SIRF is run ke
    # target course ke liye — pehle ye har workflow mein sab 29 courses ke
    # liye chalta tha, jo 3+ ghante le leta tha aur raat ke saare workflows
    # overlap ho kar git push par takra jate the. Doosre courses ke lesson
    # pages waise hi rehte hain jaise unke apne run mein bane the — unme
    # kuch badla hi nahi to dobara likhne ki zaroorat nahi.
    for slug, course in COURSES.items():
        try:
            lessons = posts.get(slug, [])
            os.makedirs(os.path.join(DOCS_DIR, "courses", slug, "posts"), exist_ok=True)
            with open(os.path.join(DOCS_DIR, "courses", slug, "index.html"), "w", encoding="utf-8") as f:
                f.write(render_course_page(slug, course, lessons))

            if target_slug and slug != target_slug:
                continue  # is run ka target nahi — per-lesson kaam skip

            # re-render every lesson page so only the newest carries "Latest"
            for i, lesson in enumerate(lessons):
                image_href = publish_lesson_image(slug, lesson["day"])
                generate_lesson_narration_video(
                    slug, course, lesson, image_source_path=find_lesson_image(slug, lesson["day"])
                )
                video_href = publish_lesson_video(slug, lesson["day"])
                prev_href = f"{lessons[i-1]['date']}-{lessons[i-1]['id']}.html" if i > 0 else None
                prev_title = lessons[i-1]["title"] if i > 0 else None
                next_href = f"{lessons[i+1]['date']}-{lessons[i+1]['id']}.html" if i < len(lessons) - 1 else None
                next_title = lessons[i+1]["title"] if i < len(lessons) - 1 else None
                page = render_lesson_page(
                    slug, course, lesson, is_latest=(i == len(lessons) - 1),
                    image_href=image_href, video_href=video_href,
                    prev_href=prev_href, prev_title=prev_title,
                    next_href=next_href, next_title=next_title,
                )
                with open(
                    os.path.join(DOCS_DIR, "courses", slug, "posts", f"{lesson['date']}-{lesson['id']}.html"),
                    "w", encoding="utf-8",
                ) as f:
                    f.write(page)
        except Exception as e:
            msg = f"[{slug}] rebuild is baar fail hui, agla course try ho raha hai: {e}"
            print(msg, file=sys.stderr)
            log_error(msg)
            continue

    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_home(posts))

    # Games Zone — standalone hub, 3 memory-match levels (har lesson page
    # par bhi wahi game hai, yeh ek repeat-visit-friendly hub page hai).
    with open(os.path.join(DOCS_DIR, "games.html"), "w", encoding="utf-8") as f:
        f.write(render_games_page())

    # Certificate admin panel — sirf Fazul Khan ke liye (Firebase config
    # fill hone par hi actual kaam karega, warna setup-instructions dikhata hai).
    with open(os.path.join(DOCS_DIR, "admin-certificates.html"), "w", encoding="utf-8") as f:
        f.write(render_admin_certificates_page())

    # PWA files — har build par (taake naye icons/manifest changes turant
    # reflect hon). Icons khud generate ho jate hain (agar manually upload
    # nahi kiye) taake install icon hamesha dikhe.
    with open(os.path.join(DOCS_DIR, MANIFEST_FILENAME), "w", encoding="utf-8") as f:
        f.write(build_manifest_json())
    with open(os.path.join(DOCS_DIR, SW_FILENAME), "w", encoding="utf-8") as f:
        f.write(build_service_worker_js())
    ensure_pwa_icons()

    # version.json — live-update check ke liye (khuli tabs/PWA har 8s
    # mein ye file check karte hain; build_stamp badalte hi khud reload).
    with open(os.path.join(DOCS_DIR, VERSION_FILENAME), "w", encoding="utf-8") as f:
        json.dump({"build": BUILD_STAMP}, f)

    # SEO — sitemap.xml + robots.txt (SITE_URL set hona zaroori hai warna
    # sitemap skip ho jati hai, robots.txt phir bhi likhi jati hai).
    sitemap_xml = build_sitemap_xml(posts)
    if sitemap_xml:
        with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
            f.write(sitemap_xml)
    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(build_robots_txt())
    with open(os.path.join(DOCS_DIR, "ads.txt"), "w", encoding="utf-8") as f:
        f.write(build_ads_txt())

    # RSS feed — SITE_URL set hona zaroori hai.
    rss_xml = build_rss_feed(posts)
    if rss_xml:
        with open(os.path.join(DOCS_DIR, "feed.xml"), "w", encoding="utf-8") as f:
            f.write(rss_xml)

    # IndexNow — is run mein bane naye lessons ka fast-index ping
    # (Bing/Yandex). INDEXNOW_KEY set na ho to yeh khud skip ho jata hai.
    write_indexnow_key_file()
    ping_indexnow(new_lesson_urls)

    print("Done — site docs/ mein update ho gayi.")


if __name__ == "__main__":
    main()
