from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parent


def build_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCustom",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0F172A"),
            alignment=TA_LEFT,
            spaceAfter=12,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#475569"),
            spaceAfter=3,
        ),
        "h2": ParagraphStyle(
            "H2Custom",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=16,
            textColor=colors.HexColor("#1D4ED8"),
            spaceBefore=10,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "H3Custom",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "BodyCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#111827"),
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "BulletCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.2,
            leading=13.5,
            leftIndent=2,
            textColor=colors.HexColor("#111827"),
        ),
    }


def add_bullets(story, items, style):
    flowable = ListFlowable(
        [ListItem(Paragraph(item, style)) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=18,
        bulletFontName="Helvetica",
        bulletFontSize=9,
    )
    story.append(flowable)
    story.append(Spacer(1, 0.1 * inch))


def build_cv(path: Path):
    s = build_styles()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        title="Sample CV - Riya Sharma",
        author="OpenAI Codex",
    )
    story = []

    story.append(Paragraph("Riya Sharma", s["title"]))
    story.append(Paragraph("Bengaluru, India | riya.sharma@example.com | +91-90000-00000", s["meta"]))
    story.append(Paragraph("linkedin.com/in/riya-sharma", s["meta"]))
    story.append(Spacer(1, 0.08 * inch))

    story.append(Paragraph("Professional Summary", s["h2"]))
    story.append(
        Paragraph(
            "Data Analyst with 3+ years of experience in BI reporting, SQL analytics, dashboard development, "
            "and stakeholder communication. Strong experience with SQL, Tableau, Excel, and Python for "
            "reporting automation and business insight generation. Worked with retail and ecommerce datasets "
            "to track sales, conversion, inventory, and customer performance.",
            s["body"],
        )
    )

    story.append(Paragraph("Core Skills", s["h2"]))
    add_bullets(
        story,
        [
            "SQL",
            "Tableau",
            "Python",
            "Excel",
            "Power BI",
            "Data Cleaning",
            "Dashboard Design",
            "KPI Reporting",
            "Business Analysis",
            "Retail Analytics",
        ],
        s["bullet"],
    )

    story.append(Paragraph("Work Experience", s["h2"]))
    story.append(Paragraph("Data Analyst | BrightCart Retail Pvt Ltd", s["h3"]))
    story.append(Paragraph("July 2023 - Present | Bengaluru, India", s["meta"]))
    add_bullets(
        story,
        [
            "Built and maintained Tableau dashboards for weekly sales, returns, inventory aging, and regional performance.",
            "Created SQL queries and views for recurring KPI reporting used by category managers and finance teams.",
            "Automated monthly reporting workflows using Python and reduced manual reporting effort by 35%.",
            "Partnered with merchandising and operations teams to analyze retail performance across stores and online channels.",
            "Created exception reports to identify low-stock items and margin drops.",
        ],
        s["bullet"],
    )
    story.append(Paragraph("Evidence-style skill summary: Tableau 18 months, SQL 18 months, Python 12 months, Retail Analytics 18 months.", s["body"]))

    story.append(Paragraph("Junior Business Analyst | InsightGrid Solutions", s["h3"]))
    story.append(Paragraph("January 2022 - June 2023 | Bengaluru, India", s["meta"]))
    add_bullets(
        story,
        [
            "Supported analytics delivery for ecommerce and customer reporting projects.",
            "Prepared SQL-based reports for campaign performance and customer segmentation.",
            "Built Power BI dashboards for internal stakeholders and account managers.",
            "Assisted with requirement gathering, metric definitions, and ad hoc data analysis.",
        ],
        s["bullet"],
    )
    story.append(Paragraph("Evidence-style skill summary: SQL 18 months, Power BI 12 months, Excel 18 months, Ecommerce Analytics 18 months.", s["body"]))

    story.append(Paragraph("Education", s["h2"]))
    story.append(Paragraph("Bachelor of Technology in Information Science | PES University | 2018 - 2022", s["body"]))

    story.append(Paragraph("Certifications", s["h2"]))
    add_bullets(
        story,
        [
            "Tableau Desktop Specialist",
            "SQL for Data Analytics Certification",
        ],
        s["bullet"],
    )

    story.append(Paragraph("Selected Project Highlights", s["h2"]))
    story.append(Paragraph("Sales Performance Dashboard", s["h3"]))
    add_bullets(
        story,
        [
            "Developed a Tableau dashboard combining store sales, discounts, and returns data.",
            "Helped business users identify underperforming categories and improve weekly review quality.",
        ],
        s["bullet"],
    )
    story.append(Paragraph("Reporting Automation", s["h3"]))
    add_bullets(
        story,
        [
            "Wrote Python scripts and SQL queries to automate recurring Excel-based reporting packs.",
            "Reduced analyst turnaround time from one day to two hours.",
        ],
        s["bullet"],
    )

    story.append(Paragraph("Additional Information", s["h2"]))
    add_bullets(
        story,
        [
            "Total professional experience: approximately 36 months",
            "Notice period: 30 days",
            "Current role focus: BI dashboards, SQL reporting, retail analytics",
        ],
        s["bullet"],
    )

    doc.build(story)


