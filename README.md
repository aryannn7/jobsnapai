# Jobsnapai
# JobSnapAI — Explainable AI Career Intelligence Platform

**Live Demo:** https://jobsnapai-mvp-project.streamlit.app/  
**Tech Stack:** Python, Streamlit, OpenAI API, Modular Rule-Based Engine

---

## Overview

**JobSnapAI** is an explainable AI career intelligence system that analyzes resumes against job descriptions or target roles, identifies evidence-backed skill gaps, and recommends a single high-impact next learning action.

Unlike black-box resume screeners, JobSnapAI combines **deterministic skill extraction** with **optional large language model reasoning** to deliver transparent, actionable, and decision-focused guidance.

The system is designed to help candidates focus on *what actually moves the needle* for their target role — without overwhelm.

---

## Key Features

### Deterministic Resume & Job Analysis
- Parses PDF and DOCX resumes
- Extracts skills using rule-based matching with aliases
- Maps **evidence-backed resume snippets** to each detected skill
- Computes match percentage using transparent logic (no hidden scoring)

### Decision-First Recommendation Engine
- Identifies skill gaps based on job or role requirements
- Recommends **one high-impact “next learning action”**
- Optimized for focus, not exhaustive to-do lists

### AI Reasoning Layer (GPT-4)
When enabled, AI augments — but does not replace — deterministic logic:
- Role reality checks (what the role actually expects)
- Explanation of why a specific skill is blocking progress
- Structured 7-day learning plans for the selected focus skill

> AI is strictly optional. The system remains fully functional without it.

### Resume Health & Role Readiness
- Resume quality scoring with improvement tips
- Role-specific readiness analysis (e.g. Data Analyst, Data Engineer)
- Works **with or without a job description**

### Professional UX
- Minimal, decision-first interface
- Light theme by default (dark optional)
- Staged “thinking” analysis flow for clarity
- Evidence hidden behind expanders to reduce cognitive load

---

## Architecture & Design Principles

- **Explainability first:** Every recommendation is traceable to evidence
- **Deterministic core:** Rule-based extraction is the source of truth
- **AI as augmentation:** LLMs enhance reasoning, not scoring
- **Modular design:** Parsing, scoring, AI, UI, and progress tracking are isolated
- **Production hygiene:** Secrets managed securely, clean Git history

---

## Project Structure

jobsnapai/
├── app.py # Streamlit application entry point
├── core/
│ ├── parsing.py # Resume parsing (PDF/DOCX)
│ ├── cleaning.py # Text normalization
│ ├── skills.py # Skill taxonomy & aliases
│ ├── scoring.py # Deterministic matching logic
│ ├── next_move.py # Decision-first recommendation engine
│ ├── resume_health.py # Resume quality scoring
│ ├── role_paths.py # Role-based skill expectations
│ ├── ai_engine.py # Optional GPT-powered reasoning
│ ├── ui_theme.py # UI theming & CSS
│ └── progress.py # User progress tracking
├── requirements.txt
├── .streamlit/
│ └── config.toml # Streamlit configuration (theme)
└── README.md


---

## System Flow (High Level)

1. Resume uploaded (PDF/DOCX)
2. Text parsed and normalized
3. Skills extracted deterministically with aliases
4. Evidence snippets mapped to each skill
5. Job or role requirements compared
6. Match percentage computed
7. Missing skills ranked
8. One next high-impact action selected
9. Optional AI reasoning layered on top


## Deployment

The application is deployed using **Streamlit Community Cloud**.

Secrets (e.g. OpenAI API keys) are handled via Streamlit Secrets and are **not committed to Git**.

---

## Use Cases

- Job seekers targeting data, analytics, or AI roles
- Candidates overwhelmed by generic resume feedback
- Professionals seeking focused upskilling guidance
- Recruiters evaluating explainable skill matching tools

---

## Future Enhancements

- Authentication & user profiles
- Shareable resume analysis reports (PDF)
- Job scraping & auto-ingested job descriptions
- Analytics dashboard for user learning trends
- Subscription-based SaaS model

---

## Author

**Aryan Dhawan**  
AI / Data / Analytics  
Built as a personal project to explore explainable AI, decision systems, and production-ready tooling.

---

## License

This project is released for educational and demonstration purposes.


