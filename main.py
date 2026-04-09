import argparse
import asyncio
import os
import shutil

from core.settings import settings
from pdf import build_resume, build_cover_letter
from schemas import Resume


def parse_args():
    available_types = list(settings.resume_templates.keys())
    parser = argparse.ArgumentParser(description="Resume adapter")
    parser.add_argument(
        "--provider",
        choices=["openai", "claude"],
        default=settings.default_provider,
        help=f"AI provider to use (default: {settings.default_provider})",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name override (e.g. gpt-4o, claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--resume-type",
        choices=available_types,
        default=settings.default_resume_type,
        help=f"Resume type (default: {settings.default_resume_type}). Available: {', '.join(available_types)}",
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Use cached response from cache.json",
    )
    parser.add_argument(
        "--addition",
        default="addition.txt",
        help="Path to addition file (default: addition.txt)",
    )
    return parser.parse_args()


def create_ai_client(provider: str, use_cache: bool):
    if provider == "claude":
        from gateways.claude import get_claude_client
        return get_claude_client(use_cache=use_cache)
    else:
        from gateways.openai import get_ai_client
        return get_ai_client(use_cache=use_cache)


def load_text_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def prepare_output_dir(company_name: str) -> str:
    base_folder = company_name.replace(" ", "_").replace("/", "_").replace("-", "_").lower()
    folder_path = os.path.join(settings.output_dir, base_folder)
    counter = 2

    while os.path.exists(folder_path):
        folder_path = os.path.join(settings.output_dir, f"{base_folder}_{counter}")
        counter += 1

    os.makedirs(folder_path)
    return folder_path


def generate_pdfs(output_dir: str, resume: Resume, cover_letter: str):
    build_resume(
        path=os.path.join(output_dir, "resume.pdf"),
        title="Report",
        resume=resume,
    )
    build_cover_letter(
        path=os.path.join(output_dir, "cover_letter.pdf"),
        title="Cover letter",
        text=cover_letter,
        position=resume.title,
        company_name=resume.company_name,
    )


async def main():
    args = parse_args()

    ai_client = create_ai_client(args.provider, use_cache=args.cache)

    kwargs = {}
    if args.model:
        kwargs["model"] = args.model

    vacancy_text = load_text_file(settings.vacancy_file)
    addition_text = load_text_file(args.addition)

    resume, cover_letter = await asyncio.gather(
        ai_client.adaptating_resume(
            vacancy_text=vacancy_text,
            addition_text=addition_text,
            resume_type=args.resume_type,
            **kwargs,
        ),
        ai_client.adaptating_cover_letter(
            vacancy_text=vacancy_text,
            addition_text=addition_text,
            resume_type=args.resume_type,
            **kwargs,
        ),
        return_exceptions=True,
    )
    if isinstance(resume, Exception):
        raise resume
    if isinstance(cover_letter, Exception):
        raise cover_letter

    output_dir = prepare_output_dir(resume.company_name)
    generate_pdfs(output_dir, resume, cover_letter)
    shutil.copy(settings.vacancy_file, os.path.join(output_dir, "vacancy.txt"))

    print(f"Done! Output saved to: {output_dir}")


asyncio.run(main())
