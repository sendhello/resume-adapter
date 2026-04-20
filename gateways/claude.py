import logging
from typing import TypeVar

import anthropic
from anthropic import AsyncAnthropic
from pydantic import BaseModel

from core.cache import read_cache, write_cache
from core.settings import settings
from gateways.prompts import format_resume_prompt, format_cover_letter_prompt
from schemas import CoverLetter, Resume

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ClaudeAIClient:
    def __init__(self, use_cache: bool = False):
        self.client = AsyncAnthropic(
            api_key=settings.anthropic_api_key.get_secret_value(),
        )
        self.use_cache = use_cache

    async def _chat_asc(
        self,
        prompt: str,
        text: str,
        model: str,
        output_format: type[T],
    ) -> T | None:
        if self.use_cache:
            cached = read_cache(prompt, text)
            if cached is not None:
                return output_format.model_validate_json(cached)

        if not text or not text.strip():
            logger.error("Cannot send empty user message to Claude API")
            return None

        try:
            response = await self.client.messages.parse(
                model=model,
                max_tokens=16000,
                system=prompt,
                output_format=output_format,
                output_config={"effort": "high"},
                messages=[{"role": "user", "content": text}],
            )
            logger.debug(f"Response from Claude: {response}")
        except anthropic.PermissionDeniedError as e:
            logger.error(f"Claude permission denied: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in Claude chat completion: {e}")
            return None

        parsed: T | None = response.parsed_output
        if parsed is None:
            logger.error("Claude returned no parsed_output")
            return None

        write_cache(prompt, text, parsed.model_dump_json())
        return parsed

    async def adaptating_resume(
            self,
            vacancy_text: str,
            addition_text: str,
            model: str = None,
            resume_type: str = settings.default_resume_type,
    ) -> Resume:
        if model is None:
            model = settings.claude_model

        print("Request resume adaptation (Claude)")
        resume_path = settings.get_resume_path(resume_type)
        with open(resume_path, "r") as f:
            base_resume = Resume.model_validate_json(f.read())
            base_resume_text = "My basic resume data: " + base_resume.model_dump_json()

            additional_data = ""
            if addition_text.strip():
                additional_data = "Additional information for the resume: " + addition_text

            prompt = format_resume_prompt(settings) + base_resume_text + additional_data

        new_resume = await self._chat_asc(
            prompt=prompt,
            text=vacancy_text,
            model=model,
            output_format=Resume,
        )
        resume = base_resume.model_copy()
        resume.company_name = new_resume.company_name
        resume.title = new_resume.title
        resume.professional_summary = new_resume.professional_summary
        resume.key_skills = new_resume.key_skills
        resume.work_experience = new_resume.work_experience
        if new_resume.personal_projects:
            resume.personal_projects = new_resume.personal_projects
        return resume

    async def adaptating_cover_letter(
            self,
            vacancy_text: str,
            addition_text: str,
            model: str = None,
            resume_type: str = settings.default_resume_type,
    ) -> str:
        if model is None:
            model = settings.claude_model

        print("Request cover_letter adaptation (Claude)")
        resume_path = settings.get_resume_path(resume_type)
        with open(resume_path, "r") as f:
            base_resume = "My basic resume data: " + f.read()

            additional_data = ""
            if addition_text.strip():
                additional_data = "Additional information for the resume: " + addition_text

            prompt = format_cover_letter_prompt(settings) + base_resume + additional_data

        parsed = await self._chat_asc(
            prompt=prompt,
            text=vacancy_text,
            model=model,
            output_format=CoverLetter,
        )
        return parsed.cover_letter


def get_claude_client(use_cache: bool = False) -> ClaudeAIClient:
    return ClaudeAIClient(use_cache=use_cache)
