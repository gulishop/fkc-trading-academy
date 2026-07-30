#!/usr/bin/env python3
"""
FKC Trading Academy — lesson page builder.

Reads one lessons/day-XX.md file and writes docs/index.html:
  - the lesson (concept / example) as reading material
  - a separate "Assignment" box (practice / mini project)
  - a "Share on WhatsApp" button for the teacher (opens WhatsApp's
    chat picker with the lesson pre-filled — no bot/API needed)
  - a small "Submit assignment" box where a student types their
    answer and taps a button that opens WhatsApp with it pre-filled,
    so they can pick the class group and send it themselves

Usage: python3 scripts/build_page.py <lesson_file> <day_number> <out_html>
"""
import sys
import re
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

    sections = []  # list of (label, content) — keeps original order
    for i in range(1, len(parts), 2):
        label = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections.append((label, content))

    return title, preamble, sections


def classify(sections):
    lesson_parts, assignment_parts = [], []
    assignment_words = ["practice", "assignment", "project", "kaam", "amaliyat", "mashq"]
    for label, content in sections:
        if any(w in label.lower() for w in assignment_words):
            assignment_parts.append((label, content))
        else:
            lesson_parts.append((label, content))
    return lesson_parts, assignment_parts


def md_to_html(text: str) -> str:
    """Very small markdown->html: fenced code blocks + paragraphs."""
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


def render(day_num: int, title: str, preamble: str, lesson_parts, assignment_parts, share_text: str) -> str:
    lesson_html = md_to_html(preamble)
    for label, content in lesson_parts:
        lesson_html += f'<h3>{html.escape(label)}</h3>\n{md_to_html(content)}'

    assignment_html = ""
    for label, content in assignment_parts:
        assignment_html += f'<h3>{html.escape(label)}</h3>\n{md_to_html(content)}'
    if not assignment_html:
        assignment_html = "<p>Aaj koi alag assignment nahi — lesson mein diya gaya practice karein.</p>"

    wa_share_lesson = f"https://wa.me/?text={quote(share_text)}"
    padded = f"{day_num:02d}" if day_num < 100 else f"{day_num:03d}"

    return f"""<!DOCTYPE html>
<html lang="ur" dir="ltr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FKC Trading Academy — Day {padded}</title>
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
    margin-bottom: 24px;
  }}
  .ticker .sym {{ font-weight: 600; }}
  .ticker .lbl {{ color: var(--muted); font-weight: 400; }}
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
</style>
</head>
<body>
  <div class="wrap">
    <div class="ticker">
      <span class="sym">FKC · {padded}</span>
      <span class="lbl">daily lesson</span>
    </div>

    <h1>{html.escape(title) if title else f"Day {padded}"}</h1>

    <div class="card lesson">
      {lesson_html}
      <a class="btn" href="{wa_share_lesson}" target="_blank" rel="noopener">Share lesson on WhatsApp</a>
    </div>

    <div class="card assignment">
      <h2>Assignment</h2>
      <div class="sub">Aaj ka kaam — mukammal karke neeche apna jawab likhein aur WhatsApp par group ko bhej dein.</div>
      {assignment_html}
      <input type="text" id="student-name" placeholder="Apna naam likhein">
      <textarea id="student-answer" placeholder="Apna code ya jawab yahan paste/likhein..."></textarea>
      <br>
      <button class="btn green" onclick="submitAssignment()">Send via WhatsApp</button>
    </div>

    <footer>FKC Trading Academy — automatically updated</footer>
  </div>

<script>
const SHEET_WEBHOOK_URL = "{SHEET_WEBHOOK_URL}";

function submitAssignment() {{
  const name = document.getElementById('student-name').value.trim() || 'Student';
  const answer = document.getElementById('student-answer').value.trim();
  if (!answer) {{ alert('Pehle apna jawab likhein.'); return; }}

  if (SHEET_WEBHOOK_URL) {{
    const formData = new URLSearchParams();
    formData.append('day', '{padded}');
    formData.append('name', name);
    formData.append('answer', answer);
    fetch(SHEET_WEBHOOK_URL, {{ method: 'POST', mode: 'no-cors', body: formData }}).catch(() => {{}});
  }}

  const text = "Day {padded} Assignment — " + name + ":\\n\\n" + answer;
  window.open("https://wa.me/?text=" + encodeURIComponent(text), "_blank");
}}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: build_page.py <lesson_file> <day_number> <out_html>", file=sys.stderr)
        sys.exit(1)

    lesson_file, day_arg, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    DAY_NUM = int(day_arg)

    with open(lesson_file, encoding="utf-8") as f:
        raw = f.read()

    title, preamble, sections = parse_lesson(raw)
    lesson_parts, assignment_parts = classify(sections)
    share_text = plain_text_for_share(DAY_NUM, title, preamble, sections)
    html_out = render(DAY_NUM, title, preamble, lesson_parts, assignment_parts, share_text)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"Page likh di: {out_path}")
