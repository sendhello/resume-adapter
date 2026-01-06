from gateways.openai import get_ai_client, AIClient
from pdf import build_resume, build_cover_letter
import asyncio
from schemas import Resume, ResumeType



async def main():
    ai_client: AIClient = get_ai_client(use_cache=False)

    with open("vacancy.txt", "r") as f:
        vacancy_text = f.read()
        resume, cover_letter = await ai_client.adaptating_resume(vacancy_text, resume_type=ResumeType.SoftwareEngineer)

    build_resume(
        path="resume.pdf",
        title="Report",
        resume=resume,
    )

    build_cover_letter(
        path="cover_letter.pdf",
        title="Cover letter",
        text=cover_letter,
        position=resume.title,
        company_name=resume.company_name,
    )


asyncio.run(main())