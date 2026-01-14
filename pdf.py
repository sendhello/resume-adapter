from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable, ListFlowable, ListItem, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm, cm, inch
from schemas import Resume
from reportlab.pdfbase.pdfmetrics import registerFont, registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY


registerFont(TTFont("CenturyGothic", "fonts/centurygothic.ttf"))
registerFont(TTFont("CenturyGothic-Bold", "fonts/centurygothic_bold.ttf"))

registerFontFamily(
    "Century Gothic",
    normal="CenturyGothic",
    bold="CenturyGothic-Bold",
    italic="CenturyGothic",
    boldItalic="CenturyGothic-Bold",
)


class SplitParagraph(Flowable):
    """Flowable для размещения двух параграфов на одной строке"""

    def __init__(self, left_text, right_text, left_style, right_style, width=None, left_part=0.7, right_part=0.3):
        Flowable.__init__(self)
        self.left_para = Paragraph(left_text, left_style)
        self.right_para = Paragraph(right_text, right_style)
        self.left_part = left_part
        self.right_part = right_part
        self._width = width

    def wrap(self, availWidth, availHeight):
        self.width = self._width or availWidth
        # Получаем высоту обоих параграфов
        left_w, left_h = self.left_para.wrap(self.width * self.left_part, availHeight)
        right_w, right_h = self.right_para.wrap(self.width * self.right_part, availHeight)
        self.height = max(left_h, right_h)
        return (self.width, self.height)

    def draw(self):
        # Рисуем левый параграф
        self.left_para.drawOn(self.canv, 0, 0)
        # Рисуем правый параграф справа
        right_w, right_h = self.right_para.wrap(self.width * 0.3, self.height)
        self.right_para.drawOn(self.canv, self.width - right_w, 0)


class IndentedListFlowable(ListFlowable):
    """ListFlowable с отступом слева"""

    def __init__(self, items, left_margin=20, **kwargs):
        ListFlowable.__init__(self, items, **kwargs)
        self.left_margin = left_margin

    def wrap(self, availWidth, availHeight):
        # Уменьшаем доступную ширину на величину отступа
        return ListFlowable.wrap(self, availWidth - self.left_margin, availHeight)

    def drawOn(self, canvas, x, y, _sW=0):
        # Сдвигаем рисование вправо
        return ListFlowable.drawOn(self, canvas, x + self.left_margin, y, _sW)


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
    stylesheet = getSampleStyleSheet()
    stylesheet.add(ParagraphStyle(
        name='Body',
        parent=stylesheet["BodyText"],
        fontName="Times-Roman",
    ))
    stylesheet.add(ParagraphStyle(
        name='BodyList',
        parent=stylesheet["Body"],
        spaceAfter=0,
        spaceBefore=0,

    ))
    stylesheet.add(ParagraphStyle(
        name='BodySkils',
        parent=stylesheet["Body"],
        spaceAfter=2,
        spaceBefore=0,

    ))
    stylesheet.add(ParagraphStyle(
        name='SubtitleLeft',
        parent=stylesheet["Body"],
        fontSize=12.5,
        leading=17,
    ))
    stylesheet.add(ParagraphStyle(
        name='SubtitleLeftBold',
        parent=stylesheet["SubtitleLeft"],
        fontName="Times-Bold",
    ))
    stylesheet.add(ParagraphStyle(
        name='SubtitleRight',
        parent=stylesheet["SubtitleLeft"],
        alignment=TA_RIGHT,
    ))
    stylesheet.add(ParagraphStyle(
        name='SubtitleCenter',
        parent=stylesheet["SubtitleLeft"],
        alignment=TA_CENTER,
    ))
    stylesheet.add(ParagraphStyle(
        name='H1',
        parent=stylesheet["Title"],
        fontName="Times-Bold",
        fontSize=20,
        spaceAfter=6,
    ))
    stylesheet.add(ParagraphStyle(
        name='H3',
        parent=stylesheet["Heading3"],
        fontName="Times-Bold",
        fontSize=12.5,
        spaceAfter=1,
        spaceBefore=10,
    ))
    return stylesheet


