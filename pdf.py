from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm, cm, inch
from schemas import Resume
from reportlab.pdfbase.pdfmetrics import registerFont, registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont


registerFont(TTFont("CenturyGothic", "fonts/centurygothic.ttf"))
registerFont(TTFont("CenturyGothic-Bold", "fonts/centurygothic_bold.ttf"))

registerFontFamily(
    "Century Gothic",
    normal="CenturyGothic",
    bold="CenturyGothic-Bold",
    italic="CenturyGothic",
    boldItalic="CenturyGothic-Bold",
)


def create_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Body",
        parent=styles["BodyText"],
        fontName="CenturyGothic",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#888888"),
    ))
    styles.add(ParagraphStyle(
        name="BodyWithoutSpaces",
        parent=styles["Body"],
        leading=11,
    ))
    styles.add(ParagraphStyle(
        name="Body2",
        parent=styles["Body"],
        textColor=colors.HexColor("#000"),
    ))
    styles.add(ParagraphStyle(
        name="H4",
        parent=styles["Body"],
        fontName="CenturyGothic-Bold",
        textColor=colors.HexColor("#686868"),
        spaceBefore=0.3 * cm,
        spaceAfter=0.4 * cm,
    ))
    styles.add(ParagraphStyle(
        name="H1Green",
        fontName="CenturyGothic-Bold",
        parent=styles["Body"],
        fontSize=31,
        leading=31,
        textColor=colors.HexColor("#2c806e"),
        spaceAfter=0.5 * cm,
    ))
    styles.add(ParagraphStyle(
        name="H2Green",
        parent=styles["H1Green"],
        fontSize=20,
        leading=20,
        spaceAfter=0.4 * cm,
    ))
    styles.add(ParagraphStyle(
        name="H3Green",
        parent=styles["H1Green"],
        fontSize=12,
        leading=12,
        spaceBefore=0.6 * cm,
        spaceAfter=0.4 * cm,
        textTransform="uppercase",
    ))
    return styles


def create_simple_styles():
    styles = getSampleStyleSheet()
    return styles


def build_resume(path: str, title: str, resume: Resume):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=1.48*cm, rightMargin=1.48*cm,
        topMargin=0.63*cm, bottomMargin=1.83*cm,
        title=title, author=resume.name
    )
    styles = create_styles()

    flow = []

    flow.append(Paragraph(resume.name, styles["H1Green"]))
    flow.append(Paragraph(resume.title, styles["H2Green"]))
    flow.append(Paragraph(f"{resume.phone} | {resume.email} | {resume.address}", styles["Body"]))
    flow.append(Paragraph(" | ".join(f"{network_name}: {link}" for network_name, link in resume.websites.items()), styles["Body"]))
    flow.append(Paragraph(f"Work rights: {resume.work_rights}", styles["Body"]))

    flow.append(Paragraph("Personal summary", styles["H3Green"]))
    flow.append(Paragraph(resume.personal_summary, styles["Body"]))

    flow.append(Paragraph("Skills", styles["H3Green"]))
    for group, skills in resume.skills.items():
        flow.append(Paragraph(f"{group}: ", styles["H4"]))
        flow.append(ListFlowable(
            [ListItem(Paragraph(skill, styles["BodyWithoutSpaces"])) for skill in skills],
            bulletType="bullet",
            bulletFontName="CenturyGothic",
            bulletFontSize=10.5,
            leading=11,
            bulletColor=colors.HexColor("#888888"),
        ))

    flow.append(Paragraph("Professional Experience", styles["H3Green"]))
    for workplace in resume.career_history:
        flow.append(
            Paragraph(f"{workplace.position}, {workplace.company}, {workplace.dates} ({workplace.location})",
                      styles["H4"]))
        flow.append(ListFlowable(
            [ListItem(Paragraph(responsibility, styles["BodyWithoutSpaces"])) for responsibility in workplace.responsibilities],
            bulletType="bullet",
            bulletFontName="CenturyGothic",
            bulletFontSize=10.5,
            leading=11,
            bulletColor=colors.HexColor("#888888"),
        ))

    flow.append(Paragraph("Education & Certifications", styles["H3Green"]))
    for edu in resume.education:
        flow.append(
            Paragraph(
                f"<b>{edu.qualification}</b> - {edu.institution}, {edu.location} - {edu.dates}",
                styles["Body"]
            )
        )

    flow.append(Paragraph("Languages", styles["H3Green"]))
    flow.append(Paragraph(f"{'&nbsp;'*10}".join(f"- {lang}" for lang in resume.languages), styles["Body"]))

    flow.append(Paragraph("Hobbies and Interests", styles["H3Green"]))
    flow.append(Paragraph(f"{'&nbsp;'*10}".join(f"- {hobby}" for hobby in resume.hobbies_interests), styles["Body"]))

    doc.build(flow)


