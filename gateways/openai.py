import json
import logging

from openai import AsyncOpenAI, OpenAIError, PermissionDeniedError
from openai.types.shared.chat_model import ChatModel

from core.cache import read_cache, write_cache
from core.settings import settings
from gateways.prompts import format_resume_prompt, format_cover_letter_prompt
from schemas import Resume

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self, use_cache: bool = False):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            organization=settings.openai_organization_id,
            project=settings.openai_project_id,
        )
        self.use_cache = use_cache

    async def _chat_asc(self, prompt: str, text: str, model: ChatModel) -> str | None:
        if self.use_cache:
            cached = read_cache(prompt, text)
            if cached is not None:
                return cached

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
            )

            logger.debug(f"Response from OpenAI: {response}")
            if not response.choices:
                raise OpenAIError("Empty response from API.")

        except PermissionDeniedError as e:
            logger.error(f"Error in OpenAI chat completion: {e}")
            return None

        except Exception as e:
            logger.error(f"Error in OpenAI chat completion: {e}")
            return None

        result = response.choices[0].message.content
        write_cache(prompt, text, result)
        return result

    async def adaptating_resume(
            self,
            vacancy_text: str,
            addition_text: str,
            model: ChatModel = settings.openai_model,
            resume_type: str = settings.default_resume_type,
    ) -> Resume:
        print("Request resume adaptation")
        resume_path = settings.get_resume_path(resume_type)
        with open(resume_path, "r") as f:
            base_resume = Resume.model_validate_json(f.read())
            base_resume_text = "My basic resume data: " + base_resume.model_dump_json()

            additional_data = ''
            if addition_text.strip():
                additional_data = "Additional information for the resume: " + addition_text

            prompt = format_resume_prompt(settings) + base_resume_text + additional_data

        answer = await self._chat_asc(prompt=prompt, text=vacancy_text, model=model)
        new_resume = Resume.model_validate_json(answer)
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
            model: ChatModel = settings.openai_model,
            resume_type: str = settings.default_resume_type,
    ) -> str:
        print("Request cover_letter adaptation")
        resume_path = settings.get_resume_path(resume_type)
        with open(resume_path, "r") as f:
            base_resume = "My basic resume data: " + f.read()

            additional_data = ''
            if addition_text.strip():
                additional_data = "Additional information for the resume: " + addition_text

            prompt = format_cover_letter_prompt(settings) + base_resume + additional_data

        answer = await self._chat_asc(prompt=prompt, text=vacancy_text, model=model)
        return json.loads(answer)['cover_letter']


def get_ai_client(use_cache: bool = False) -> AIClient:
    return AIClient(use_cache=use_cache)