def build_resume(path: str, title: str, resume: Resume):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=0.42*inch, rightMargin=0.42*inch,
        topMargin=0.5*inch, bottomMargin=0.35*inch,
        title=title, author=resume.name
    )
    styles = create_simple_styles()

    flow = []

    flow.append(Paragraph(resume.name, styles["H1"]))
    flow.append(Paragraph(f"{resume.address} | {resume.phone} | {resume.email} | {resume.linkedin}", styles["SubtitleCenter"]))

    flow.append(Paragraph("EDUCATION", styles["H3"]))
    flow.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceBefore=0, spaceAfter=6))
    for edu in resume.education:
        flow.append(SplitParagraph(
            edu.institution.upper(),
            edu.location,
            styles["SubtitleLeftBold"],
            styles["SubtitleRight"]
        ))
        flow.append(SplitParagraph(
            edu.qualification,
            f"<i>{edu.dates}</i>",
            styles["SubtitleLeft"],
            styles["SubtitleRight"]
        ))

    flow.append(Paragraph("WORK EXPERIENCE", styles["H3"]))
    flow.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceBefore=0, spaceAfter=6))
    for workplace in resume.work_experience:
        flow.append(SplitParagraph(
            workplace.company,
            workplace.location,
            styles["SubtitleLeftBold"],
            styles["SubtitleRight"]
        ))
        flow.append(SplitParagraph(
            f"<i>{workplace.position}</i>",
            f"<i>{workplace.dates}</i>",
            styles["SubtitleLeft"],
            styles["SubtitleRight"]
        ))
        flow.append(
            IndentedListFlowable(
                [ListItem(Paragraph(achiev, styles["BodyList"]), bulletIndent=30) for achiev in workplace.achievements],
                left_margin=20,
                bulletType="bullet",
                spaceAfter=15,
                spaceBefore=0,
                bulletFontSize=16,
                bulletOffsetY=3,
            )
        )

    flow.append(Paragraph("KEY SKILLS", styles["H3"]))
    flow.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceBefore=0, spaceAfter=6))
    for group, skills in resume.key_skills.items():
        if len(skills) > 1:
            flow.append(Paragraph(f"<b>{group}:</b> {', '.join(skills[:-1])} and {skills[-1]}", styles["BodySkils"]))
        else:
            flow.append(Paragraph(f"<b>{group}:</b> {', '.join(skills)}", styles["BodySkils"]))

    flow.append(Paragraph("PROFESSIONAL  SUMMARY", styles["H3"]))
    flow.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceBefore=0, spaceAfter=6))
    flow.append(Paragraph(resume.professional_summary, styles["Body"]))
    flow.append(Paragraph(f"<b>GitHub</b>: {resume.github}", styles["Body"]))

    doc.build(flow)


def build_cover_letter(path: str, title: str, text: str, position: str, company_name: str, author: str = "Ivan Bazhenov"):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=0.42 * inch, rightMargin=0.42 * inch,
        topMargin=0.5 * inch, bottomMargin=0.35 * inch,
        title=title, author=author
    )
    styles = create_simple_styles()

    flow = []

    flow.append(Paragraph(f"{position} - {company_name}", styles["H3"]))
    flow.extend([Paragraph(article, styles["Body"]) for article in text.split("\n")])
    flow.append(Paragraph("", styles["Body"]))
    if not "regards" in text:
        flow.append(Paragraph("Kind regards,", styles["Body"]))
        flow.append(Paragraph("Ivan Bazhenov", styles["Body"]))
        flow.append(Paragraph("Melbourne, VIC", styles["Body"]))
        flow.append(Paragraph("0466 284 180 | bazhenov.in@gmail.com", styles["Body"]))
        flow.append(Paragraph("LinkedIn: linkedin.com/in/sendhello", styles["Body"]))
        flow.append(Paragraph("GitHub: github.com/sendhello", styles["Body"]))

    doc.build(flow)