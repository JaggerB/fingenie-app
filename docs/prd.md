
# Product Requirements Document (PRD)

**Product Name:** FinGenie – AI-Powered Monthly Management Reporting Assistant

---

## 1. Overview & Goals

**Overview:**  
FinGenie helps finance teams automate monthly management reporting using static uploads of financial data. It transforms raw P&L, balance sheet, and KPI files into executive-ready visuals and insights. It also supports financial Q&A, follow-ups, and lightweight forecasting—all accessible through a chat interface.

**Phase 1 Goal:**  
Build a proof-of-concept that ingests static data (CSV/Excel), generates charts and commentary, flags key movements using hardcoded thresholds, and allows Q&A interactions. This version focuses on live review within the app—exporting to PowerPoint or Excel is out of scope.

**Objectives:**
- Reduce hours spent on manual reporting prep
- Improve the clarity and consistency of insights delivered to execs
- Enable faster follow-up on questions and anomalies
- Set foundation for interactive, AI-assisted finance automation

---

## 2. Target Users

**Primary User: Finance Analyst / Manager**  
- Uploads data, reviews output, interacts with chat interface

**Secondary User: CFO / Executive**  
- Reviews insights, asks questions, triggers deeper analysis

**Tertiary User: Divisional Lead**  
- Responds to routed questions, provides assumptions for forecasts

---

## 3. Core Features

### Data Upload & Ingestion
- Static CSV/XLS upload
- Basic column validation/mapping

### Insight Generation
- Hardcoded thresholds to flag movements/anomalies
- Commentary generation for key changes

### Visual Output (In-App Only)
- Charts: trend, YoY, MoM, waterfall
- Visual + commentary pairs rendered live
- Regeneration via chat

### Q&A Interface
- Natural language chat with stored history
- Auto-drafted responses or routing to humans
- Logged answer repository

### Forecasting Lite
- Manual assumption input
- Line-level forward projections
- Trend variance logic (simple)

---

## 4. UX Expectations

- Streamlit-based interface for management insights
- Embedded chat for Q&A and edit requests
- Realtime visual update loop from GPT to chart engine
- Seaborn for simple visuals, Plotly for detailed charts
- Forecast inputs handled through manual entry fields
- No export or version control in Phase 1

---

## 5. Success Metrics

- 3–5 successful client test runs
- ≥50% reduction in reporting prep time (directional)
- 70%+ of chat queries return useful responses
- Forecast module used by ≥1 team to guide planning
- 2+ teams request early access to Phase 2

---

## 6. Non-Functional Requirements

- Charts and commentary load within 60s of data upload
- Q&A responds in <10s on average
- Data stored in-session only (no DB)
- Basic login (Streamlit Auth)
- No SSO, no persistent user state

---

## 7. Out of Scope

- Live integrations (Xero, SAP, etc.)
- Exports with source references
- Role-based access and approval flows
- Advanced forecast modeling
- Knowledge center or persistent GPT memory

---

## 8. Dependencies & Constraints

- GPT-4o for commentary/Q&A
- Seaborn + Plotly for charts
- Streamlit for front-end
- pandas/openpyxl for file processing
- No backend DB, no export engine
- Limited dev bandwidth
