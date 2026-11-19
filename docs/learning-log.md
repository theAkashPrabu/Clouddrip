# CloudDrip 💧 Learning Log

A short record of what I built, why, and how I'd explain it in an interview.

---

## Phase 0: Prepare tools & GitHub (18 Nov 2026)

### 0.1 Created the GitHub repo
- **What:** Created the public repo `Clouddrip` with a description, topics, README, Python `.gitignore` and MIT license.
- **Why:** To give the project a professional, searchable home from day one.
- **Interview Q&A:** *"Why use version control on a data project?"*
  → It tracks every change, so I can roll back mistakes, show how the project grew, and collaborate safely.

### 0.2 Installed the core tools (macOS)
- **What:** Installed the Command Line Developer Tools (Git 2.50), Python 3.15 and VS Code, and set up the `code` terminal command.
- **Why:** These are the core tools for writing, running and version-controlling the pipeline.
- **Interview Q&A:** *"Why not use the Mac's built-in Python?"*
  → It's old (3.9) and used by macOS itself. A separate, current version avoids breaking the system and gets security fixes.

### 0.3 Configured Git and cloned the repo
- **What:** Set my Git name and GitHub noreply email, then cloned the repo to `~/Projects/Clouddrip`.
- **Why:** The noreply email links commits to my GitHub profile while keeping my personal email private.
- **Interview Q&A:** *"What's the difference between Git and GitHub?"*
  → Git is the version-control tool on my machine; GitHub is the online host where the repo is stored and shared.

### 0.4 Created the folder structure
- **What:** Created `src/ingestion`, `src/transform`, `sql`, `adf`, `powerbi`, `docs`, `tests`, with `.gitkeep` files so Git tracks the empty folders.
- **Why:** Each pipeline stage has its own home, so the repo is easy to read and maintain.
- **Interview Q&A:** *"How do you organise a data engineering repo?"*
  → By pipeline stage: ingestion, transformation, SQL models, orchestration, reporting, docs and tests.

### 0.5 Set up a virtual environment and made the first commit
- **What:** Created `.venv`, installed `requests`, `pandas`, `python-dotenv`, saved versions to `requirements.txt`, then committed and pushed.
- **Why:** Keeps dependencies isolated and reproducible on any machine.
- **Interview Q&A:** *"How do you make a Python project reproducible?"*
  → A virtual environment for isolation, pinned versions in `requirements.txt`, and the venv kept out of Git. Anyone can rebuild with `pip install -r requirements.txt`.

---