def build_jd(path: Path):
    s = build_styles()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        title="Sample Job Description - Business Intelligence Analyst",
        author="OpenAI Codex",
    )
    story = []

    story.append(Paragraph("Business Intelligence Analyst", s["title"]))
    story.append(Paragraph("Location: Bengaluru, India", s["meta"]))

    story.append(Paragraph("Role Summary", s["h2"]))
    story.append(
        Paragraph(
            "We are hiring a Business Intelligence Analyst to support retail reporting, dashboard development, "
            "and business performance analysis. The candidate will work with stakeholders across merchandising, "
            "sales, finance, and operations to build dashboards, monitor KPIs, and convert raw data into "
            "actionable business insights.",
            s["body"],
        )
    )

    story.append(Paragraph("Required Qualifications", s["h2"]))
    add_bullets(
        story,
        [
            "2+ years of total analytics or BI experience.",
            "Strong SQL skills for querying, joins, aggregations, and reporting logic.",
            "Hands-on Tableau experience for dashboard development and maintenance.",
            "Experience working with retail or consumer business data.",
            "Strong communication and stakeholder management skills.",
        ],
        s["bullet"],
    )

    story.append(Paragraph("Mandatory Requirements", s["h2"]))
    add_bullets(
        story,
        [
            "SQL is mandatory.",
            "Tableau is mandatory.",
            "Minimum 24 months of Tableau experience is required.",
            "Minimum 24 months of total professional experience is required.",
            "Candidate must have experience in retail analytics or retail reporting.",
        ],
        s["bullet"],
    )

    story.append(Paragraph("Preferred Qualifications", s["h2"]))
    add_bullets(
        story,
        [
            "Experience with Python for automation or analysis.",
            "Experience with Power BI.",
            "Familiarity with inventory, sales, and margin reporting.",
            "Ability to translate business questions into KPI dashboards.",
        ],
        s["bullet"],
    )

    story.append(Paragraph("Key Responsibilities", s["h2"]))
    add_bullets(
        story,
        [
            "Design and maintain Tableau dashboards for business and operations teams.",
            "Write optimized SQL queries for recurring and ad hoc reporting.",
            "Analyze sales, returns, inventory, and category trends.",
            "Partner with business stakeholders to define metrics and reporting views.",
            "Support monthly and weekly review cadences with timely insight generation.",
        ],
        s["bullet"],
    )

    story.append(Paragraph("Evaluation Notes", s["h2"]))
    add_bullets(
        story,
        [
            "Strong evidence of SQL ownership in recent roles.",
            "Clear dashboard-building experience in Tableau.",
            "At least 24 months of Tableau usage.",
            "Exposure to retail domain data.",
            "Ability to explain business impact from analytics work.",
        ],
        s["bullet"],
    )

    doc.build(story)


if __name__ == "__main__":
    build_cv(ROOT / "sample_cv.pdf")
    build_jd(ROOT / "sample_jd.pdf")
    print("Generated sample_cv.pdf and sample_jd.pdf")
