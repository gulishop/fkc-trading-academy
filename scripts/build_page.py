#!/usr/bin/env python3
"""
FKC Trading Academy — lesson archive page builder.

Reads lessons/day-XX.md files up to the count in lessons/.last-posted
(so pre-written future lessons never leak early) and writes
docs/index.html as a running archive: newest posted lesson on top,
every older lesson stays below it. Each lesson keeps its own reading
material, Assignment box, WhatsApp share button, and student submit
box. An "Answer Key" section (if present in the .md) is parsed out,
hidden from display, and used by JS to give the student instant
feedback ("Excellent!" / "Try again") before their answer goes to
WhatsApp.

Usage: python3 scripts/build_page.py <lessons_dir> <out_html>
"""
import sys
import re
import os
import html
from urllib.parse import quote

# Paste your Google Apps Script "Web app" URL here after Step 2 setup
# (ends in /exec). Every assignment submission gets sent here so it
# lands as a row in your Google Sheet automatically.
SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbx1UBGM5GyFx4xYOIt5BbRE0k-LaURaZXXwuU3hJWYTYq3fEMiFGeb68gdXtutKJmBi/exec"


def parse_lesson(text: str):
    lines = text.strip("\n").split("\n")
    title = ""
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
        sections.append((label, content))

    return title, preamble, sections


def classify(sections):
    lesson_parts, assignment_parts, answer_key_parts = [], [], []
    assignment_words = ["practice", "assignment", "project", "kaam", "amaliyat", "mashq"]
    answer_key_words = ["answer key", "sahi jawab", "jawab key"]
    for label, content in sections:
        low = label.lower()
        if any(w in low for w in answer_key_words):
            answer_key_parts.append((label, content))
        elif any(w in low for w in assignment_words):
            assignment_parts.append((label, content))
        else:
            lesson_parts.append((label, content))
    return lesson_parts, assignment_parts, answer_key_parts


def md_to_html(text: str) -> str:
    if not text:
        return ""
    blocks = re.split(r"```(?:\w+)?\n(.*?)```", text, flags=re.S)
    out = []
    for i, block in enumerate(blocks):
        if i % 2 == 1:
            out.append(f"<pre><code>{html.escape(block.strip())}</code></pre>")
        else:
            paras = [p.strip() for p in block.strip().split("\n\n") if p.strip()]
            for p in paras:
                p = html.escape(p).replace("\n", "<br>")
                out.append(f"<p>{p}</p>")
    return "\n".join(out)


def plain_text_for_share(day_num, title, preamble, sections):
    chunks = [title if title else f"Day {day_num} lesson"]
    if preamble:
        chunks.append(preamble)
    for label, content in sections:
        chunks.append(f"{label}:\n{content}")
    return "\n\n".join(chunks)


def phase_info(day_num: int):
    """Returns (phase_label, day_in_phase, total_in_phase_or_None)."""
    if day_num <= 90:
        return "Coding · Python", day_num, 90
    elif day_num <= 120:
        return "E-commerce", day_num - 90, 30
    else:
        return "Trading / Markets", day_num - 120, None


def padded_str(day_num: int) -> str:
    return f"{day_num:02d}" if day_num < 100 else f"{day_num:03d}"


def answer_key_keywords(answer_key_parts) -> str:
    """Combine all Answer Key section content into a comma-separated,
    lowercased keyword string used for client-side matching."""
    raw = ", ".join(content for _, content in answer_key_parts)
    # split on commas, clean each keyword
    keywords = [k.strip().lower() for k in raw.split(",") if k.strip()]
    return ", ".join(keywords)


