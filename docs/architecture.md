# FinGenie – Fullstack Architecture Document

## 1. System Overview

The FinGenie MVP is a web-based financial assistant for monthly management reporting. It ingests static P&L, balance sheet, and KPI data via CSV or Excel uploads, then generates charts, commentary, and simple forecasts using AI. The system includes a live chat interface for user interaction, question routing, and iterative updates to outputs.

The core system components are:
- **Frontend (Streamlit)** – user interface for uploading data, viewing reports, chatting with the AI assistant, and reviewing outputs.
- **Backend (Python services)** – handles file parsing, data prep, prompt orchestration, chart generation, and session state.
- **AI Layer (OpenAI GPT-4o)** – generates financial commentary, answers user questions, and manages follow-up workflows.
- **Visualization Engine** – Seaborn for simple visuals, Plotly for complex financial charts.
- **Session Storage** – in-memory or lightweight disk cache (no persistent DB in MVP).
- **Authentication** – handled via Streamlit Auth (basic password-based access).

## 2. Data Flow

1. **User Uploads Data**: CSV or Excel file is uploaded through the Streamlit interface.
2. **Preprocessing**: Backend Python service parses and validates data (pandas, openpyxl).
3. **AI Prompting**: Structured data is passed to GPT-4o with preset prompts for commentary and analysis.
4. **Visualization**:
   - GPT generates Python code for Seaborn or Plotly
   - Backend executes code and returns rendered visuals
5. **Assembly**:
   - Commentary and visuals are combined into a live report view
   - Responses and commentary are cached in-memory per session
6. **User Interaction**:
   - Users engage via chat to explore data or ask follow-ups
   - Q&A Agent identifies if human input is needed and logs unanswered questions

## 3. Component Breakdown

### Frontend (Streamlit)
- File upload widget
- Multi-tab layout: Data Preview, Insights, Visuals, Forecast
- Embedded chat component
- Button triggers: regenerate chart, clarify answer, request forecast

### Backend (Python)
- FastAPI-style internal structure within Streamlit app
- Data handling: pandas for tabular ops, numpy for math
- LLM interface: OpenAI API, caching layer for repeat prompts
- Chart runner: executes GPT-generated code in controlled scope

### AI Layer (GPT-4o)
- Commentary generation prompt (management pack tone)
- Chart code generation prompt (Seaborn + Plotly context)
- Q&A engine prompt with logic routing (SQL generation optional)
- Prompt tuning happens outside runtime (via prompt library)

### Visualization Engine
- **Seaborn** for basic trends, bar/line graphs, grouped data
- **Plotly** for waterfalls, bridges, drilldowns, conditional formatting
- Execution sandboxed to protect against prompt injection in Python code

### Session Storage
- No DB used in MVP
- Data, charts, and chat history cached in session memory
- Option to extend to Redis or SQLite for session persistence if needed

### Authentication
- Streamlit Auth for login (username/password only)
- Admin-defined list of allowed users

## 4. Deployment & Ops

- Hosted via Streamlit Cloud or containerized for AWS deployment
- All secrets (OpenAI key) stored securely in environment variables
- Logging to local file or stdout
- Rate limits added to OpenAI calls to control cost

## 5. Future-State Additions (Post-MVP)

- DB layer (PostgreSQL or DynamoDB) for persistent storage
- ETL pipelines for Xero, SAP, MYOB integrations
- Role-based access and workflow approvals
- Auto-export to PowerPoint/Excel with embedded sources
- AI memory tuning per user/client
- Forecasting from multiple sources (divisional inputs)

## 6. Known Limitations (MVP)

- No persistent state across sessions
- No inline edit or visual annotations
- No automatic formatting for branded reports
- Limited protection against malformed input data
- Basic access control only

---

End of architecture draft.
