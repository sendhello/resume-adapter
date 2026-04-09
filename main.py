import argparse
import asyncio
import os
import shutil

from core.settings import settings
from pdf import build_resume, build_cover_letter


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


async def main():
    args = parse_args()

    if args.provider == "claude":
        from gateways.claude import get_claude_client
        ai_client = get_claude_client(use_cache=args.cache)
    else:
        from gateways.openai import get_ai_client
        ai_client = get_ai_client(use_cache=args.cache)

    kwargs = {}
    if args.model:
        kwargs["model"] = args.model

    with open(settings.vacancy_file, "r") as f:
        vacancy_text = f.read()

    with open(args.addition, "r") as f:
        addition_text = f.read()

    resume_coro = ai_client.adaptating_resume(
        vacancy_text=vacancy_text,
        addition_text=addition_text,
        resume_type=args.resume_type,
        **kwargs,
    )
    cover_letter_coro = ai_client.adaptating_cover_letter(
        vacancy_text=vacancy_text,
        addition_text=addition_text,
        resume_type=args.resume_type,
        **kwargs,
    )
    resume, cover_letter = await asyncio.gather(resume_coro, cover_letter_coro, return_exceptions=True)
    if isinstance(resume, Exception):
        raise resume
    if isinstance(cover_letter, Exception):
        raise cover_letter

    base_path = settings.output_dir
    base_folder_name = resume.company_name.replace(" ", "_").replace("/", "_").replace("-", "_").lower()
    folder_name = os.path.join(base_path, base_folder_name)
    counter = 2

    while os.path.exists(folder_name):
        folder_name = os.path.join(base_path, f"{base_folder_name}_{counter}")
        counter += 1

    os.makedirs(folder_name)

    build_resume(
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

    shutil.copy(settings.vacancy_file, os.path.join(folder_name, "vacancy.txt"))


asyncio.run(main())