def render_lesson_block(day_num: int, title: str, preamble: str, lesson_parts, assignment_parts, answer_key_parts, is_latest: bool):
    padded = padded_str(day_num)
    phase_label, day_in_phase, total_in_phase = phase_info(day_num)
    progress_text = f"{phase_label} · Day {day_in_phase}/{total_in_phase}" if total_in_phase else f"{phase_label} · Day {day_in_phase}"

    lesson_html = md_to_html(preamble)
    for label, content in lesson_parts:
        lesson_html += f'<h3>{html.escape(label)}</h3>\n{md_to_html(content)}'

    assignment_html = ""
    for label, content in assignment_parts:
        assignment_html += f'<h3>{html.escape(label)}</h3>\n{md_to_html(content)}'
    if not assignment_html:
        assignment_html = "<p>Aaj koi alag assignment nahi — lesson mein diya gaya practice karein.</p>"

    all_sections = lesson_parts + assignment_parts
    share_text = plain_text_for_share(day_num, title, preamble, all_sections)
    wa_share_lesson = f"https://wa.me/?text={quote(share_text)}"

    search_blob = html.escape((title + " " + preamble + " " + " ".join(c for _, c in all_sections)).lower())
    latest_badge = '<span class="latest-tag">Latest</span>' if is_latest else ""

    answer_key = html.escape(answer_key_keywords(answer_key_parts))

    return f"""
    <div class="lesson-block" id="day-{padded}" data-search="{search_blob}">
      {latest_badge}
      <span class="phase-tag">{html.escape(progress_text)}</span>
      <h1>{html.escape(title) if title else f"Day {padded}"}</h1>
      <div class="card lesson">
        {lesson_html}
        <a class="btn" href="{wa_share_lesson}" target="_blank" rel="noopener">Share lesson on WhatsApp</a>
      </div>
      <div class="card assignment">
        <h2>Assignment</h2>
        <div class="sub">Aaj ka kaam — mukammal karke neeche apna jawab likhein aur WhatsApp par group ko bhej dein.</div>
        {assignment_html}
        <input type="text" id="student-name-{padded}" placeholder="Apna naam likhein">
        <textarea id="student-answer-{padded}" placeholder="Apna code ya jawab yahan paste/likhein..." data-answer-key="{answer_key}"></textarea>
        <br>
        <button class="btn green" onclick="submitAssignment('{padded}')">Send via WhatsApp</button>
      </div>
    </div>
"""


