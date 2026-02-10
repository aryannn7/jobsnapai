"""
core/skills.py

Deterministic skill taxonomy for extraction.

We expose:
- SKILL_ALIASES: canonical -> list of aliases/synonyms (strings)
Optional metadata:
- SKILL_CATEGORY: canonical -> category string
- SKILL_PRIORITY: canonical -> int weight (higher = more important)

Design principles:
- Canonical names are what the UI shows.
- Aliases include common spellings, abbreviations, recruiter keywords.
- Avoid overly generic aliases that cause false positives (e.g., "R", "BA").
- Prefer multi-word aliases ("Business Analyst") over ambiguous acronyms ("BA").
"""

from __future__ import annotations

from typing import Dict, List

# -------------------------
# Canonical -> aliases
# -------------------------
SKILL_ALIASES: Dict[str, List[str]] = {
    # =========================
    # Core Data / Programming
    # =========================
    "Python": ["Python"],
    "SQL": ["SQL", "Structured Query Language"],
    # Keep R conservative to reduce false positives from letters/grades.
    "R": ["RStudio", "R Studio"],

    "Pandas": ["Pandas"],
    "NumPy": ["NumPy", "Numpy"],

    "PySpark": ["PySpark", "Py Spark"],
    "Apache Spark": ["Apache Spark", "Spark"],

    "Data Analysis": ["Data Analysis", "Data Analytics"],
    "Data Engineering": ["Data Engineering", "Data Engineer"],
    "Data Modeling": ["Data Modeling", "Data Modelling", "Dimensional Modeling", "Star Schema", "Snowflake Schema"],
    "ETL": ["ETL", "ETL Pipelines", "Extract Transform Load"],
    "Statistics": ["Statistics", "Statistical Analysis"],
    "Statistical Modeling": ["Statistical Modeling", "Statistical Modelling"],

    # =========================
    # Machine Learning / AI
    # =========================
    "Machine Learning": ["Machine Learning", "ML"],
    "Artificial Intelligence": ["Artificial Intelligence", "AI"],
    "NLP": ["Natural Language Processing", "NLP"],

    "Scikit-learn": ["Scikit-learn", "Scikit Learn", "sklearn"],
    "TensorFlow": ["TensorFlow", "Tensor Flow"],
    "PyTorch": ["PyTorch", "Pytorch"],
    "XGBoost": ["XGBoost", "XG Boost"],

    # =========================
    # Cloud / Data Platforms
    # =========================
    "Azure": ["Azure", "Microsoft Azure"],
    "Azure Data Factory": ["Azure Data Factory", "ADF"],
    "Databricks": ["Databricks"],
    "Cosmos DB": ["Cosmos DB", "CosmosDB", "Azure Cosmos DB"],
    "Data Lakes": ["Data Lake", "Data Lakes", "Datalake", "DataLake"],

    # =========================
    # Databases
    # =========================
    "PostgreSQL": ["PostgreSQL", "Postgres"],
    "MySQL": ["MySQL"],

    # =========================
    # DevOps / Tools
    # =========================
    "Git": ["Git"],
    "GitHub": ["GitHub", "Github"],
    "Docker": ["Docker"],
    "Azure DevOps": ["Azure DevOps", "Azure DevOps Services", "ADO"],

    # =========================
    # BI / Visualization
    # =========================
    "Excel": ["Excel", "Microsoft Excel", "Advanced Excel", "Pivot Tables", "PivotTable", "VLOOKUP", "XLOOKUP"],
    "Power BI": ["Power BI", "PowerBI"],
    "Tableau": ["Tableau"],
    "Data Visualization": ["Data Visualization", "Data Visualisation", "Dashboards", "Dashboarding"],

    # =========================
    # Business Analyst / Product / Process
    # (This is what fixes your BA match scores)
    # =========================
    "Business Analysis": ["Business Analysis", "Business Analyst"],
    "Requirements Gathering": [
        "Requirements Gathering",
        "Requirement Gathering",
        "Requirements Elicitation",
        "Requirement Elicitation",
        "Stakeholder Requirements",
    ],
    "Stakeholder Management": [
        "Stakeholder Management",
        "Stakeholder Communication",
        "Stakeholder Engagement",
        "Stakeholder Communications",
    ],
    "Communication": [
        "Communication",
        "Presentation",
        "Presentations",
        "Client Communication",
        "Written Communication",
        "Verbal Communication",
    ],
    "Agile": ["Agile", "Scrum", "Kanban"],
    "User Stories": ["User Stories", "User Story", "Acceptance Criteria"],
    "UAT": ["UAT", "User Acceptance Testing"],
    "Process Mapping": ["Process Mapping", "Process Map", "Process Flow", "Process Flows", "Workflow"],
    "BPMN": ["BPMN", "Business Process Model and Notation"],
    "Process Improvement": ["Process Improvement", "Process Optimization", "Process Optimisation"],
    "Documentation": ["Documentation", "BRD", "PRD", "FRD", "Functional Requirements", "Non-Functional Requirements"],
    "Jira": ["Jira", "JIRA"],
    "Confluence": ["Confluence"],

    # =========================
    # Product / Parsing mentions
    # =========================
    "Streamlit": ["Streamlit"],
    "PyMuPDF": ["PyMuPDF", "fitz"],
    "BeautifulSoup": ["BeautifulSoup", "Beautiful Soup"],
}

