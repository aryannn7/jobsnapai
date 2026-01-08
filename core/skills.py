"""
core/skills.py

Skill taxonomy for deterministic extraction.

We expose:
- SKILL_ALIASES: dict mapping canonical skill -> list of aliases/synonyms

Design:
- Canonical names are what the UI shows.
- Aliases include common spellings and abbreviations.
"""

from __future__ import annotations

from typing import Dict, List


SKILL_ALIASES: Dict[str, List[str]] = {
    # -------------------------
    # Programming & Data
    # -------------------------
    "Python": ["Python"],
    "Structured Query Language": ["SQL", "Structured Query Language"],
    "R": ["R", "R Studio", "RStudio"],
    "Scala": ["Scala"],
    "Pandas": ["Pandas"],
    "NumPy": ["NumPy", "Numpy"],
    "PySpark": ["PySpark", "Py Spark"],
    "Apache Spark": ["Apache Spark", "Spark"],
    "Data Analysis": ["Data Analysis", "Data Analytics"],
    "Data Engineering": ["Data Engineering", "Data Engineer"],
    "Data Modeling": ["Data Modeling", "Data Modelling"],
    "ETL Pipelines": ["ETL", "ETL Pipelines", "Extract Transform Load"],
    "Statistical Modeling": ["Statistical Modeling", "Statistical Modelling"],
    "Statistics": ["Statistics", "Statistical Analysis"],

    # -------------------------
    # Machine Learning / AI
    # -------------------------
    "Machine Learning": ["Machine Learning", "ML"],
    "Artificial Intelligence": ["Artificial Intelligence", "AI"],
    "Natural Language Processing": ["Natural Language Processing", "NLP"],
    "TensorFlow": ["TensorFlow", "Tensor Flow"],
    "PyTorch": ["PyTorch", "Pytorch"],
    "XGBoost": ["XGBoost", "XG Boost"],
    "Scikit-learn": ["Scikit-learn", "Scikit Learn", "sklearn"],

    # -------------------------
    # Cloud / Data Platforms
    # -------------------------
    "Azure": ["Azure", "Microsoft Azure"],
    "Azure Data Factory": ["Azure Data Factory", "ADF"],
    "Databricks": ["Databricks"],
    "Cosmos DB": ["Cosmos DB", "CosmosDB", "Azure Cosmos DB"],
    "Data Lakes": ["Data Lake", "Data Lakes", "Datalake", "DataLake"],

    # -------------------------
    # Databases
    # -------------------------
    "PostgreSQL": ["PostgreSQL", "Postgres"],
    "MySQL": ["MySQL"],

    # -------------------------
    # DevOps / Tools
    # -------------------------
    "Git": ["Git"],
    "GitHub": ["GitHub", "Github"],
    "Docker": ["Docker"],
    "Azure DevOps": ["Azure DevOps", "Azure DevOps Services", "ADO"],

    # -------------------------
    # BI / Visualization
    # -------------------------
    "Power BI": ["Power BI", "PowerBI"],
    "Tableau": ["Tableau"],
    "Data Visualization": ["Data Visualization", "Data Visualisation"],

    # -------------------------
    # Documents / Parsing (if mentioned)
    # -------------------------
    "Streamlit": ["Streamlit"],
    "PyMuPDF": ["PyMuPDF", "fitz"],
    "BeautifulSoup": ["BeautifulSoup", "Beautiful Soup"],
}