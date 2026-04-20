#!/usr/bin/env python3
"""Standalone PDF generator for resume and cover letter.

Usage:
    python generate_pdf.py \
        --resume-json adapted_resume.json \
        --cover-letter-text cover_letter.txt \
        --output-dir /path/to/output \
        --config-yaml config.yaml
"""

import argparse
import os
import sys
from pathlib import Path

import yaml
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.pdfmetrics import registerFont, registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Flowable,
    ListFlowable,
    ListItem,
    HRFlowable,
)


# --- Models (from schemas.py) ---

class Education(BaseModel):
    institution: str
    location: str
    dates: str
    qualification: str


class Experience(BaseModel):
    position: str
    company: str
    location: str
    dates: str
    achievements: list[str]


class PersonalProject(BaseModel):
    name: str
    url: str = ""
    description: str


class Resume(BaseModel):
    company_name: str
    name: str
    title: str
    phone: str
    email: str
    linkedin: str = ""
    github: str = ""
    address: str
    professional_summary: str
    key_skills: dict[str, list[str]]
    work_experience: list[Experience]
    education: list[Education]
    personal_projects: list[PersonalProject] = []
    other_educations: list[Education] = []
    languages: list[str] = []
    hobbies: list[str] = []
    work_rights: str = ""


# --- Font registration ---

FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"

registerFont(TTFont("CenturyGothic", str(FONTS_DIR / "centurygothic.ttf")))
registerFont(TTFont("CenturyGothic-Bold", str(FONTS_DIR / "centurygothic_bold.ttf")))
registerFontFamily(
    "Century Gothic",
    normal="CenturyGothic",
    bold="CenturyGothic-Bold",
    italic="CenturyGothic",
    boldItalic="CenturyGothic-Bold",
)


# --- Custom flowables ---

class SplitParagraph(Flowable):
    """Two paragraphs side by side on one line."""

    def __init__(self, left_text, right_text, left_style, right_style, width=None, left_part=0.7, right_part=0.3):
        Flowable.__init__(self)
        self.left_para = Paragraph(left_text, left_style)
        self.right_para = Paragraph(right_text, right_style)
        self.left_part = left_part
        self.right_part = right_part
        self._width = width

    def wrap(self, availWidth, availHeight):
        self.width = self._width or availWidth
        left_w, left_h = self.left_para.wrap(self.width * self.left_part, availHeight)
        right_w, right_h = self.right_para.wrap(self.width * self.right_part, availHeight)
        self.height = max(left_h, right_h)
        return (self.width, self.height)

    def draw(self):
        self.left_para.drawOn(self.canv, 0, 0)
        right_w, right_h = self.right_para.wrap(self.width * 0.3, self.height)
        self.right_para.drawOn(self.canv, self.width - right_w, 0)


class IndentedListFlowable(ListFlowable):
    """ListFlowable with left margin indent."""

    def __init__(self, items, left_margin=20, **kwargs):
        ListFlowable.__init__(self, items, **kwargs)
        self.left_margin = left_margin

    def wrap(self, availWidth, availHeight):
        return ListFlowable.wrap(self, availWidth - self.left_margin, availHeight)

    def drawOn(self, canvas, x, y, _sW=0):
        return ListFlowable.drawOn(self, canvas, x + self.left_margin, y, _sW)


# --- Styles ---

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


# --- PDF builders ---

