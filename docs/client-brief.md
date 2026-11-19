# CloudDrip 💧 Client Brief

> **Note:** This is a portfolio project. The client below is **fictional**; the data sources and industry figures are real.

## 1. Client
**Harbourline Insurance (fictional)**, a mid-sized UK insurer with around 800 staff.
It runs most of its IT on **Microsoft Azure** (claims systems, data platform, internal apps).

## 2. The problem
- **Cloud bills keep rising**, and nobody can clearly say why. Monthly Azure spend is roughly **£40,000** (illustrative).
- Resources are often **left running** after projects end, and many have **no owner tag**.
- The industry average is high: the **Flexera 2026 State of the Cloud Report** estimates **29% of IaaS/PaaS cloud spend is wasted**.
- The board has also asked IT to **report its carbon footprint**, but there is no data on the CO₂ impact of cloud usage.

## 3. What the client wants (objectives)
1. **See** where Azure money goes: by service, team, region and over time.
2. **Find waste**: idle, oversized or untagged resources (the "drips" 💧).
3. **Estimate CO₂** from cloud usage using real UK grid carbon data.
4. **Act**: get 3–5 clear recommendations, each with **£ saved per month** and **CO₂ reduced**.

## 4. Key questions to answer
- What are the **top 5 cost drivers**?
- How much spend is **likely waste**, and where is it?
- Which resources have **no owner or project tag**?
- When and where is the **UK grid cleanest**, so flexible jobs can run then?
- What would we save, in **£ and CO₂**, if we fixed the biggest drips?

## 5. Data sources
| Source | What it gives | Type |
|---|---|---|
| Azure Retail Prices API | Official Azure prices by service and region | Real, public API |
| UK Carbon Intensity API (National Grid ESO) | Grid CO₂ intensity by region, every 30 minutes | Real, public API |
| FOCUS-format billing data | Cloud billing records in the industry-standard FOCUS format | Sample/synthetic, realistic |

## 6. Scope
**In scope:** daily data pipeline, cleaned data model, waste and carbon analysis, Power BI dashboard, findings report.
**Out of scope:** automatically switching resources off, other clouds (AWS/GCP), live access to the client's real billing account.

## 7. Deliverables
1. Automated daily pipeline (Python + Azure Data Factory)
2. Data lake with Bronze / Silver / Gold layers (ADLS Gen2)
3. Star-schema data model with a data quality log (Azure SQL)
4. Power BI dashboard (3 pages): **Executive summary**, **Waste finder**, **Region & carbon advisor**
5. Findings report with **3–5 recommendations** (£ and CO₂)
6. README case study and architecture diagram

## 8. Success criteria
- Pipeline runs daily **without manual steps**
- Data quality checks pass and failures are **logged**
- Dashboard answers all 5 key questions
- Each recommendation shows a **£ saving** and a **CO₂ reduction**

## 9. Constraints
- **Budget:** £0. Free Azure credit only, with a £5 budget alert.
- **Deadline:** Azure work completed before **4 December 2026**.
- **Region:** UK South (UK data stays in the UK).
- **Security:** no secrets in GitHub; credentials kept in `.env` (git-ignored).