def build_new_resume(path: str, title: str, resume: Resume):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=1*inch, rightMargin=1*inch,
        topMargin=1*inch, bottomMargin=1*inch,
        title=title, author=resume.name
    )
    styles = create_simple_styles()

    flow = []

    flow.append(Paragraph(resume.name, styles["Title"]))
    websites = " | ".join(f"{network_name}: {link}" for network_name, link in resume.websites.items())
    flow.append(Paragraph(f"VIC | {resume.phone} | {resume.email} | {websites}", styles["BodyText"]))
    flow.append(Paragraph(f"Work rights: {resume.work_rights}", styles["BodyText"]))

    flow.append(Paragraph("PERSONAL SUMMARY", styles["Heading3"]))
    flow.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    flow.append(Paragraph(resume.personal_summary, styles["BodyText"]))

    flow.append(Paragraph("SKILLS", styles["Heading3"]))
    flow.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    skills_items = []
    for group, skills in resume.skills.items():
        skills_items.append(ListItem(Paragraph(f"<b>{group}:</b> {', '.join(skills)}", styles["BodyText"])))

    flow.append(ListFlowable(
        skills_items,
        bulletType="bullet",
        bulletFontName="CenturyGothic",
        bulletFontSize=10.5,
        leading=11,
        bulletColor=colors.HexColor("#888888"),
    ))

    flow.append(Paragraph("EDUCATION", styles["Heading3"]))
    flow.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    for edu in resume.education:
        flow.append(
            Paragraph(
                f"<b>{edu.qualification}</b> - {edu.institution}, {edu.location} - {edu.dates}",
                styles["BodyText"]
            )
        )

    flow.append(Paragraph("WORK EXPERIENCE", styles["Heading3"]))
    flow.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    for workplace in resume.career_history:
        flow.append(
            Paragraph(f"{workplace.position}, {workplace.company}, {workplace.dates} ({workplace.location})",
                      styles["Heading4"]))
        flow.append(ListFlowable(
            [ListItem(Paragraph(responsibility, styles["BodyText"])) for responsibility in workplace.responsibilities],
            bulletType="bullet",
            bulletFontName="CenturyGothic",
            bulletFontSize=10.5,
            leading=11,
            bulletColor=colors.HexColor("#888888"),
        ))

    flow.append(Paragraph("EXTRAS", styles["Heading3"]))
    flow.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    flow.append(Paragraph("Courses & Certifications", styles["Heading3"]))
    for cert in resume.certificates:
        flow.append(
            Paragraph(
                f"<b>{cert.qualification}</b> - {cert.institution}, {cert.location} - {cert.dates}",
                styles["BodyText"]
            )
        )

    flow.append(Paragraph("Languages", styles["Heading3"]))
    flow.append(Paragraph(f"{'&nbsp;'*10}".join(f"- {lang}" for lang in resume.languages), styles["BodyText"]))

    flow.append(Paragraph("Hobbies and Interests", styles["Heading3"]))
    flow.append(Paragraph(f"{'&nbsp;'*10}".join(f"- {hobby}" for hobby in resume.hobbies_interests), styles["BodyText"]))

    doc.build(flow)


def build_cover_letter(path: str, title: str, text: str, position: str, company_name: str, author: str = "Ivan Bazhenov"):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=1.48*cm, rightMargin=1.48*cm,
        topMargin=0.63*cm, bottomMargin=1.83*cm,
        title=title, author=author
    )
    styles = create_styles()
    flow = []
    flow.append(Paragraph(f"{position} - {company_name}", styles["Heading3"]))
    flow.extend([Paragraph(article, styles["BodyText"]) for article in text.split("\n")])
    flow.append(Paragraph("", styles["BodyText"]))
    flow.append(Paragraph("Kind regards,", styles["BodyText"]))
    flow.append(Paragraph("Ivan Bazhenov", styles["BodyText"]))
    flow.append(Paragraph("Kensington, VIC", styles["BodyText"]))
    flow.append(Paragraph("0466 284 180 | bazhenov.in@gmail.com", styles["BodyText"]))
    flow.append(Paragraph("LinkedIn: linkedin.com/in/sendhello | GitHub: github.com/sendhello", styles["BodyText"]))
    doc.build(flow)