def build_resume(path: str, resume: Resume):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=0.42 * inch, rightMargin=0.42 * inch,
        topMargin=0.5 * inch, bottomMargin=0.35 * inch,
        title="Report", author=resume.name,
    )
    styles = create_simple_styles()
    flow = []

    flow.append(Paragraph(resume.name, styles["H1"]))
    contact_parts = [resume.address, resume.phone, resume.email]
    if resume.linkedin:
        contact_parts.append(resume.linkedin)
    flow.append(Paragraph(" | ".join(contact_parts), styles["SubtitleCenter"]))

    flow.append(Paragraph("EDUCATION", styles["H3"]))
    flow.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceBefore=0, spaceAfter=6))
    for edu in resume.education:
        flow.append(SplitParagraph(
            edu.institution.upper(), edu.location,
            styles["SubtitleLeftBold"], styles["SubtitleRight"],
        ))
        flow.append(SplitParagraph(
            edu.qualification, f"<i>{edu.dates}</i>",
            styles["SubtitleLeft"], styles["SubtitleRight"],
        ))

    flow.append(Paragraph("WORK EXPERIENCE", styles["H3"]))
    flow.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceBefore=0, spaceAfter=6))
    for workplace in resume.work_experience:
        flow.append(SplitParagraph(
            workplace.company, workplace.location,
            styles["SubtitleLeftBold"], styles["SubtitleRight"],
        ))
        flow.append(SplitParagraph(
            f"<i>{workplace.position}</i>", f"<i>{workplace.dates}</i>",
            styles["SubtitleLeft"], styles["SubtitleRight"],
        ))
        flow.append(IndentedListFlowable(
            [ListItem(Paragraph(achiev, styles["BodyList"]), bulletIndent=30) for achiev in workplace.achievements],
            left_margin=20,
            bulletType="bullet",
            spaceAfter=15,
            spaceBefore=0,
            bulletFontSize=16,
            bulletOffsetY=3,
        ))

    flow.append(Paragraph("KEY SKILLS", styles["H3"]))
    flow.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceBefore=0, spaceAfter=6))
    for group, skills in resume.key_skills.items():
        if len(skills) > 1:
            flow.append(Paragraph(f"<b>{group}:</b> {', '.join(skills[:-1])} and {skills[-1]}", styles["BodySkils"]))
        else:
            flow.append(Paragraph(f"<b>{group}:</b> {', '.join(skills)}", styles["BodySkils"]))

    if resume.personal_projects:
        flow.append(Paragraph("PERSONAL PROJECTS", styles["H3"]))
        flow.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceBefore=0, spaceAfter=6))
        for project in resume.personal_projects:
            if project.url:
                flow.append(Paragraph(f"<b>{project.name}</b> — {project.url}", styles["BodySkils"]))
            else:
                flow.append(Paragraph(f"<b>{project.name}</b>", styles["BodySkils"]))
            flow.append(Paragraph(project.description, styles["BodyList"]))
            flow.append(Paragraph("", styles["BodyList"]))

    flow.append(Paragraph("PROFESSIONAL  SUMMARY", styles["H3"]))
    flow.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceBefore=0, spaceAfter=6))
    flow.append(Paragraph(resume.professional_summary, styles["Body"]))
    if resume.github:
        flow.append(Paragraph(f"<b>GitHub</b>: {resume.github}", styles["Body"]))

    doc.build(flow)


def build_cover_letter(path: str, text: str, position: str, company_name: str, config: dict):
    personal = config.get("personal", {})
    author = personal.get("name", "")

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=0.42 * inch, rightMargin=0.42 * inch,
        topMargin=0.5 * inch, bottomMargin=0.35 * inch,
        title="Cover letter", author=author,
    )
    styles = create_simple_styles()
    flow = []

    flow.append(Paragraph(f"{position} - {company_name}", styles["H3"]))
    flow.extend([Paragraph(article, styles["Body"]) for article in text.split("\n")])
    flow.append(Paragraph("", styles["Body"]))

    if "regards" not in text.lower():
        flow.append(Paragraph("Kind regards,", styles["Body"]))
        flow.append(Paragraph(personal.get("name", ""), styles["Body"]))
        flow.append(Paragraph(personal.get("location", ""), styles["Body"]))
        phone = personal.get("phone", "")
        email = personal.get("email", "")
        if phone or email:
            flow.append(Paragraph(f"{phone} | {email}", styles["Body"]))
        linkedin = personal.get("linkedin", "")
        if linkedin:
            flow.append(Paragraph(f"LinkedIn: {linkedin}", styles["Body"]))
        github = personal.get("github", "")
        if github:
            flow.append(Paragraph(f"GitHub: {github}", styles["Body"]))

    doc.build(flow)


# --- CLI ---

def parse_args():
    parser = argparse.ArgumentParser(description="Generate resume and cover letter PDFs")
    parser.add_argument("--resume-json", required=True, help="Path to adapted resume JSON file")
    parser.add_argument("--cover-letter-text", required=True, help="Path to cover letter text file")
    parser.add_argument("--output-dir", required=True, help="Output directory for PDFs")
    parser.add_argument("--config-yaml", required=True, help="Path to config.yaml")
    return parser.parse_args()


def main():
    args = parse_args()

    with open(args.config_yaml, "r") as f:
        config = yaml.safe_load(f)

    with open(args.resume_json, "r") as f:
        resume = Resume.model_validate_json(f.read())

    with open(args.cover_letter_text, "r") as f:
        cover_text = f.read()

    os.makedirs(args.output_dir, exist_ok=True)

    resume_path = os.path.join(args.output_dir, "resume.pdf")
    build_resume(path=resume_path, resume=resume)
    print(f"Resume PDF: {resume_path}")

    cover_path = os.path.join(args.output_dir, "cover_letter.pdf")
    build_cover_letter(
        path=cover_path,
        text=cover_text,
        position=resume.title,
        company_name=resume.company_name,
        config=config,
    )
    print(f"Cover letter PDF: {cover_path}")


if __name__ == "__main__":
    main()
