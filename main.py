from gateways.openai import get_ai_client, AIClient
from pdf import build_new_resume, build_cover_letter
import asyncio
from schemas import Resume, ResumeType
import os
import shutil


async def main():
    ai_client: AIClient = get_ai_client(use_cache=False)

    with open("vacancy.txt", "r") as f:
        vacanсy_text = f.read()

    with open("addition.txt", "r") as f:
        addition_text = f.read()

    resume = await ai_client.adaptating_resume(
        vacanсy_text=vacanсy_text,
        addition_text=addition_text,
        resume_type=ResumeType.SoftwareEngineer
    )
    cover_letter = await ai_client.adaptating_cover_letter(
        vacanсy_text=vacanсy_text,
        addition_text=addition_text,
        resume_type=ResumeType.SoftwareEngineer
    )

    base_path = '/Users/ivanbazhenov/Library/Mobile Documents/com~apple~CloudDocs/Documents/Look a Job'
    base_folder_name = resume.company_name.replace(" ", "_").replace("/", "_").replace("-", "_").lower()
    folder_name = os.path.join(base_path, base_folder_name)
    counter = 2

    # Проверка существования папки и добавление суффикса при необходимости
    while os.path.exists(folder_name):
        folder_name = os.path.join(base_path, f"{base_folder_name}_{counter}")
        counter += 1

    # Создание новой папки
    os.makedirs(folder_name)


    build_new_resume(
        path=os.path.join(folder_name, "resume.pdf"),
        title="Report",
        resume=resume,
    )

    build_cover_letter(
        path=os.path.join(folder_name, "cover_letter.pdf"),
        title="Cover letter",
        text=cover_letter,
        position=resume.title,
        company_name=resume.company_name,
    )

    shutil.copy("vacancy.txt", os.path.join(folder_name, "vacancy.txt"))


asyncio.run(main())