# -------------------------
# Optional metadata
# -------------------------
SKILL_CATEGORY: Dict[str, str] = {
    # Programming / Data
    "Python": "Programming",
    "SQL": "Programming",
    "R": "Programming",
    "Pandas": "Programming",
    "NumPy": "Programming",
    "PySpark": "Data Engineering",
    "Apache Spark": "Data Engineering",
    "Data Analysis": "Analytics",
    "Data Engineering": "Data Engineering",
    "Data Modeling": "Data Engineering",
    "ETL": "Data Engineering",
    "Statistics": "Analytics",
    "Statistical Modeling": "Analytics",

    # ML/AI
    "Machine Learning": "ML/AI",
    "Artificial Intelligence": "ML/AI",
    "NLP": "ML/AI",
    "Scikit-learn": "ML/AI",
    "TensorFlow": "ML/AI",
    "PyTorch": "ML/AI",
    "XGBoost": "ML/AI",

    # Cloud
    "Azure": "Cloud",
    "Azure Data Factory": "Cloud",
    "Databricks": "Cloud",
    "Cosmos DB": "Cloud",
    "Data Lakes": "Cloud",

    # Databases
    "PostgreSQL": "Databases",
    "MySQL": "Databases",

    # DevOps
    "Git": "DevOps",
    "GitHub": "DevOps",
    "Docker": "DevOps",
    "Azure DevOps": "DevOps",

    # BI
    "Excel": "BI/Analytics",
    "Power BI": "BI",
    "Tableau": "BI",
    "Data Visualization": "BI",

    # BA / Product
    "Business Analysis": "Business",
    "Requirements Gathering": "Business",
    "Stakeholder Management": "Business",
    "Communication": "Business",
    "Agile": "Delivery",
    "User Stories": "Delivery",
    "UAT": "Delivery",
    "Process Mapping": "Business",
    "BPMN": "Business",
    "Process Improvement": "Business",
    "Documentation": "Business",
    "Jira": "Tools",
    "Confluence": "Tools",

    # Product mentions
    "Streamlit": "Product",
    "PyMuPDF": "Product",
    "BeautifulSoup": "Product",
}

# Higher = more important in screening
SKILL_PRIORITY: Dict[str, int] = {
    # Core
    "SQL": 5,
    "Python": 5,
    "Excel": 5,  # critical for BA / analyst screening
    "Power BI": 4,
    "Tableau": 4,

    # Engineering
    "ETL": 4,
    "Data Modeling": 4,
    "Git": 4,

    # BA
    "Requirements Gathering": 5,
    "Stakeholder Management": 5,
    "Communication": 4,
    "Agile": 4,
    "User Stories": 4,
    "UAT": 3,
    "Process Mapping": 3,
    "Process Improvement": 3,
    "Documentation": 3,
    "Jira": 2,
    "Confluence": 2,

    # Cloud/Platforms
    "Azure": 3,
    "Databricks": 3,
    "Apache Spark": 3,
    "PySpark": 3,
    "Azure Data Factory": 3,

    # Analytics/ML
    "Statistics": 3,
    "Machine Learning": 3,
    "Scikit-learn": 3,

    # Lower priority
    "Docker": 2,
    "PostgreSQL": 2,
    "MySQL": 2,
    "NLP": 2,
    "TensorFlow": 2,
    "PyTorch": 2,
    "XGBoost": 2,

    "Streamlit": 1,
    "PyMuPDF": 1,
    "BeautifulSoup": 1,
}
