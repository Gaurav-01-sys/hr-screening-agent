"""
Shared test data helpers — sample resume & JD text used when file upload
is not being tested.
"""
SAMPLE_RESUME_TEXT = """
John Doe
Senior Data Analyst | john.doe@email.com | +1-555-0100

PROFESSIONAL EXPERIENCE

Data Analyst — RetailCo Inc.  (Jan 2021 – Present, 28 months)
  • Built executive dashboards in Tableau, visualising £50M+ revenue trends.
  • Wrote complex SQL queries (PostgreSQL) for inventory and margin analysis.
  • Automated ETL pipelines in Python (pandas, SQLAlchemy).

Junior Analyst — ShopMetrics Ltd.  (Jan 2019 – Dec 2020, 24 months)
  • Maintained weekly Excel/Power BI reports for category managers.
  • Supported SQL data extraction from MSSQL for supplier performance packs.

SKILLS
Tableau: 28 months | SQL / PostgreSQL / MSSQL: 52 months
Python: 28 months | Power BI: 24 months | Excel: 52 months

Total professional experience: approximately 52 months (4+ years)
""".strip()

SAMPLE_JD_TEXT = """
Job Title: Business Intelligence Analyst

About the Role:
We are looking for an experienced BI Analyst to join our retail analytics team.

Responsibilities:
- Design and maintain Tableau dashboards for senior stakeholders.
- Write performant SQL queries against large data warehouses.
- Collaborate with data engineers on ETL pipelines.

Requirements:
- Minimum 3 years (36 months) of total experience.
- Proficient in Tableau (minimum 24 months).
- Strong SQL skills (any variant: PostgreSQL, MSSQL, MySQL).
- Python experience preferred.
- Retail or e-commerce domain experience preferred.
""".strip()

SAMPLE_RULE_NOTES = (
    "Tableau experience must be at least 24 months (2 years). "
    "SQL is mandatory. "
    "Total experience must be at least 36 months."
)
