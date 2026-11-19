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

---## Phase 1: Azure setup (19 Nov 2026)

### 1.1 Checked the existing Azure account
- **What:** Used my existing Azure free account (£150 credit, expires 4 Dec 2026) and confirmed no leftover resources were running.
- **Why:** Leftover resources quietly use credit, so the first job is always "what's already running?"
- **Interview Q&A:** *"What's the first thing you check in a cloud account?"*
  → What's already running and what it costs, before building anything new.

### 1.2 Created a £5 budget alert
- **What:** Created `clouddrip-budget` (£5/month) on the subscription, with alerts at 50% and 100% actual spend and 100% forecasted spend.
- **Why:** To get an early warning before costs grow. Budgets send alerts; they don't stop spending.
- **Interview Q&A:** *"Does an Azure budget stop resources when it's exceeded?"*
  → No. A budget only sends alerts. To stop spend you need actions like automation or the free account's spending limit.

### 1.3 Created a tagged resource group
- **What:** Created `rg-clouddrip-dev` in UK South with tags `project`, `owner` and `environment`.
- **Why:** One folder for all project resources: easy cost tracking, and one-click clean-up at the end. UK South keeps UK data in the UK.
- **Interview Q&A:** *"Why are tags important in FinOps?"*
  → Tags show who owns each resource and which project it belongs to, so costs can be tracked and untagged waste can be found.

---## Phase 2: Client brief (19 Nov 2026)
- **What:** Wrote a one-page client brief for a fictional UK insurer: problem, objectives, key questions, data sources, scope, deliverables and success criteria.
- **Why:** Real data projects start by agreeing the business problem, so the work answers the right questions and has clear "done" criteria.
- **Interview Q&A:** *"How do you start a new data project?"*
  → I agree the business problem and the key questions with stakeholders first, then define scope, data sources and success criteria before building anything.
## Phase 3.1 – Carbon intensity data 🌍 (19 Nov 2026)

**What I did**
Today I wrote my first ingestion script, `carbon_intensity.py`.
It calls the National Grid Carbon Intensity API and gets the last 24 hours
of data for all UK regions. That's 48 half-hour slots. Then it saves the raw
JSON file in `data/bronze/carbon_intensity/` inside a folder with today's date.

**Why I did it this way**
Bronze is like keeping the original receipt 🧾. I don't change anything in it.
If I make a mistake later when cleaning the data, I can just go back to
these files. No need to call the API again.

**My decision**
I chose to save the files on my laptop first, not straight into Azure.
It felt like the safer option instead of going to Azure and getting stuck
in the middle. So I started with the easier one. I'll move it to Azure
storage in Phase 6.

**Problems I faced (and how I fixed them) 🛠️**
- I typed the terminal prompt itself as a command 😅 and got
  `zsh: parse error`. Now I know the prompt is just the terminal saying
  "I'm ready". Also, I have to turn on `.venv` every time I open a new terminal.
- I ran the script before saving it and got `No such file or directory`.
  The white dot ● on the tab means the file isn't saved yet. Cmd + S first!
- I got `IndentationError: unexpected indent` because I put extra spaces
  on one line. In Python, spaces really matter. The red squiggle line
  warns you before you even run it.

**Something interesting I noticed 💡**
At 2am, North Scotland's carbon intensity was 0, because it was mostly wind
and hydro power. So where and when you run something really does change
the CO₂.

**Interview Q&A 🎤**
Q: Why didn't you clean the data as soon as you downloaded it?
A: I keep the raw data as it is in Bronze, so I can always go back to it
and check where any number came from. Cleaning happens in the next step,
Silver.