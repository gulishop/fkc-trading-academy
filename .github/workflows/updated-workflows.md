# Updated Workflow Files — GEMINI_API_KEY se GROQ_API_KEY

Har section ka poora content us naam ki file mein paste karein (`.github/workflows/<filename>`).

## `.github/workflows/create-lessons-affiliate-marketing.yml`

```yaml
name: create-lessons-affiliate-marketing

on:
  schedule:
    - cron: '0 12 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-affiliate-marketing
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Affiliate Marketing ka lesson generate karo
        env:
          COURSE_SLUG: affiliate-marketing
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Affiliate Marketing — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-ai-content-writing.yml`

```yaml
name: create-lessons-ai-content-writing

on:
  schedule:
    - cron: '40 11 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-ai-content-writing
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Ai Content Writing ka lesson generate karo
        env:
          COURSE_SLUG: ai-content-writing
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Ai Content Writing — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-ai-tools.yml`

```yaml
name: create-lessons-ai-tools

on:
  schedule:
    - cron: '20 10 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-ai-tools
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Ai Tools ka lesson generate karo
        env:
          COURSE_SLUG: ai-tools
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Ai Tools — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-amazon-fba.yml`

```yaml
name: create-lessons-amazon-fba

on:
  schedule:
    - cron: '40 10 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-amazon-fba
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Amazon Fba ka lesson generate karo
        env:
          COURSE_SLUG: amazon-fba
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Amazon Fba — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-daraz-seller.yml`

```yaml
name: create-lessons-daraz-seller

on:
  schedule:
    - cron: '50 10 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-daraz-seller
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Daraz Seller ka lesson generate karo
        env:
          COURSE_SLUG: daraz-seller
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Daraz Seller — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-digital-marketing-seo.yml`

```yaml
name: create-lessons-digital-marketing-seo

on:
  schedule:
    - cron: '20 11 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-digital-marketing-seo
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Digital Marketing Seo ka lesson generate karo
        env:
          COURSE_SLUG: digital-marketing-seo
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Digital Marketing Seo — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-dropshipping.yml`

```yaml
name: create-lessons-dropshipping

on:
  schedule:
    - cron: '0 11 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-dropshipping
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Dropshipping ka lesson generate karo
        env:
          COURSE_SLUG: dropshipping
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Dropshipping — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-facebook-page-growth.yml`

```yaml
name: create-lessons-facebook-page-growth

on:
  schedule:
    - cron: '30 10 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-facebook-page-growth
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Facebook Page Growth ka lesson generate karo
        env:
          COURSE_SLUG: facebook-page-growth
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Facebook Page Growth — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-freelancing.yml`

```yaml
name: create-lessons-freelancing

on:
  schedule:
    - cron: '10 11 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-freelancing
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Freelancing ka lesson generate karo
        env:
          COURSE_SLUG: freelancing
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Freelancing — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-graphic-design-canva.yml`

```yaml
name: create-lessons-graphic-design-canva

on:
  schedule:
    - cron: '30 11 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-graphic-design-canva
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Graphic Design Canva ka lesson generate karo
        env:
          COURSE_SLUG: graphic-design-canva
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Graphic Design Canva — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-no-code-app-dev.yml`

```yaml
name: create-lessons-no-code-app-dev

on:
  schedule:
    - cron: '20 12 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-no-code-app-dev
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: No Code App Dev ka lesson generate karo
        env:
          COURSE_SLUG: no-code-app-dev
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: No Code App Dev — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-print-on-demand.yml`

```yaml
name: create-lessons-print-on-demand

on:
  schedule:
    - cron: '10 12 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-print-on-demand
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Print On Demand ka lesson generate karo
        env:
          COURSE_SLUG: print-on-demand
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Print On Demand — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-social-media-marketing.yml`

```yaml
name: create-lessons-social-media-marketing

on:
  schedule:
    - cron: '10 10 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-social-media-marketing
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Social Media Marketing ka lesson generate karo
        env:
          COURSE_SLUG: social-media-marketing
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Social Media Marketing — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-video-editing.yml`

```yaml
name: create-lessons-video-editing

on:
  schedule:
    - cron: '50 11 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-video-editing
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Video Editing ka lesson generate karo
        env:
          COURSE_SLUG: video-editing
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Video Editing — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```

## `.github/workflows/create-lessons-youtube-automation.yml`

```yaml
name: create-lessons-youtube-automation

on:
  schedule:
    - cron: '0 10 * * *'
  workflow_dispatch: {}

concurrency:
  group: create-lessons-youtube-automation
  cancel-in-progress: false

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - name: Repo checkout karo
        uses: actions/checkout@v4

      - name: Python setup karo
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Dependencies install karo
        run: |
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Youtube Automation ka lesson generate karo
        env:
          COURSE_SLUG: youtube-automation
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          SITE_URL: ${{ secrets.SITE_URL }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          FB_PAGE_ID: ${{ secrets.FB_PAGE_ID }}
          FB_PAGE_ACCESS_TOKEN: ${{ secrets.FB_PAGE_ACCESS_TOKEN }}
        run: python generate_post.py

      - name: Changes commit aur push karo
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add -A
          git diff --staged --quiet || git commit -m "Auto: Youtube Automation — naya lesson [skip ci]"
          git pull --rebase origin main
          git push
```