def render_page(blocks_html: str, toc_html: str, latest_padded: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ur" dir="ltr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FKC Trading Academy — Day {latest_padded}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink: #EDECE4;
    --paper: #0B1220;
    --panel: #111a2b;
    --line: #22304a;
    --gold: #D4A73A;
    --green: #3FB68B;
    --red: #E2574C;
    --muted: #93a0b8;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--paper);
    color: var(--ink);
    font-family: 'IBM Plex Mono', monospace;
    line-height: 1.6;
  }}
  .wrap {{ max-width: 720px; margin: 0 auto; padding: 32px 20px 80px; }}
  .ticker {{
    display: flex;
    align-items: baseline;
    gap: 10px;
    font-family: 'IBM Plex Mono', monospace;
    color: var(--gold);
    letter-spacing: 0.08em;
    font-size: 14px;
    border-bottom: 1px solid var(--line);
    padding-bottom: 14px;
    margin-bottom: 20px;
  }}
  .ticker .sym {{ font-weight: 600; }}
  .ticker .lbl {{ color: var(--muted); font-weight: 400; }}
  .toc {{
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 14px;
  }}
  .toc a {{
    color: var(--gold);
    text-decoration: none;
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 4px 10px;
    font-size: 12px;
  }}
  .toc a:hover {{ border-color: var(--gold); }}
  #search-box {{
    width: 100%;
    background: #060a12;
    border: 1px solid var(--line);
    border-radius: 4px;
    color: var(--ink);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 14px;
    padding: 10px 12px;
    margin-bottom: 28px;
  }}
  .lesson-block {{ margin-bottom: 44px; }}
  .lesson-block:not(:first-child) {{ padding-top: 36px; border-top: 1px dashed var(--line); }}
  .lesson-block h1 {{ font-size: 26px; margin: 6px 0 20px; }}
  .latest-tag {{
    display: inline-block;
    background: var(--gold);
    color: #0B1220;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 3px;
    margin-right: 8px;
  }}
  .phase-tag {{
    display: inline-block;
    color: var(--muted);
    font-size: 11px;
    letter-spacing: 0.04em;
  }}
  h1 {{
    font-family: 'Fraunces', serif;
    font-weight: 700;
    font-size: 34px;
    line-height: 1.15;
    margin: 0 0 28px;
    color: var(--ink);
  }}
  h3 {{
    font-family: 'Fraunces', serif;
    font-weight: 500;
    font-size: 18px;
    color: var(--gold);
    margin: 22px 0 6px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  p {{ margin: 8px 0; color: var(--ink); font-size: 15px; }}
  pre {{
    background: #060a12;
    border: 1px solid var(--line);
    border-radius: 4px;
    padding: 14px;
    overflow-x: auto;
    font-size: 13.5px;
  }}
  code {{ font-family: 'IBM Plex Mono', monospace; }}
  .card {{
    background: var(--panel);
    border: 1px solid var(--line);
    border-left: 3px solid var(--gold);
    border-radius: 6px;
    padding: 20px 22px;
    margin-bottom: 22px;
  }}
  .card.assignment {{ border-left-color: var(--green); }}
  .card.assignment h2 {{ color: var(--green); }}
  h2 {{
    font-family: 'Fraunces', serif;
    font-size: 20px;
    margin: 0 0 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}
  .sub {{ color: var(--muted); font-size: 13px; margin-bottom: 14px; }}
  textarea {{
    width: 100%;
    min-height: 110px;
    background: #060a12;
    border: 1px solid var(--line);
    border-radius: 4px;
    color: var(--ink);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 14px;
    padding: 12px;
    resize: vertical;
  }}
  input[type=text] {{
    width: 100%;
    background: #060a12;
    border: 1px solid var(--line);
    border-radius: 4px;
    color: var(--ink);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 14px;
    padding: 10px 12px;
    margin-bottom: 10px;
  }}
  .btn {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--gold);
    color: #0B1220;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    font-size: 14px;
    text-decoration: none;
    padding: 12px 18px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 8px;
  }}
  .btn.green {{ background: var(--green); }}
  .btn:active {{ transform: translateY(1px); }}
  footer {{ color: var(--muted); font-size: 12px; margin-top: 40px; text-align: center; }}

  /* Feedback popup */
  .popup-overlay {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(6, 10, 18, 0.75);
    align-items: center;
    justify-content: center;
    z-index: 999;
    padding: 20px;
  }}
  .popup-overlay.show {{ display: flex; }}
  .popup-box {{
    background: var(--panel);
    border: 1px solid var(--line);
    border-left: 4px solid var(--green);
    border-radius: 8px;
    padding: 24px;
    max-width: 340px;
    width: 100%;
    text-align: center;
  }}
  .popup-box.wrong {{ border-left-color: var(--red); }}
  .popup-box .emoji {{ font-size: 34px; margin-bottom: 8px; }}
  .popup-box h3 {{ color: var(--ink); margin: 0 0 8px; text-transform: none; font-size: 19px; }}
  .popup-box.wrong h3 {{ color: var(--ink); }}
  .popup-box p {{ color: var(--muted); font-size: 13.5px; margin-bottom: 16px; }}
  .popup-box .btn {{ width: 100%; text-align: center; justify-content: center; }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="ticker">
      <span class="sym">FKC</span>
      <span class="lbl">daily lessons — archive</span>
    </div>

    <div class="toc">
{toc_html}
    </div>
    <input type="text" id="search-box" placeholder="Purana lesson dhoondein (jaise: variables, loops, risk)..." oninput="filterLessons()">

    <div id="lessons-container">
{blocks_html}
    </div>

    <footer>FKC Trading Academy — automatically updated</footer>
  </div>

  <div class="popup-overlay" id="feedback-popup">
    <div class="popup-box" id="feedback-box">
      <div class="emoji" id="feedback-emoji"></div>
      <h3 id="feedback-title"></h3>
      <p id="feedback-msg"></p>
      <button class="btn green" onclick="closePopupAndSend()">Theek hai — WhatsApp par bhejein</button>
    </div>
  </div>

<script>
const SHEET_WEBHOOK_URL = "{SHEET_WEBHOOK_URL}";
let pendingSend = null;

function checkAnswer(answer, keyStr) {{
  if (!keyStr) return null; // no answer key set for this lesson — skip check
  const keywords = keyStr.split(",").map(k => k.trim()).filter(Boolean);
  if (keywords.length === 0) return null;
  const a = answer.toLowerCase();
  return keywords.some(k => a.includes(k));
}}

function submitAssignment(day) {{
  const nameEl = document.getElementById('student-name-' + day);
  const answerEl = document.getElementById('student-answer-' + day);
  const name = nameEl.value.trim() || 'Student';
  const answer = answerEl.value.trim();
  if (!answer) {{ alert('Pehle apna jawab likhein.'); return; }}

  pendingSend = {{ day, name, answer }};

  const keyStr = answerEl.getAttribute('data-answer-key') || '';
  const isCorrect = checkAnswer(answer, keyStr);

  const box = document.getElementById('feedback-box');
  const emoji = document.getElementById('feedback-emoji');
  const title = document.getElementById('feedback-title');
  const msg = document.getElementById('feedback-msg');

  if (isCorrect === null) {{
    // No answer key available — just confirm submission
    box.className = 'popup-box';
    emoji.textContent = '📩';
    title.textContent = 'Jawab tayyar hai';
    msg.textContent = 'Ab WhatsApp par bhej dein.';
  }} else if (isCorrect) {{
    box.className = 'popup-box';
    emoji.textContent = '🎉';
    title.textContent = 'Excellent! Sahi jawab';
    msg.textContent = 'Shabash! Bilkul theek — ab isse WhatsApp par bhej dein.';
  }} else {{
    box.className = 'popup-box wrong';
    emoji.textContent = '🤔';
    title.textContent = 'Dobara koshish karein';
    msg.textContent = 'Ye jawab pura sahi nahi lag raha — lesson dobara padh kar ek baar aur try karein. Chahen to abhi bhi bhej sakte hain.';
  }}

  document.getElementById('feedback-popup').classList.add('show');
}}

function closePopupAndSend() {{
  document.getElementById('feedback-popup').classList.remove('show');
  if (!pendingSend) return;
  const {{ day, name, answer }} = pendingSend;

  if (SHEET_WEBHOOK_URL) {{
    const formData = new URLSearchParams();
    formData.append('day', day);
    formData.append('name', name);
    formData.append('answer', answer);
    fetch(SHEET_WEBHOOK_URL, {{ method: 'POST', mode: 'no-cors', body: formData }}).catch(() => {{}});
  }}

  const text = "Day " + day + " Assignment — " + name + ":\\n\\n" + answer;
  window.open("https://wa.me/?text=" + encodeURIComponent(text), "_blank");
  pendingSend = null;
}}

function filterLessons() {{
  const q = document.getElementById('search-box').value.trim().toLowerCase();
  document.querySelectorAll('.lesson-block').forEach(block => {{
    const hay = block.getAttribute('data-search') || '';
    block.style.display = (!q || hay.includes(q)) ? '' : 'none';
  }});
}}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: build_page.py <lessons_dir> <out_html>", file=sys.stderr)
        sys.exit(1)

    lessons_dir, out_path = sys.argv[1], sys.argv[2]

    last_posted_file = os.path.join(lessons_dir, ".last-posted")
    if not os.path.exists(last_posted_file):
        print("lessons/.last-posted nahi mili — abhi tak koi lesson post nahi hua.", file=sys.stderr)
        sys.exit(1)

    with open(last_posted_file, encoding="utf-8") as f:
        last_posted = int(f.read().strip())

    day_files = []
    for day_num in range(1, last_posted + 1):
        padded = padded_str(day_num)
        path = os.path.join(lessons_dir, f"day-{padded}.md")
        if os.path.exists(path):
            day_files.append((day_num, path))

    day_files.sort(key=lambda x: x[0], reverse=True)  # newest first

    if not day_files:
        print("Koi posted lesson file nahi mili.", file=sys.stderr)
        sys.exit(1)

    blocks_html_parts = []
    toc_parts = []
    latest_padded = padded_str(day_files[0][0])

    for i, (day_num, path) in enumerate(day_files):
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        title, preamble, sections = parse_lesson(raw)
        lesson_parts, assignment_parts, answer_key_parts = classify(sections)
        block = render_lesson_block(day_num, title, preamble, lesson_parts, assignment_parts, answer_key_parts, is_latest=(i == 0))
        blocks_html_parts.append(block)

        padded = padded_str(day_num)
        toc_parts.append(f'      <a href="#day-{padded}">Day {padded}</a>')

    html_out = render_page("\n".join(blocks_html_parts), "\n".join(toc_parts), latest_padded)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"Archive page likh di ({len(day_files)} posted lessons): {out_path}")
